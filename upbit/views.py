from io import IOBase
from django.http.response import HttpResponseRedirect
from django.utils import timezone
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import UpbitConfig, Market

import jwt
import uuid
import hashlib
from urllib.parse import urlencode
import requests
import json
import datetime
import time

def make_payload(request, url, query={}, method="GET"):
    config = UpbitConfig.objects.get(user=request.user)
    payload = {
        'access_key': config.access_key,
        'nonce': str(uuid.uuid4())
    }

    query_string = ""
    if query:
        query_string = urlencode(query).encode()

        m = hashlib.sha512()
        m.update(query_string)
        query_hash = m.hexdigest()
        payload['query_hash'] = query_hash
        payload['query_hash_alg'] = 'SHA512'

    jwt_token = jwt.encode(payload, config.secret_key)
    authorize_token = 'Bearer {}'.format(jwt_token)
    headers = {"Authorization": authorize_token}

    if method == "GET":
        return requests.get('https://api.upbit.com{}'.format(url), params=query_string, headers=headers)
    else:
        print("post call")
        return requests.post('https://api.upbit.com{}'.format(url), params=query, headers=headers)

def get_currency_list(request, currency='KRW'):
    res = make_payload(request, '/v1/deposits', {'currency':currency})
    return res.json()

# Create your views here.
@login_required
def index(request):
    accounts_res = make_payload(request, '/v1/accounts')
    json_data = accounts_res.json()

    market_codes = requests.request("GET", "https://api.upbit.com/v1/market/all")
    market_names = {}
    for m in market_codes.json():
        if m['market'].startswith("KRW-"):
            market_names[m['market']] = m
            # market_names[m['market'][4:]] = m
            
    krw_data = {}
    krw_price_data = []
    total_order_balance = 0.0
    account_names = []
    for r in json_data:
        if 'KRW-'+r['currency'] in market_names:
            r['korean_name'] = market_names['KRW-'+r['currency']]['korean_name']
            account_names.append(market_names['KRW-'+r['currency']])
            del(market_names['KRW-'+r['currency']])
        else:
            print('KRW-'+r['currency'])

        if float(r['avg_buy_price']) == 0:
            r['krw_price'] = int(float(r['balance']))
        else:
            r['krw_price'] = int(float(r['avg_buy_price']) * float(r['balance']))
            total_order_balance = total_order_balance + float(r['krw_price'])
        r['krw_real_price'] = 0

        if r['currency'] == 'KRW':
            krw_data = r
            continue
        if r['currency'] == 'VTHO':
            continue

        krw_price_data.append(r)

    krw_data['total_order_balance'] = int(total_order_balance)

    for key, value in market_names.items():
        krw_price_data.append({'korean_name':value['korean_name'], 'krw_price':0, 'krw_real_price':0, 'currency':key[4:], 'market':key})
    
    # 입금액 정산
    total_deposit_krw = 0.0
    for deposit in get_currency_list(request):
        if float(deposit['amount']) > 10000 and deposit['state'] == 'ACCEPTED':
            total_deposit_krw = total_deposit_krw + float(deposit['amount'])
        else:
            print(deposit)
    krw_data['total_deposit_balance'] = int(total_deposit_krw)

    markets = []
    for a in account_names+list(market_names.values()):
        markets.append(a['market'])

    # ticker_prices = []
    # while len(markets) > 0:
    #     target_markets = markets[0:10]
    #     markets = markets[10:]

    #     query = {'markets':",".join(target_markets)}
    #     print(query)

    #     target_ticker_prices = make_payload(request, '/v1/ticker', query).json()
    #     ticker_prices = ticker_prices + target_ticker_prices

    query = {'markets':",".join(markets)}

    ticker_prices = make_payload(request, '/v1/ticker', query).json()

    for t, k in zip(ticker_prices, krw_price_data):
        if t['market'] == 'KRW-'+k['currency']:
            k['signed_change_price'] = t['signed_change_price']
            k['signed_change_rate'] = t['signed_change_rate']
            k['trade_volume'] = t['trade_volume']
            k['trade_price'] = t['trade_price']
            k['acc_trade_price_24h'] = t['acc_trade_price_24h']
            if 'avg_buy_price' in k:
                k['mine_change_price'] = round((float(t['trade_price']) - float(k['avg_buy_price'])) * float(k['balance']), 2)
                k['mine_change_rate'] = float((float(t['trade_price']) - float(k['avg_buy_price'])) / float(k['avg_buy_price']))
                k['mine_change_percent'] = round(float(k['mine_change_rate']) * 100, 2)
                k['krw_real_price'] = int(float(t['trade_price']) * float(k['balance']))

                if t['market'] == 'KRW-BTC':
                    k['block_count'] = int(float(k['krw_price']) / 11000)# block value
                else:
                    k['block_count'] = int(round(float(k['krw_price']) / 5500, 0))# block value
            else:
                k['mine_change_price'] = float(t['trade_price']) - float(t['highest_52_week_price'])
                k['mine_change_rate'] = float(k['mine_change_price']) / float(t['highest_52_week_price'])
                k['mine_change_percent'] = round(float(k['mine_change_rate']) * 100, 2)
            
            # print("{} {}  {} * {} = {}".format(t['market'], 'KRW-'+k['currency'], ))
        else:
            print("{} != {}".format(t['market'], 'KRW-'+k['currency']))

    json_data = sorted(krw_price_data, key=lambda x:float(x['krw_real_price']), reverse=True)

    zero_data_index = 0
    for i, d in zip(range(len(json_data)), json_data):
        if 'avg_buy_price' not in d:
            zero_data_index = i
            break

    json_data = json_data[0:zero_data_index] + sorted(json_data[zero_data_index:], key=lambda x:float(x['acc_trade_price_24h']), reverse=True)
    
    return render(request, 'upbit/index.html', {'krw_data':krw_data, 'res':json_data, 'market_codes':market_names})

not_market_list = ["KRW", "VTHO"]
buy_rate = 0
sell_rate = 7

def dryrun(request):
    accounts_res = make_payload(request, '/v1/accounts')
    coins = []
    for a in accounts_res.json():
        if a['currency'] not in not_market_list:
            coins.append(Coin(a))
        elif a['currency'] == "KRW":
            krw = a
            krw['int_balance'] = int(float(krw['balance']))
    query={'markets':",".join(list(map(lambda x:x.get_market(), coins)))}
    ticker_prices = make_payload(request, '/v1/ticker', query)

    buy_list = []
    sell_list = []

    buy_sum = 0.0
    sell_change_sum = 0.0
    sell_sum = 0.0

    for t, c in zip(ticker_prices.json(), coins):
        c.input_ticker_price(t)

        try:
            market = Market.objects.get(user=request.user, market=c.get_market())
        except Market.DoesNotExist:
            market = Market.objects.create(user=request.user, market=c.get_market(), last_order=timezone.now() - datetime.timedelta(days=7))

        if market.last_order + datetime.timedelta(hours=6) > timezone.now():
            continue

        if buy_rate > c.get_change_rate():
            # print("{} {}% 구매".format(c.get_market(), c.get_change_rate()))
            buy_list.append(c)
            buy_sum = buy_sum + c.get_block_size()
        elif sell_rate < c.get_change_rate() and c.get_block_count() > 0:
            # print("{} {}% 판매".format(c.get_market(), c.get_change_rate()))
            sell_list.append(c)
            sell_sum = sell_sum + c.get_block_price()
            sell_change_sum = sell_change_sum + c.get_sell_change_price()

    krw['int_require'] = round(int(buy_sum) - int(krw['int_balance']), -3) + 1000
    sell_change_rate = 0
    if sell_sum > 0:
        sell_change_rate = round(float(sell_change_sum / sell_sum * 100), 2)

    return render(request, 'upbit/dryrun.html', {'buy_list':buy_list, 'sell_list':sell_list, 'buy_sum':int(buy_sum), 'sell_change_sum':int(sell_change_sum), 'sell_sum':int(sell_sum), 'krw':krw, 'sell_change_rate':sell_change_rate})

class Coin:
    market = ""
    currency = ""
    balance = 0.0
    avg_buy_price = 0.0
    blocksize = 5500
    blockcount = 0

    trade_price = 0.0
    signed_change_price = 0.0
    signed_change_rate = 0.0
    acc_trade_price_24h = 0.0

    bigblock = ["BTC"]

    def __init__(self, account):
        self.currency = account['currency']
        if self.currency in self.bigblock:
            self.blocksize = 11000
        self.market = "KRW-" + account['currency']
        self.balance = float(account['balance'])
        self.avg_buy_price = float(account['avg_buy_price'])
        self.blockcount = int(self.avg_buy_price * self.balance / self.blocksize)

    def get_market(self):
        return self.market

    def get_currency(self):
        return self.currency

    def input_ticker_price(self, ticker):
        if self.market != ticker['market']:
            print("{} != {}".format(self.market, ticker['market']))
        self.trade_price = ticker['trade_price']
        self.signed_change_price = ticker['signed_change_price']
        self.signed_change_rate = ticker['signed_change_rate']
        self.acc_trade_price_24h = ticker['acc_trade_price_24h']
        self.highest_52_week_price = ticker['highest_52_week_price']

    def get_change_rate(self):
        return round((self.trade_price - self.avg_buy_price) / self.avg_buy_price * 100, 2)

    def get_sell_balance(self):
        return self.balance / self.blockcount

    def get_sell_change_price(self):
        return int(self.get_sell_balance() * (self.trade_price - self.avg_buy_price))

    def get_block_count(self):
        return self.blockcount

    def get_block_price(self):
        return int(self.get_sell_balance() * self.trade_price)

    def get_block_size(self):
        return self.blocksize


def sell_block(request):
    if request.method == "POST":
        query = {
            'market': request.POST['market'],
            'side': request.POST['side'],
            'ord_type': request.POST['ord_type'],
        }
        if 'volume' in request.POST:
            query['volume'] = request.POST['volume']
        if 'price' in request.POST:
            query['price'] = request.POST['price']

        res = make_payload(request, '/v1/orders', query, method="POST")
        res_json = res.json()
        print(res_json)

        if 'error' in res_json and res_json['error']['name'] == 'insufficient_funds_bid':
            query = {'amount': request.POST['price']}
            res = make_payload(request, '/v1/deposits/krw', query, method="POST")
            res_json = res.json()

        if 'error' not in res_json:
            try:
                market = Market.objects.get(user=request.user, market=request.POST['market'])
                market.last_order = timezone.now()
                market.save()
            except Market.DoesNotExist:
                market = Market.objects.create(user=request.user, market=request.POST['market'], last_order=timezone.now())

    return HttpResponseRedirect(request.META['HTTP_REFERER'])

def deposit_krw(request):
    if request.method == "POST":
        query = {
            'amount': request.POST['amount']
        }

        res = make_payload(request, '/v1/deposits/krw', query, method="POST")
        res_json = res.json()
        print(res_json)

    return HttpResponseRedirect(request.META['HTTP_REFERER'])
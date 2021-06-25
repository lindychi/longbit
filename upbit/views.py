from io import IOBase
from os import curdir
from django.http.response import HttpResponse, HttpResponseRedirect
from django.utils import timezone
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Market, Order, CoinMarket
from .model.UpbitConfig import UpbitConfig
from .api.upbit import make_payload

import jwt
import uuid
import hashlib
from urllib.parse import urlencode
import requests
import json
import datetime
import time
import math

def get_currency_list(request, currency='KRW'):
    total_res = []
    page = 1
    while True:
        res = make_payload(request.user, '/v1/deposits', {'currency':currency, 'page':page})
        total_res.extend(res.json())
        if len(res.json()) < 100:
            break
        page = page + 1
    return total_res

def get_order_list(request):
    total_res = []
    page = 1
    while True:
        res = make_payload(request.user, '/v1/orders', {'state':'done', 'page':page})
        total_res.extend(res.json())
        if len(res.json()) < 100:
            break
        page = page + 1
    total_res = sorted(total_res, key=lambda x:x['created_at'], reverse=True)
    return total_res

# Create your views here.
@login_required
def index(request):
    accounts_res = make_payload(request.user, '/v1/accounts')
    account_json_data = accounts_res.json()

    market_codes = make_payload(request.user, "/v1/market/all", query={"isDetails":"true"})
    market_names = {}
    coins = []
    for m in market_codes.json():
        if m['market'].startswith("KRW-"):
            market_names[m['market']] = m
            coins.append(Coin(market=m))
        else:
            pass # 이후에 coinsㅇㅔ ㅊㅜㄱㅏㅎㅏㄹ ㅅㅜ ㅇㅣㅆㄸㅏ
            
    krw_data = {}
    krw_price_data = []
    total_order_balance = 0.0
    account_names = []
    for r in account_json_data:
        if 'KRW-'+r['currency'] in market_names:
            r['korean_name'] = market_names['KRW-'+r['currency']]['korean_name']
            r['market'] = market_names['KRW-'+r['currency']]['market']
            account_names.append(market_names['KRW-'+r['currency']])
            del(market_names['KRW-'+r['currency']])
        else:
            print('마켓에서 제외({})'.format('KRW-'+r['currency']))

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
        if deposit['state'] == 'ACCEPTED':
            total_deposit_krw = total_deposit_krw + float(deposit['amount'])
        elif deposit['state'] == 'REJECTED':
            continue
        else:
            print(deposit)
    krw_data['total_deposit_balance'] = int(total_deposit_krw)
    krw_data['total_order_gap'] = int(krw_data['total_order_balance']) - int(krw_data['total_deposit_balance']) + int(krw_data['krw_price'])
    krw_data['total_order_gap_rate'] = round(float(int(krw_data['total_order_gap']) / int(krw_data['total_deposit_balance']) * 100), 2)

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

    ticker_prices = make_payload(request.user, '/v1/ticker', query).json()

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
                if int(k['block_count']) == 0 and float(k['balance']) > 0:
                    k['sell_balance'] = float(k['balance'])
                elif int(k['block_count']) > 0:
                    k['sell_balance'] = float(k['balance']) / k['block_count']
            else:
                k['mine_change_price'] = float(t['trade_price']) - float(t['highest_52_week_price'])
                k['mine_change_rate'] = float(k['mine_change_price']) / float(t['highest_52_week_price'])
                k['mine_change_percent'] = round(float(k['mine_change_rate']) * 100, 2)
            
            # print("{} {}  {} * {} = {}".format(t['market'], 'KRW-'+k['currency'], ))
        else:
            print("{} != {}".format(t['market'], 'KRW-'+k['currency']))

    account_json_data = sorted(krw_price_data, key=lambda x:float(x['krw_real_price']), reverse=True)

    zero_data_index = 0
    for d in account_json_data:
        if 'avg_buy_price' in d and float(d['avg_buy_price']) > 0:
            print("{} {}".format(zero_data_index, d['avg_buy_price']))
        else:
            break
        zero_data_index = zero_data_index + 1

    print('zero data index: {}'.format(zero_data_index))
    # print(account_json_data[zero_data_index:])
    for j in account_json_data[zero_data_index:]:
        try:
            market = Market.objects.get(user=request.user, market=j['market'])
            j['avg_buy_price'] = market.get_avg_buy_price()
            if j['avg_buy_price'] > 0:
                j['mine_change_price'] = float(j['trade_price']) - float(j['avg_buy_price'])
                j['mine_change_rate'] = float(j['mine_change_price']) / float(j['avg_buy_price'])
                j['mine_change_percent'] = round(float(j['mine_change_rate']) * 100, 2)
        except Market.DoesNotExist:
            market = Market.objects.create(user=request.user, market=j['market'], last_order=timezone.now() - datetime.timedelta(days=7), update_date=timezone.now() - datetime.timedelta(days=7))

    account_json_data = account_json_data[0:zero_data_index] + sorted(account_json_data[zero_data_index:], key=lambda x:float(x['acc_trade_price_24h']), reverse=True)
    
    return render(request, 'upbit/index.html', {'krw_data':krw_data, 'res':account_json_data, 'market_codes':market_names})

    
def total_market_listup(user):
    all_market = make_payload(user, "/v1/market/all", query={"isDetails":"true"})
    if 'error' in all_market:
        return all_market

    for m in all_market:
        try:
            coin_market = CoinMarket.objects.get(user=user, market=m['market'])
            coin_market.set_market_warning(m['market_warning'])
        except CoinMarket.DoesNotExist:
            coin_market = CoinMarket.objects.create(user=user, market=m['market'], korean_name=m['korean_name'], english_name=m['english_name'], market_warning=m['market_warning'])

def all_accounts_reset(user):
    coin_markets = CoinMarket.objects.filter(user=user)
    for c in coin_markets:
        c.reset_account()

def all_accounts_update(user):
    all_accounts_reset(user)
    accounts = make_payload(user, '/v1/accounts')
    if 'error' in accounts:
        return accounts

    for a in accounts:
        market_name = "{}-{}".format(a['unit_currency'], a['currency'])
        try:
            coin_market = CoinMarket.objects.get(user=user, market=market_name)
        except CoinMarket.DoesNotExist:
            if market_name == "KRW-KRW":
                coin_market = CoinMarket.objects.create(user=user, market=market_name, korean_name="원화", english_name="korean_won", market_warning="NONE")
            else:
                print("no market {}".format(market_name))
            continue
        coin_market.set_account_json(a)

def order_chance_update(user, config=None):
    total_markets = CoinMarket.objects.filter(user=user, bid_min_total=0).exclude(market="KRW-KRW")
    if config:
        total_markets = get_coin_without_unuse(config, total_markets)

    for m in total_markets:
        print("chance call {}".format(m.get_market()))
        chance = make_payload(user, '/v1/orders/chance', {'market':m.get_market()})
        if 'error' in chance:
            continue
        m.set_chance(chance)

def ticker_data_update(user, config=None):
    total_markets = CoinMarket.objects.filter(user=user, ticker_update__lt=(timezone.now() - datetime.timedelta(minutes=30))) | CoinMarket.objects.filter(user=user, trade_price__lte=0)
    if config:
        total_markets = get_coin_without_unuse(config, total_markets)
    query = {'markets':",".join(list(map(lambda x:x.get_market(), total_markets)))}
    ticker_prices = make_payload(user, '/v1/ticker', query)
    if 'error' not in ticker_prices:
        for t in ticker_prices:
            coin_market = CoinMarket.objects.get(user=user, market=t['market'])
            coin_market.set_ticker(t)
    else:
        for m in total_markets:
            print(m.get_market())
            query = {'markets':m.get_market()}
            t = make_payload(user, '/v1/ticker', query)
            if 'error' in t:
                print("{} {}".format(m.get_market(), t['error']))
                if t['error']['message'] == 'Code not found' and m.get_market() != "KRW-KRW":
                    print("{} coin delete.".format(m.get_market()))
                    m.delete()
            else:
                m.set_ticker(t[0])

def get_or_result(origin_objects, new_objects):
    if origin_objects:
        print("origin_objects {} {}".format(origin_objects, len(origin_objects)))
    else:
        print("origin_objects None None")
    print("new_objects {} {}".format(new_objects, len(new_objects)))
    return_objects = None
    if origin_objects:
        return_objects = origin_objects | new_objects
    else:
        return_objects = new_objects
    return return_objects

def get_coin_without_unuse(config, markets):
    return_markets = None
    print("krw {} usdt {} btc {}".format(config.krw_market, config.usdt_market, config.btc_market))
    if config.krw_market:
        return_markets = get_or_result(return_markets, markets.filter(market__startswith='KRW'))
    if config.usdt_market:
        return_markets = get_or_result(return_markets, markets.filter(market__startswith='USDT'))
    if config.btc_market:
        return_markets = get_or_result(return_markets, markets.filter(market__startswith='BTC'))
    return return_markets


@login_required
def new_index(request):
    try:
    config = UpbitConfig.objects.get(user=request.user)
    except UpbitConfig.DoesNotExist:
        config = UpbitConfig.objects.create(user=request.user)

    # 전체 마켓 리스트를 리스트업한다.
    # total_market_listup(request.user)

    # 계정이 소유하고있는 코인들의 데이터를 업데이트한다.
    # all_accounts_update(request.user)

    # 마켓 찬스 업데이트
    # order_chance_update(request.user, config) 

    # 티커 데이터 업데이트
    # ticker_data_update(request.user, config)

    # krw_coin = CoinMarket.objects.get(user=request.user, market="KRW-KRW")
    # krw = krw_coin.get_json()

    markets = get_coin_without_unuse(config, CoinMarket.objects.filter(user=request.user))
    if config:
    markets = markets.order_by('priority', '-buy_balance')
    context['markets'] = markets


    return render(request, 'upbit/new_index.html', context)


not_market_list = ["KRW", "VTHO"]
alter_rate = 1
not_alter_list = ['BTC', 'ETH']

def print_market_list(list_name, list):
    for m in list:
        print("{} {} {}% {}%".format(list_name, m.get_market(), m.change_rate_from_avg, m.get_signed_change_rate()))

def dryrun_inner(user):
    config = UpbitConfig.objects.get(user=user)
    total_market_listup(user)
    all_accounts_update(user)
    order_chance_update(user, config) 
    while True:
    try:
            ticker_data_update(user, config)
            break
    except json.decoder.JSONDecodeError:
            time.sleep(1)

    #총 주문액 + 잔금
    total_balance = total_order_balance + krw['int_balance']
    print("총 주문액 + 잔금액 = {}원".format(total_balance))

    alter_order_balance = total_balance * alter_rate
    one_alter_max_value = alter_order_balance / alter_count * config.alter_limit_block
    print("알터코인 한종목의 최대 지분액: {}원({}%)".format(one_alter_max_value, round(one_alter_max_value/total_balance*100, 2)))
    one_alter_max_block_count = one_alter_max_value / 5500
    print("지분액 대비 블럭수: {}".format(one_alter_max_block_count))
    alter_delay_on_oneday = 24 / one_alter_max_block_count
    hour_delay = int(alter_delay_on_oneday)
    minute_delay = int((alter_delay_on_oneday - hour_delay) * 60)
    print("하루 내 알터코인 딜레이: {}   {}시 {}분".format(alter_delay_on_oneday, hour_delay, minute_delay))
    alter_delay_on_onday_sec = hour_delay * 3600 + minute_delay * 60

    coin_markets = CoinMarket.objects.filter(user=user, last_trade__lt=(timezone.now() - datetime.timedelta(hours=1))).exclude(market="KRW-KRW")
    if config:
        coin_markets = get_coin_without_unuse(config, coin_markets)
    buy_list = coin_markets.filter(market_warning='NONE')
    buy_rate_list = buy_list.filter(change_rate_from_avg__lt=config.buy_rate).order_by('priority', 'change_rate_from_avg')
    buy_drop_list = buy_list.filter(signed_change_rate__lt=(config.get_negative_harddrop() / 100)).order_by('priority', 'signed_change_rate')
    print_market_list("buy_rate_market", buy_rate_list)
    print_market_list("buy_drop_market", buy_drop_list)
    buy_list = (buy_rate_list[:3]+buy_drop_list[:3])
    
    sell_list = coin_markets.filter(balance__gt=0)
    sell_rate_list = sell_list.filter(change_rate_from_avg__gt=config.sell_rate).order_by('priority', '-change_rate_from_avg')
    sell_drop_list = sell_list.filter(signed_change_rate__gt=(config.get_positive_harddrop() / 100)).order_by('priority', '-signed_change_rate')
    print_market_list("sell_rate_market", sell_rate_list)
    print_market_list("sell_drop_market", sell_drop_list)
    sell_list = (sell_rate_list[:3]+sell_drop_list[:3])

    print_market_list("buy_market", buy_list)
    print_market_list("sell_market", sell_list)

    print("판매 리스트 건수: {}건  구매 리스트 건수: {}건".format(len(sell_list), len(buy_list)))

    #     print("{} 코인 {}".format(b.get_currency(), b.get_priority()))
    if len(buy_list) > 7:
        config.buy_rate = config.buy_rate - 1
        print("구매 기준 변경: {}%".format(config.buy_rate))
        config.save()
    elif len(buy_list) < 1:
        config.buy_rate = config.buy_rate + 1
        print("구매 기준 변경: {}%".format(config.buy_rate))
        config.save()
 
    if len(sell_list) > 7:
        config.sell_rate = config.sell_rate + 1
        print("판매 기준 변경: {}%".format(config.sell_rate))
        config.save()
    elif len(sell_list) < 1 and config.sell_rate > 0:
        config.sell_rate = config.sell_rate - 1
        print("판매 기준 변경: {}%".format(config.sell_rate))
        config.save()
 
#  , 'krw':krw, 'alter_delay_on_onday_sec':alter_delay_on_onday_sec
    return {'buy_list':buy_list, 'sell_list':sell_list}
    

def dryrun(request):
    config = UpbitConfig.objects.get(user=request.user)
    accounts_res = make_payload(request.user, '/v1/accounts')
    hour_delay = 6
    coins = []
    total_order_balance = 0.0
    alter_count = 0
    krw_price_list = {}
    for a in accounts_res.json():
        if a['currency'] not in not_market_list:
            if a['currency'] not in not_alter_list:
                alter_count = alter_count + 1
            coins.append(Coin(a))
            krw_price_list[a['currency']] = float(a['balance']) * float(a['avg_buy_price'])
            total_order_balance = total_order_balance + krw_price_list[a['currency']]
        elif a['currency'] == "KRW":
            krw = a
            krw['int_balance'] = int(float(krw['balance']))
    query={'markets':",".join(list(map(lambda x:x.get_market(), coins)))}
    ticker_prices = make_payload(request.user, '/v1/ticker', query)

    alter_order_balance = total_order_balance * alter_rate
    one_alter_max_value = alter_order_balance / alter_count * config.alter_limit_block
    print("one alter max: " + str(one_alter_max_value) + "원")

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

        if market.get_last_order() + datetime.timedelta(hours=hour_delay) > timezone.now():
            continue

        if config.buy_rate > c.get_change_rate():
            # print("{} {}% 구매".format(c.get_market(), c.get_change_rate()))
            if c.get_currency() not in not_alter_list:
                if krw_price_list[c.get_currency()] <= one_alter_max_value:
                    print(krw_price_list[a['currency']])
                    buy_list.append(c)
                    buy_sum = buy_sum + c.get_block_size()
                else:
                    continue
            else:
                buy_list.append(c)
                buy_sum = buy_sum + c.get_block_size()
        elif config.sell_rate < c.get_change_rate() and c.get_block_count() > 0:
            # print("{} {}% 판매".format(c.get_market(), c.get_change_rate()))
            sell_list.append(c)
            sell_sum = sell_sum + c.get_block_price()
            sell_change_sum = sell_change_sum + c.get_sell_change_price()

    krw['int_require'] = round(int(buy_sum) - int(krw['int_balance']), -3) + 1000
    sell_change_rate = 0
    if sell_sum > 0:
        sell_change_rate = round(float(sell_change_sum) / float(sell_sum) * 100, 2)

    buy_list = sorted(buy_list, key=lambda x:x.get_buy_krw_price()) 

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
    priority_list = [['BTC'],['ETH']]
    priority = len(priority_list)

    def __init__(self, account):
        if 'currency' in account: # 이미 구매된 자산이 입력되는 경우
            self.currency = account['currency']
            self.market = "KRW-" + account['currency']
            self.balance = float(account['balance'])
            self.avg_buy_price = float(account['avg_buy_price'])
            block_count = self.avg_buy_price * self.balance / self.blocksize
            if block_count > 0.5 and int(block_count) == 0:
                self.blockcount = 1
            else:
                self.blockcount = int(self.avg_buy_price * self.balance / self.blocksize)
        else:
            self.market = account['market']
            self.currency = self.market.split("-")[1]
        for i, p in zip(range(len(self.priority_list)), self.priority_list):
            if self.currency in p:
                self.priority = i
        if self.currency in self.bigblock:
            self.blocksize = 11000
        # print("{} block_size:{} block_count:{}".format(self.currency, self.blocksize, self.blocksize))
        # print("{} block {}".format(self.currency, self.priority))

    def get_market(self):
        return self.market

    def get_currency(self):
        return self.currency

    def get_balance(self):
        return self.balance

    def get_buy_krw_price(self):
        return int(self.balance * self.avg_buy_price)
    
    def get_priority(self):
        return self.priority

    def get_reverse_priority(self):
        return len(self.priority_list) - self.priority

    def get_buy_krw_price_with_priority(self):
        return int(self.balance * self.avg_buy_price) - (self.get_reverse_priority() * 10000000)

    def input_ticker_price(self, ticker):
        if self.market != ticker['market']:
            print("{} != {}".format(self.market, ticker['market']))
        self.trade_price = ticker['trade_price']
        self.signed_change_price = ticker['signed_change_price']
        self.signed_change_rate = ticker['signed_change_rate']
        self.acc_trade_price_24h = ticker['acc_trade_price_24h']
        self.highest_52_week_price = ticker['highest_52_week_price']

    def gap_with_highest_balance(self):
        mine_change_price = self.trade_price - self.highest_52_week_price
        mine_change_rate = float(mine_change_price) / float(self.highest_52_week_price)
        mine_change_percent = round(float(mine_change_rate) * 100, 2)
        return mine_change_percent

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

    def get_signed_change_rate(self):
        return self.signed_change_rate * 100


def trade_block(user, trade_dict):
    query = {
        'market': trade_dict['market'],
        'side': trade_dict['side'],
        'ord_type': trade_dict['ord_type'],
    }
    if 'volume' in trade_dict:
        query['volume'] = trade_dict['volume']
    if 'price' in trade_dict:
        query['price'] = trade_dict['price']

    res_json = make_payload(user, '/v1/orders', query, method="POST")

    if 'error' not in res_json:
        try:
            market = Market.objects.get(user=user, market=trade_dict['market'])
            market.last_order = timezone.now()
            market.save()
        except Market.DoesNotExist:
            market = Market.objects.create(user=user, market=trade_dict['market'], last_order=timezone.now())
        order = Order.objects.create(user=user, market=market, created_at=timezone.now(),
                                        side=trade_dict['side'], uuid=res_json['uuid'])
        return True
    else:
        return res_json



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

        res = make_payload(request.user, '/v1/orders', query, method="POST")
        res_json = res.json()
        # print(res_json)

        if 'error' in res_json and res_json['error']['name'] == 'insufficient_funds_bid':
            query = {'amount': request.POST['price']}
            res = make_payload(request.user, '/v1/deposits/krw', query, method="POST")
            res_json = res.json()
            return HttpResponseRedirect(request.META['HTTP_REFERER'])

        if 'error' not in res_json:
            try:
                market = Market.objects.get(user=request.user, market=request.POST['market'])
                market.last_order = timezone.now()
                market.save()
            except Market.DoesNotExist:
                market = Market.objects.create(user=request.user, market=request.POST['market'], last_order=timezone.now())
            order = Order.objects.create(user=request.user, market=market, created_at=timezone.now(),
                                         side=request.POST['side'], uuid=res_json['uuid'])
        else:
            print(res_json)

    return HttpResponseRedirect(request.META['HTTP_REFERER'])


def deposit_krw(request):
    if request.method == "POST":
        query = {
            'amount': request.POST['amount']
        }

        res = make_payload(request.user, '/v1/deposits/krw', query, method="POST")
        res_json = res.json()
        print(res_json)

    return HttpResponseRedirect(request.META['HTTP_REFERER'])

def refresh_data(request):
    markets = Market.objects.filter(user=request.user, update_date__lte=(timezone.now() - datetime.timedelta(hours=12)))
    if 'error' in markets:
        return markets

    for m in markets:
        res = make_payload(request.user, '/v1/orders/chance', {'market':m.get_market()})
        m.set_chance(res.json())

        res = make_payload(request.user, '/v1/orders', {'market':m.get_market(), 'state': 'done'})
        json = res.json()
        for j in json:
            if j['side'] == 'ask' and not j['price']:
                j['price'] = get_uuid_price(request, j['uuid'])
                print(j['price'])
            elif j['side'] == 'bid' and not j['volume']:
                j['volume'] = j['executed_volume']
                # order_json = make_payload(request.user, '/v1/order', {'uuid':j['uuid']}).json()
                # print(order_json)

        m.set_orders(json)

        m.update_date = timezone.now()
        m.save()
    return HttpResponseRedirect(request.META['HTTP_REFERER'])

def get_uuid_price(request, uuid):
    order_json = make_payload(request.user, '/v1/order', {'uuid':uuid}).json()
    p_sum_volume = 0.0
    p_sum_price = 0.0
    for t in order_json['trades']:
        p_sum_volume = p_sum_volume + float(t['volume'])
        p_sum_price = p_sum_price + float(t['volume']) * float(t['price'])
    return p_sum_price / p_sum_volume

def refresh_market(request, market):
    m = Market.objects.get(user=request.user, market=market)
    orders = Order.objects.filter(user=request.user, market=m)

    for o in orders:
        o.delete()
    
    res = make_payload(request.user, '/v1/orders/chance', {'market':m.get_market()})
    m.set_chance(res.json())

    res = make_payload(request.user, '/v1/orders', {'market':m.get_market(), 'state': 'done'})
    json = res.json()
    for j in json:
        if j['side'] == 'ask' and not j['price']:
            j['price'] = get_uuid_price(request, j['uuid'])
            print(j['price'])
        elif j['side'] == 'bid' and not j['volume']:
            j['volume'] = j['executed_volume']
            # order_json = make_payload(request.user, '/v1/order', {'uuid':j['uuid']}).json()
            # print(order_json)
    m.set_orders(json)

    m.update_date = timezone.now()
    m.save()
    return HttpResponseRedirect(request.META['HTTP_REFERER'])

def detail_market(request, market):
    m = Market.objects.get(user=request.user, market=market)
    orders = Order.objects.filter(user=request.user, market=m)

    return render(request, 'upbit/detail_market.html', {'market':m, 'orders':orders})

def deposits(request):
    deposits = get_currency_list(request)

    date_list = {}
    for d in deposits:
        if d['state'] == 'ACCEPTED':
            date = d['done_at'].split('T')[0]
            if date in date_list:
                date_list[date] = date_list[date] + float(d['amount'])
            else:
                date_list[date] = float(d['amount'])

    date_list = sorted(date_list.items(), key=lambda item:item[0])

    total_amount = 0.0
    deposits = []
    for d in date_list:
        total_amount = total_amount + d[1]
        deposits.append({'date':d[0], 'amount':d[1], 'total_amount':total_amount})
    
    return render(request, 'upbit/deposits.html', {'deposits':deposits})
class SignupView(generic.edit.CreateView):
    template_name = 'registration/signup.html'
    form_class = SignupForm
    success_url = reverse_lazy('upbit:index')
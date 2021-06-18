from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid
import datetime
from upbit.api.upbit import make_payload


class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    market = models.ForeignKey('market', on_delete=models.CASCADE)
    created_at = models.DateTimeField()
    side = models.CharField(max_length=12)
    price = models.FloatField(default=0.0)
    volume = models.FloatField(default=0.0)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)


class Market(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    market = models.CharField(max_length=255, default="")
    last_order = models.DateTimeField()
    currency = models.CharField(max_length=32, default="")
    unit_currency = models.CharField(max_length=64, default="KRW")
    bid_min = models.FloatField(default=5500.0)
    ask_min = models.FloatField(default=5500.0)
    update_date = models.DateTimeField(default=(timezone.now() - datetime.timedelta(days=7)))

    def get_krw_price(self):
        return float()

    def get_last_order(self):
        last_order = Order.objects.filter(user=self.user, market=self).order_by('-created_at').first()
        if last_order:
            return last_order.created_at
        else:
            return self.last_order

    def get_currency(self):
        if not self.currency and self.market:
            self.currency = self.market.split("-")[1]
            self.save()
        return self.currency

    def get_market(self):
        return self.market

    def set_chance(self, json):
        bid_min = float(json['market']['bid']['min_total']) * 1.1
        ask_min = float(json['market']['ask']['min_total']) * 1.1
        self.save()

    def set_orders(self, json):
        for j in json:
            try:
                order = Order.objects.get(uuid=j['uuid'])
                continue
            except Order.DoesNotExist:
                order = Order.objects.create(created_at=j['created_at'],
                                             price=j['price'],
                                             side=j['side'],
                                             user=self.user,
                                             market=self,
                                             volume=j['volume'],
                                             uuid=j['uuid'])

    def get_avg_buy_price(self):
        orders = Order.objects.filter(market=self,
                                      side='bid')

        if not orders:
            print("{} no orders".format(self.market))
            return 0

        sum_volume = 0.0
        sum_price = 0.0

        for o in orders:
            sum_volume = sum_volume + o.volume
            sum_price = sum_price + o.volume * o.price
            print("{} {} / {}".format(self.market, sum_volume, sum_price))

        if sum_volume:
            return round(sum_price / sum_volume, 2)
        else:
            return 0


class CoinMarket(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    market = models.CharField(max_length=64)
    korean_name = models.CharField(max_length=64, default="")
    english_name = models.CharField(max_length=64, default="")
    market_warning = models.CharField(max_length=64, default="")
    balance = models.FloatField(default=0.0)
    avg_buy_price = models.FloatField(default=0.0)
    buy_balance = models.FloatField(default=0.0)
    
    # ticker data
    opening_price = models.FloatField(default=0.0)
    trade_price = models.FloatField(default=0.0)
    change_price = models.FloatField(default=0.0)
    change_rate = models.FloatField(default=0.0)
    signed_change_price = models.FloatField(default=0.0)
    signed_change_rate = models.FloatField(default=0.0)
    ticker_update = models.DateTimeField(default=timezone.now())

    # chance data
    bid_min_total = models.FloatField(default=0.0)

    # additional data
    priority = models.IntegerField(default=5)

    def __str__(self):
        return "[{}] {}".format(self.user, self.market)

    def get_market(self):
        return self.market

    def set_account_json(self, account):
        self.balance = float(account['balance'])
        avg_buy_price = float(account['avg_buy_price'])
        if avg_buy_price > 0:
            self.avg_buy_price = avg_buy_price
            self.buy_balance = self.balance * self.avg_buy_price
        self.save()

    def get_buy_balance(self):
        return round(self.buy_balance, 2)

    def get_current_balance(self):
        return round(self.trade_price * self.balance, 2)

    def get_earn_balance(self):
        return round(self.get_current_balance() - self.get_buy_balance(), 2)

    def get_earn_balance_rate(self):
        if self.get_buy_balance() > 0:
            return round(self.get_earn_balance() / self.get_buy_balance() * 100, 2)
        return 0.0

    def set_market_warning(self, market_warning):
        if self.market_warning != market_warning:
            self.market_warning = market_warning
            self.save()

    def get_unit_currency(self):
        unit_currency = self.market.split('-')[0]
        if unit_currency == "KRW":
            unit_currency = "원"
        return unit_currency

    def set_ticker(self, ticker):
        self.opening_price = float(ticker['opening_price'])
        self.trade_price = float(ticker['trade_price'])
        self.change_price = float(ticker['change_price'])
        self.change_rate = float(ticker['change_rate'])
        self.signed_change_price = float(ticker['signed_change_price'])
        self.signed_change_rate = float(ticker['signed_change_rate'])
        self.ticker_update = timezone.now()
        self.save()

    def set_chance(self, chance):
        self.bid_min_total = float(chance['market']['bid']['min_total'])
        self.save()

    def get_blockcount(self):
        if self.bid_min_total > 0:
            return int(self.get_buy_balance() / (self.bid_min_total * 1.1))
        else:
            return 0

    def get_bid_min_total(self):
        return int(self.bid_min_total)

    def set_priorty(self, vector):
        self.priority = self.priority + vector
        self.save()

    def get_json(self):
        return {'int_balance':self.balance}
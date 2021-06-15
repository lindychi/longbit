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
from django.db import models
from django.conf import settings

# Create your models here.
class UpbitConfig(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    access_key = models.CharField(max_length=255)
    secret_key = models.CharField(max_length=255)
    sell_rate = models.FloatField(default=7)
    buy_rate = models.FloatField(default=0)
    alter_limit_block = models.FloatField(default=2)
    hard_drop = models.FloatField(default=20)
    new_buy_rate = models.FloatField(default=-50)
    krw_market = models.BooleanField(default=True)
    btc_market = models.BooleanField(default=False)
    usdt_market = models.BooleanField(default=False)
    unit_count = models.IntegerField(default=1)
    reserve_rate = models.FloatField(default=0.5)

    def __str__(self):
        return "{} - {}".format(self.user, self.access_key)

    # def get_absolute_url(self):
    #     return reverse("_detail", kwargs={"pk": self.pk})

    def get_positive_harddrop(self):
        return abs(self.hard_drop)

    def get_negative_harddrop(self):
        return abs(self.hard_drop) * -1

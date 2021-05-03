from django.db import models
from django.conf import settings

# Create your models here.
class UpbitConfig(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    access_key = models.CharField(max_length=255)
    secret_key = models.CharField(max_length=255)

    def __str__(self):
        return "{} - {}".format(self.user, self.access_key)

    # def get_absolute_url(self):
    #     return reverse("_detail", kwargs={"pk": self.pk})

class Market(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    market = models.CharField(max_length=255, default="")
    last_order = models.DateTimeField()
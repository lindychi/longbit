from django.contrib import admin
from .models import Market
from .model.UpbitConfig import UpbitConfig

# Register your models here.
admin.site.register(UpbitConfig)
admin.site.register(Market)
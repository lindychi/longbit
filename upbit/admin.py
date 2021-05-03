from django.contrib import admin
from .models import UpbitConfig, Market

# Register your models here.
admin.site.register(UpbitConfig)
admin.site.register(Market)
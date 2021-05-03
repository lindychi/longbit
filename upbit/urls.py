
from django.contrib import admin
from django.urls import path, include
from . import views

app_name = "upbit"

urlpatterns = [
    path('', views.index, name='index'),
    path('dryrun/', views.dryrun, name='dryrun'),
    path('sell_block/', views.sell_block, name="sell_block"),
    path('deposit_krw/', views.deposit_krw, name="deposit_krw"),
]

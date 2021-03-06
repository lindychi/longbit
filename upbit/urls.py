
from django.contrib import admin
from django.urls import path, include
from . import views

app_name = "upbit"

urlpatterns = [
    path('', views.new_index, name='index'),
    path('dryrun/', views.dryrun, name='dryrun'),
    path('sell_block/', views.sell_block, name="sell_block"),
    path('deposit_krw/', views.deposit_krw, name="deposit_krw"),
    path('refresh_data/', views.refresh_data, name="refresh_data"),
    path('refresh_market/<str:market>/', views.refresh_market, name="refresh_market"),
    path('detail/<str:market>/', views.detail_market, name='detail_market'),
    path('deposits/', views.deposits, name='deposits'),
    path('new_index/', views.index, name='new_index'),
    path('user_index/<str:username>/', views.user_index, name='user_index'),
    path('admin_userlist/', views.admin_userlist, name='admin_userlist'),
    path('modify_reserve/', views.modify_reserve, name='modify_reserve'),
]

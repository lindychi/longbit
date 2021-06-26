import os
import sys
import django
import time
import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'conf.settings')
django.setup()

from django.contrib.auth import get_user_model
from upbit.views import dryrun_inner as dryrun, trade_block
from upbit.model.UpbitConfig import UpbitConfig
# from upbit.views import CoinMarket
from django.utils import timezone

def user_backrun(username):
    User = get_user_model()
    user = User.objects.get(username=username)
    config = UpbitConfig.objects.get(user=user)

    while True:
        print()
        print(timezone.now() + datetime.timedelta(hours=9))
        time.sleep(1)
        dryrun_dict = dryrun(user)
        # if dryrun_dict is False:
        #     continue
        if len(dryrun_dict['buy_list']) < 1 or len(dryrun_dict['buy_list']) > 7:
            continue

        for s in dryrun_dict['sell_list']:
            ask = {'market':s.get_market(), 'volume':s.get_sell_balance(), 'ord_type':'market', 'side':'ask'}
            res = trade_block(user, ask)
            
            if res is True:
                print("{} 판매 완료 volume:{}{}".format(s.get_market(), s.get_sell_balance(), s.get_currency()))
                s.sell_success()
            else:
                print(ask)
                print(res)
            time.sleep(0.5)

        # time.sleep(1)
        # dryrun_dict = dryrun(user)
        # if dryrun_dict is False:
        #     time.sleep(600)
        #     continue

        # print("주문 가능 금액: {}원".format(dryrun_dict['krw']['int_balance']))
        for b in dryrun_dict['buy_list']:
            bid = {'market':b.get_market(), 'price':b.get_block_size(), 'ord_type':'price', 'side':'bid'}
            res = trade_block(user, bid)
            if res is True:
                print("{} 구매 완료 price: {}원".format(b.get_market(), b.get_block_size()))
                b.buy_success()
            else:
                print(bid)
                print(res)
                # if res['error']['name'] == 'insufficient_funds_bid':
                #     break
            time.sleep(0.5)
        # cycle_delay_sec = int(dryrun_dict['alter_delay_on_onday_sec'] * 600 / 18000 * 10)
        # print("회차 대기 시간: {}초({}분 {}초)".format(cycle_delay_sec, int(cycle_delay_sec/60), (cycle_delay_sec%60)))
        # time.sleep(cycle_delay_sec)
        time.sleep(1800)

if __name__ == "__main__":
    arguments = sys.argv
    user_backrun(arguments[1])
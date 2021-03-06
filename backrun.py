import os
import sys
import django
import time
import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'conf.settings')
django.setup()

from django.contrib.auth import get_user_model
from upbit.views import dryrun_inner as dryrun, trade_block, get_current_krw, dryrun_update
from upbit.model.UpbitConfig import UpbitConfig
from upbit.models import SellResult
# from upbit.views import CoinMarket
from django.utils import timezone

def user_backrun(username):
    User = get_user_model()
    user = User.objects.get(username=username)
    config = UpbitConfig.objects.get(user=user)
    try:
        sr = SellResult.objects.get(user=user)
    except SellResult.DoesNotExist:
        sr = SellResult.objects.create(user=user)

    while True:
        print()
        print(timezone.now() + datetime.timedelta(hours=9))
        time.sleep(1)
        dryrun_dict = dryrun(user)

        # if len(dryrun_dict['buy_list']) < 1 or len(dryrun_dict['buy_list']) > 7:
        #     continue

        for s in dryrun_dict['sell_list']:
            current_krw = float(get_current_krw(user)['balance'])
            gap_krw = 0

            (total_sell_balance, sell_block_count, sell_block_balance) = s.get_sell_balance()
            ask = {'market':s.get_market(), 'volume':total_sell_balance, 'ord_type':'market', 'side':'ask'}
            res = trade_block(user, ask)
            
            if res is True:
                print("{} ํ๋งค ์๋ฃ volume:{}{}".format(s.get_market(), total_sell_balance, s.get_currency()))
                s.sell_success()

                while True:
                    after_krw = float(get_current_krw(user)['balance'])
                    if current_krw < after_krw:
                        print("'{}' < '{}'".format(current_krw, after_krw))
                        gap_krw = after_krw - current_krw
                        break
                    time.sleep(0.1)
                    
                if sell_block_count * s.get_block_size() < gap_krw:
                    gap_incre_krw = gap_krw - ( sell_block_count * s.get_block_size() )
                    sr.add_new_trade(sell_block_count * s.get_block_size(), gap_krw)
                    print("๋งค๋์? ๋งค๋ํ ์ฐจ์ก: {}์  ์ด์ต๊ธ: {}์  ์?๋ณด๊ธ: {}์  ๊ตฌ๋งค์ก: {}์  ํ๋งค์ก: {}์".format(gap_krw, gap_incre_krw, gap_incre_krw * config.reserve_rate, sell_block_count * s.get_block_size(), gap_krw))
            else:
                print(ask)
                print(res)
            time.sleep(0.5)

        for b in dryrun_dict['buy_list']:
            # ์?๋ณด๊ธ์ ์?์ธํ ๊ธ์ก์ด ๊ตฌ๋งค๊ฐ ๋ถ๊ฐ๋ฅํ? ๊ฒฝ์ฐ ์?๋ณด
            current_krw = float(get_current_krw(user)['balance']) - sr.get_reserve(config)
            if current_krw < b.get_block_size():
                print("๊ตฌ๋งค ๋ถ๊ฐ๋ฅํ ์ฌ์? ์๊ธ: {}์ ์?๋ณด๊ธ:{}์".format(current_krw, sr.get_reserve(config)))
                continue

            bid = {'market':b.get_market(), 'price':b.get_block_size(), 'ord_type':'price', 'side':'bid'}
            res = trade_block(user, bid)
            if res is True:
                print("{} ๊ตฌ๋งค ์๋ฃ price: {}์".format(b.get_market(), b.get_block_size()))
                b.buy_success()
            else:
                print(bid)
                print(res)
            time.sleep(0.5)
        # cycle_delay_sec = int(dryrun_dict['alter_delay_on_onday_sec'] * 600 / 18000 * 10)
        # print("ํ์ฐจ ๋๊ธฐ ์๊ฐ: {}์ด({}๋ถ {}์ด)".format(cycle_delay_sec, int(cycle_delay_sec/60), (cycle_delay_sec%60)))
        # time.sleep(cycle_delay_sec)
        dryrun_update(user)
        time.sleep(1800)

if __name__ == "__main__":
    arguments = sys.argv
    if len(arguments) >= 3:
        time.sleep(int(arguments[2]))
    user_backrun(arguments[1])
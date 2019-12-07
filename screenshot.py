# coding: utf-8

"""
定时执行抓取任务，图像识别并入库（夜间模式只抓取，不识别）
"""

from selenium import webdriver
from datetime import datetime
import traceback
import pymysql
import time
import sys
import logging
import requests
from apscheduler.schedulers.blocking import BlockingScheduler
from utils import parse_image

db_opt = {
    'host': '127.0.0.1', 'user': 'root', 'passwd': 'test',
    'db': 'bonus',
}

"""
TODO:

1.
552 期 【 108侣
552 期 [X] 借

返回 -1

2.
552 期 【 108侣
552 期 [X] 1 借

返回-1

3.
reset时结合select出来的结果处理
"""


def screenshot():
    now = datetime.now()
    print "do screenshot: {0}".format(now)
    filename = "./images/{0}.png".format(now.strftime("%Y%m%d%H%M"))
    try:
        # 1. 网页截图
        option = webdriver.ChromeOptions()
        option.add_argument('disable-infobars')
        option.add_argument('headless')
        browser = webdriver.Chrome('./chromedriver', chrome_options=option)
        browser.get('https://69960a.com/chat/index.html?web#/room/879')
        # 等10s页面完全刷新
        time.sleep(5)
        browser.save_screenshot(filename)
        browser.close()

        if night_mode:
            # 夜间模式直接入库-1
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute(
                'INSERT INTO rounds(bet_timestamp, state) VALUES(%s,-1)',
                [now.strftime("%Y%m%d%H%M"), ]
            )
            cursor.close()
            return

        # 2. 图像识别
        roundid, bet_map = parse_image(filename)

        state = 0
        # 3. 错误处理
        if roundid == -1:
            print "invalid file: {0}".format(filename)
            bet_map[roundid] = {}
            state = -1

        # 出现9倍发送消息
        if bet_map[roundid].get('bet_single', 0) == 9 or bet_map[roundid].get('bet_double', 0) == 9 or bet_map[roundid].get('bet_small', 0) == 9 or bet_map[roundid].get('bet_big', 0) == 9:
            requests.get('http://xb.matrix.netease.com:4179/push_msg?users=["cgn4196@corp.netease.com"]&msg=999')

        # 当bet_a和bet_b有且仅有一个>0，另一个为0时，记录有效
        if not ((bet_map[roundid].get('bet_single', 0) > 0 and bet_map[roundid].get('bet_double', 0) == 0) or (bet_map[roundid].get('bet_double', 0) > 0 and bet_map[roundid].get('bet_single', 0) == 0)):
            print "invalid single_double"
            state = -1

        if not ((bet_map[roundid].get('bet_small', 0) > 0 and bet_map[roundid].get('bet_big', 0) == 0) or (bet_map[roundid].get('bet_big', 0) > 0 and bet_map[roundid].get('bet_small', 0) == 0)):
            print "invalid big_small"
            state = -1

        # 4. 入库
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute(
            ('INSERT INTO rounds(bet_timestamp, bet_single, bet_double, '
             'bet_big, bet_small, roundid, state) '
             'VALUES(%s,%s,%s,%s,%s,%s,%s)'
             ),
            [now.strftime("%Y%m%d%H%M"),
             str(bet_map[roundid].get('bet_single', 0)),
             str(bet_map[roundid].get('bet_double', 0)),
             str(bet_map[roundid].get('bet_big', 0)),
             str(bet_map[roundid].get('bet_small', 0)),
             str(roundid),
             str(state)]
        )
        cursor.close()

    except Exception:
        print "invalid file: {0}".format(filename)
        print traceback.format_exc()


try:
    conn = pymysql.connect(**db_opt)
    conn.autocommit(True)
    night_mode = False
    if len(sys.argv) == 2 and sys.argv[1] == 'n':
        # 夜间模式：只截图，不计算；入库为-1
        night_mode = True

except Exception:
    print "init mysql error"
    print traceback.format_exc()
    sys.exit(1)

logging.basicConfig()
scheduler = BlockingScheduler()
scheduler.add_job(screenshot, 'cron', second='30', max_instances=3)
scheduler.start()

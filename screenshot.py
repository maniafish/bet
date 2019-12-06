# coding: utf-8

"""
定时执行抓取任务，图像识别并入库（夜间模式只抓取，不识别）
"""

from selenium import webdriver
from datetime import datetime
from PIL import Image
import pytesseract
import traceback
import pymysql
import time
import sys
import logging
from apscheduler.schedulers.blocking import BlockingScheduler

db_opt = {
    'host': '127.0.0.1', 'user': 'root', 'passwd': 'test',
    'db': 'bonus',
}

"""
TODO:

2. 图片重算：对state = -1的图片进行重算；对计算后仍无法满足条件的，进行截图重算
3. 入库结果校验
"""


def set_multi(line):
    """ 解析行中的轮次和倍率 """
    print line
    s = line.split()
    try:
        roundid = int(s[0])
        bet = 0
        # 反向遍历第一个数字为倍率
        for i in range(len(s)-1, 0, -1):
            try:
                bet = int(s[i])
                break
            except:
                continue

        if not bet:
            raise
    except Exception:
        print "invalid line: {0}".format(line)
        return -1, 0

    return roundid, bet


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
        time.sleep(10)
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
        out = pytesseract.image_to_string(Image.open(filename), lang='chi_sim')
        bet_map = {}
        roundid = -1
        state = 0
        bet_type = ''
        bet = 0
        # 永远以最近的一条为准
        for line in out.split('\n'):
            if line.find(u'期') > 0:
                if line.find(u'双') > 0:
                    roundid, bet = set_multi(line)
                    bet_type = 'double'
                elif line.find(u'单') > 0:
                    roundid, bet = set_multi(line)
                    bet_type = 'single'
                elif line.find(u'大') > 0:
                    roundid, bet = set_multi(line)
                    bet_type = 'big'
                elif line.find(u'小') > 0 or line.find('JJ') > 0:
                    roundid, bet = set_multi(line)
                    bet_type = 'small'

                # 没有就创建
                if not bet_map.get(roundid):
                    bet_map[roundid] = {bet_type: bet}
                else:
                    bet_map[roundid][bet_type] = bet

        if roundid == -1:
            print "invalid file: {0}".format(filename)
            bet_map[roundid] = {}
            state = -1

        # 当bet_a和bet_b有且仅有一个>0，另一个为0时，记录有效
        if not ((bet_map[roundid].get('single', 0) > 0 and bet_map[roundid].get('double', 0) == 0) or (bet_map[roundid].get('double', 0) > 0 and bet_map[roundid].get('single', 0) == 0)):
            print "invalid single_double"
            state = -1

        if not ((bet_map[roundid].get('small', 0) > 0 and bet_map[roundid].get('big', 0) == 0) or (bet_map[roundid].get('big', 0) > 0 and bet_map[roundid].get('small', 0) == 0)):
            print "invalid big_small"
            state = -1

        # 3. 入库
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute(
            ('INSERT INTO rounds(bet_timestamp, bet_single, bet_double, '
             'bet_big, bet_small, roundid, state) '
             'VALUES(%s,%s,%s,%s,%s,%s,%s)'
             ),
            [now.strftime("%Y%m%d%H%M"),
             str(bet_map[roundid].get('single', 0)),
             str(bet_map[roundid].get('double', 0)),
             str(bet_map[roundid].get('big', 0)),
             str(bet_map[roundid].get('small', 0)),
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
scheduler.add_job(screenshot, 'cron', second='40')
scheduler.start()

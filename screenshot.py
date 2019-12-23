# coding: utf-8

"""
定时执行抓取任务，图像识别并入库
"""

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import traceback
import pymysql
import logging
import requests
from apscheduler.schedulers.blocking import BlockingScheduler
from utils import parse_image
from conf import req, db_opt
from urllib import quote
import time


"""
TODO:
1. 网络状况差时的截图处理
2. 失败未入库的情况
"""
succ = 100


def screenshot():
    now = datetime.now()
    # 夜晚不做处理
    if now.hour < 8:
        return

    timestamp = now.strftime("%Y%m%d%H%M")
    print "do screenshot: {0}".format(now)
    filename = "./images/{0}.png".format(now.strftime("%Y%m%d%H%M"))
    try:
        # 1. 网页截图
        option = webdriver.ChromeOptions()
        option.add_argument('disable-infobars')
        option.add_argument('headless')
        browser = webdriver.Chrome('./chromedriver', chrome_options=option)
        browser.set_page_load_timeout(15)
        browser.set_script_timeout(15)
        browser.get('https://69960a.com/chat/index.html?web#/room/879')
        max_retry = 3
        while max_retry > 0:
            try:
                # 至多等5s
                element = WebDriverWait(browser, 5)
                element.until(EC.presence_of_element_located((By.XPATH, '//script[contains(@src, "app")]')))
                # 等5s保证刷新
                time.sleep(5)
                browser.save_screenshot(filename)
                # 设置max_retry值=succ，表示抓取成功
                max_retry = succ
                break
            except TimeoutException:
                # 超时刷新重新等待
                print "get page timeout"
                browser.refresh()
                max_retry -= 1
                continue
            except Exception:
                print traceback.format_exc()
                break

        browser.quit()
        if max_retry != succ:
            print "get page failed"
            raise

        # 2. 图像识别
        roundid, bet_map = parse_image(filename)
        print "roundid: {0}, bet_map: {1}".format(roundid, bet_map)

        state = 0
        # 3. 错误处理
        if roundid == -1:
            print "invalid file: {0}".format(filename)
            bet_map[roundid] = {}
            state = -1

        # 当bet_a和bet_b有且仅有一个>0，另一个为0时，记录有效
        if not ((bet_map[roundid].get('bet_single', 0) > 0 and bet_map[roundid].get('bet_double', 0) == 0) or (bet_map[roundid].get('bet_double', 0) > 0 and bet_map[roundid].get('bet_single', 0) == 0)):
            print "invalid single_double"
            state = -1

        if not ((bet_map[roundid].get('bet_small', 0) > 0 and bet_map[roundid].get('bet_big', 0) == 0) or (bet_map[roundid].get('bet_big', 0) > 0 and bet_map[roundid].get('bet_small', 0) == 0)):
            print "invalid big_small"
            state = -1

        # 4. 入库
        conn = pymysql.connect(**db_opt)
        conn.autocommit(True)
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute(
            ('INSERT INTO rounds(bet_timestamp, bet_single, bet_double, '
             'bet_big, bet_small, roundid, state) '
             'VALUES(%s,%s,%s,%s,%s,%s,%s)'
             ),
            [timestamp,
             str(bet_map[roundid].get('bet_single', 0)),
             str(bet_map[roundid].get('bet_double', 0)),
             str(bet_map[roundid].get('bet_big', 0)),
             str(bet_map[roundid].get('bet_small', 0)),
             str(roundid),
             str(state)]
        )
        cursor.close()

        # 状态错误发送信息
        msg = quote("{0}: -1".format(timestamp))
        if state == -1:
            requests.get("{0}{1}".format(req, msg))

    except Exception:
        print "invalid file: {0}".format(filename)
        print traceback.format_exc()
        msg = quote("{0}: traceback".format(timestamp))
        requests.get("{0}{1}".format(req, msg))


logging.basicConfig()
scheduler = BlockingScheduler()
scheduler.add_job(screenshot, 'cron', second='25', max_instances=5)
scheduler.start()

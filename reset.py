# coding: utf-8

"""
重新识别数据库中状态为-1的轮次
"""

import pymysql
import traceback
from utils import parse_image
from datetime import datetime, timedelta

db_opt = {
    'host': '127.0.0.1', 'user': 'root', 'passwd': 'test',
    'db': 'bonus',
}

begin_date = 201912070000
end_date = 201912080000
bet_list = [1, 3, 9]


def set_multi(line):
    """ 解析行中的轮次和倍率 """
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
        print traceback.format_exc()
        return -1, 0

    return roundid, bet


def get_bet_duration(bet_timestamp):
    """ 读取前1分钟到后10分钟的数据 """
    t = datetime.strptime(str(bet_timestamp), "%Y%m%d%H%M")
    begin_t = t - timedelta(minutes=1)
    end_t = t + timedelta(minutes=10)
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute(
        ('SELECT bet_timestamp, bet_single, bet_double, bet_small, bet_big '
         'FROM rounds WHERE bet_timestamp BETWEEN %s AND %s ORDER BY bet_timestamp'),
        [begin_t.strftime("%Y%m%d%H%M"),
         end_t.strftime("%Y%m%d%H%M")],
    )

    r = cursor.fetchall()
    cursor.close()
    return r


def do_traverse(r, j, bet_a, bet_b, expect):
    while j < len(r):
        # 预测值递增
        if expect in bet_list:
            # 前几轮倍率 * 3
            expect = expect * 3
        else:
            # 几轮后倍率 * 2
            expect = expect * 2

        # 遍历到第一个有效数据
        if (r[j][bet_a] > 0 and r[j][bet_b] == 0) or (r[j][bet_b] > 0 and r[j][bet_a] == 0):
            post_bet = r[j][bet_a] if r[j][bet_a] > 0 else r[j][bet_b]
            if post_bet == expect:
                return True

            return False

        j += 1

    return False


def traverse_bet(bet_timestamp, bet_a, bet_b):
    """ 拿前一轮的向后遍历，预测本轮的bet """
    """ 预测失败返回bet_b, 0, False；成功返回bet_type, <预测值>, True """
    try:
        # 读取前1分钟到后10分钟的数据
        r = get_bet_duration(bet_timestamp)
        # 至少要有前一轮和后一轮的数据
        if len(r) < 3 or r[0]['bet_timestamp'] >= bet_timestamp or r[1]['bet_timestamp'] != bet_timestamp or r[2]['bet_timestamp'] <= bet_timestamp:
            print "{0} invalid rounds: {1}".format(bet_timestamp, r)
            return bet_b, 0, False

        # 默认bet_type为bet_b
        bet_type = bet_b
        pre_bet = 0
        # 上轮有效的，bet_type取上轮的值
        if r[0][bet_a] > 0 and r[0][bet_b] == 0:
            bet_type = bet_a
            pre_bet = r[0][bet_a]
        elif r[0][bet_b] > 0 and r[0][bet_a] == 0:
            bet_type = bet_b
            pre_bet = r[0][bet_b]

        # 本轮从1开始，看是否能够命中
        expect = 1
        if do_traverse(r, 2, bet_a, bet_b, expect):
            return bet_type, expect, True

        if pre_bet > 0:
            # 本轮expect较上轮递增
            if pre_bet in bet_list:
                # 前几轮倍率 * 3
                expect = pre_bet * 3
            else:
                # 几轮后倍率 * 2
                expect = pre_bet * 2

            if do_traverse(r, 2, bet_a, bet_b, expect):
                return bet_type, expect, True

        return bet_b, 0, False

    except Exception:
        print traceback.format_exc()
        return bet_b, 0, False


try:
    conn = pymysql.connect(**db_opt)
    conn.autocommit(True)
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute(
        ('SELECT bet_timestamp, bet_small, bet_big, bet_single, bet_double '
         'FROM rounds WHERE state != 0'
         'AND bet_timestamp BETWEEN %s AND %s ORDER BY bet_timestamp'),
        [str(begin_date), str(end_date)]
    )
    r = cursor.fetchall()
    cursor.close()
    for i in range(0, len(r)):
        filename = './images/{0}.png'.format(r[i]['bet_timestamp'])
        print "parse file: {0}".format(filename)
        roundid, bet_map = parse_image(filename)

        if roundid == -1:
            # 完全没解出来的，就不用挣扎了
            print "invalid file: {0}".format(filename)
            continue

        state = 0
        print "debug bet_map:", bet_map
        # 当bet_a和bet_b有且仅有一个>0，另一个为0时，记录有效
        # 单双没解出来的，递归预测出一个结果来
        if not ((bet_map[roundid].get('bet_single', 0) > 0 and bet_map[roundid].get('bet_double', 0) == 0) or (bet_map[roundid].get('bet_double', 0) > 0 and bet_map[roundid].get('bet_single', 0) == 0)):
            bet_type, bet, ok = traverse_bet(r[i]['bet_timestamp'], 'bet_single', 'bet_double')
            if ok:
                bet_map[roundid][bet_type] = bet
                state = 1
            else:
                state = -1

        # 大小没解出来的，递归预测出一个结果来
        if not ((bet_map[roundid].get('bet_small', 0) > 0 and bet_map[roundid].get('bet_big', 0) == 0) or (bet_map[roundid].get('bet_big', 0) > 0 and bet_map[roundid].get('bet_small', 0) == 0)):
            bet_type, bet, ok = traverse_bet(r[i]['bet_timestamp'], 'bet_small', 'bet_big')
            if ok:
                bet_map[roundid][bet_type] = bet
                state = 1
            else:
                state = -1

        print "debug", roundid, "bet_map after set:", bet_map
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute(
            ('UPDATE rounds SET bet_single = %s, bet_double = %s, '
             'bet_big = %s, bet_small = %s, roundid = %s, state = %s '
             'WHERE bet_timestamp = %s'),
            [str(bet_map[roundid].get('bet_single', 0)),
             str(bet_map[roundid].get('bet_double', 0)),
             str(bet_map[roundid].get('bet_big', 0)),
             str(bet_map[roundid].get('bet_small', 0)),
             str(roundid),
             str(state),
             str(r[i]['bet_timestamp'])]
        )
        cursor.close()

except Exception:
    print traceback.format_exc()

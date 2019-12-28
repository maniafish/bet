# coding: utf-8

"""
分析预测数据库中状态为-1的轮次
"""

import pymysql
import traceback
from datetime import datetime, timedelta
from conf import db_opt

bet_list = [1, 3, 9]


def get_bet_duration(bet_timestamp):
    """ 读取前1分钟到后2分钟的数据 """
    t = datetime.strptime(str(bet_timestamp), "%Y%m%d%H%M")
    begin_t = t - timedelta(minutes=1)
    end_t = t + timedelta(minutes=2)
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

            post_expect = expect
            if do_traverse(r, 2, bet_a, bet_b, expect):
                return bet_type, expect, True

        # 实在预测不中，就用上一轮的下个倍率作为expect
        return bet_type, post_expect, True

    except Exception:
        print traceback.format_exc()
        return bet_b, 0, False


try:
    conn = pymysql.connect(**db_opt)
    conn.autocommit(True)
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute(
        ('SELECT bet_timestamp, bet_small, bet_big, bet_single, bet_double, roundid, state '
         'FROM rounds WHERE state = -1 ORDER BY bet_timestamp'),
    )
    r = cursor.fetchall()
    cursor.close()
    # 默认state
    state = 1
    for i in range(0, len(r)):
        print i, 'before reset', r[i]
        # 当bet_a和bet_b有且仅有一个>0，另一个为0时，记录有效
        # 单双没解出来的，递归预测出一个结果来
        if not ((r[i].get('bet_single', 0) > 0 and r[i].get('bet_double', 0) == 0) or (r[i].get('bet_double', 0) > 0 and r[i].get('bet_single', 0) == 0)):
            bet_type, bet, ok = traverse_bet(r[i]['bet_timestamp'], 'bet_single', 'bet_double')
            if ok:
                r[i][bet_type] = bet
                state = 1
            else:
                state = -1

        # 大小没解出来的，递归预测出一个结果来
        if not ((r[i].get('bet_small', 0) > 0 and r[i].get('bet_big', 0) == 0) or (r[i].get('bet_big', 0) > 0 and r[i].get('bet_small', 0) == 0)):
            bet_type, bet, ok = traverse_bet(r[i]['bet_timestamp'], 'bet_small', 'bet_big')
            if ok:
                r[i][bet_type] = bet
                # 单双没问题，大小也没问题才设置
                if state != -1:
                    state = 1
            else:
                state = -1

        r[i]['state'] = state
        print i, 'after reset', r[i]
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute(
            ('UPDATE rounds SET bet_single = %s, bet_double = %s, '
             'bet_big = %s, bet_small = %s, state = %s '
             'WHERE bet_timestamp = %s'),
            [str(r[i].get('bet_single', 0)),
             str(r[i].get('bet_double', 0)),
             str(r[i].get('bet_big', 0)),
             str(r[i].get('bet_small', 0)),
             str(r[i].get('state', -1)),
             str(r[i]['bet_timestamp'])]
        )
        cursor.close()

except Exception:
    print traceback.format_exc()

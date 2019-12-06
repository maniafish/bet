# coding: utf-8

import pymysql
import traceback
import sys
from datetime import datetime

begin_date = 201912050000
end_date = 201912060000
bet_list = [1, 3, 9]

db_opt = {
    'host': '127.0.0.1', 'user': 'root', 'passwd': 'test',
    'db': 'bonus',
}


def filename(ts):
    t = datetime.fromtimestamp(ts)
    return "{0}.png".format(t.strftime("%Y%m%d%H%M%S"))


def do_traverse(r, j, bet_a, bet_b, expect):
    while j < len(r):
        # 遍历到第一个有效数据
        if (r[j][bet_a] > 0 and r[j][bet_b] == 0) or (r[j][bet_b] > 0 and r[j][bet_a] == 0):
            post_bet = r[j][bet_a] if r[j][bet_a] > 0 else r[j][bet_b]
            if post_bet == expect:
                return True

            return False

        # 预测值递增
        if expect in bet_list:
            # 前几轮倍率 * 3
            expect = expect * 3
        else:
            # 几轮后倍率 * 2
            expect = expect * 2

        j += 1

    return False


def traverse_bet(r, i, bet_a, bet_b):
    """ 拿前一轮的向后遍历，预测本轮的bet """
    """ 预测失败返回1, False；成功返回<预测值>, True """
    pre_bet = r[i][bet_a] if r[i][bet_a] > 0 else r[i][bet_b]
    if pre_bet == 0:
        return 1, False

    # 本轮expect较上轮递增
    if pre_bet in bet_list:
        # 前几轮倍率 * 3
        expect = pre_bet * 3
    else:
        # 几轮后倍率 * 2
        expect = pre_bet * 2

    # 校验expect
    if do_traverse(r, i+1, bet_a, bet_b, expect):
        return expect, True

    # 本轮expect从头开始
    expect = 1
    if do_traverse(r, i+1, bet_a, bet_b, expect):
        return expect, True

    return 1, False


def check_rounds(r):
    """ 检查轮次 """
    for i in range(0, len(r)):
        if i - 1 >= 0 and r[i]['roundid'] != r[i-1]['roundid'] + 1 and r[i]['roundid'] != 0:
            print "{0}.png".format(r[i]['bet_timestamp'])


def check(r, bet_a, bet_b, cursor):
    """ 检查单双/大小 """
    for i in range(0, len(r)):
        # 当bet_a和bet_b有且仅有一个>0，另一个为0时，记录有效
        if not ((r[i][bet_a] > 0 and r[i][bet_b] == 0) or (r[i][bet_b] > 0 and r[i][bet_a] == 0)):
            # 上一轮有效
            if i - 1 >= 0:
                # 从上一轮开始遍历，预测本轮数据
                r[i][bet_b], ok = traverse_bet(r, i-1, bet_a, bet_b)
                if ok:
                    print "{0}.png".format(r[i]['bet_timestamp']), r[i][bet_b], "fixed"
                    # 修正记录
                    cursor.execute(
                        'UPDATE rounds SET {0}=%s, state=1 WHERE bet_timestamp=%s'.format(bet_b),
                        [r[i][bet_b], r[i]['bet_timestamp']]
                    )
                    continue

            print "{0}.png".format(r[i]['bet_timestamp']), 0


if len(sys.argv) < 2:
    print "1: check rounds"
    print "2: check big_small"
    print "3: check single_double"
    sys.exit(1)

try:
    check_flag = int(sys.argv[1])
    conn = pymysql.connect(**db_opt)
    conn.autocommit(True)
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute(
        ('SELECT bet_timestamp, bet_single, bet_double, '
         'bet_big, bet_small, roundid, state FROM rounds '
         'WHERE bet_timestamp BETWEEN %s AND %s '
         'ORDER BY bet_timestamp'),
        [str(begin_date), str(end_date)]
    )

    r = cursor.fetchall()
    # 任何一种检查，都要人为保证首条记录正确
    if check_flag == 1:
        check_rounds(r)
    elif check_flag == 2:
        check(r, 'bet_big', 'bet_small', cursor)
    elif check_flag == 3:
        check(r, 'bet_single', 'bet_double', cursor)

except Exception:
    print traceback.format_exc()

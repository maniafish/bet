# coding: utf-8

"""
模拟下注
"""

from conf import db_opt
import pymysql
import traceback
import sys
import matplotlib
matplotlib.use('TkAgg')

import matplotlib.pyplot as plt


begin_date = 201912110000
end_date = 201912130000

lazer_types = [
    'b-', 'r-', 'g-', 'c-', 'm-', 'y-', 'k-',
]

# 下注矩阵
bet_list = [1, 3]
# 最大下注轮数
max_bet = len(bet_list)

# 下注倍数
multi_bet = 1
factor_bet = [max_bet-1, max_bet-1]
bet_counting = [0, 0]
principal = 40.0


def check_bonus(actual_bet, bet_type):
    global factor_bet
    global principal
    # 下注过程中回归bet，说明下注成功
    if bet_counting[bet_type] == 1 and actual_bet == bet_list[0]:
        principal += 1.96 * multi_bet * bet_list[factor_bet[bet_type]]
        # 回归下注因子
        factor_bet[bet_type] = max_bet - 1


def do_bet(actual_bet, bet_type):
    """ 下注 """
    global factor_bet
    global bet_counting
    global principal
    # 持续下注
    factor_bet[bet_type] = (factor_bet[bet_type] + 1) % max_bet
    print "do {0} bet".format(bet_type), multi_bet * bet_list[factor_bet[bet_type]]
    principal -= multi_bet * bet_list[factor_bet[bet_type]]
    bet_counting[bet_type] = 1


def reset_multi(principal):
    """ 重设每日倍率 """
    global factor_bet
    global bet_counting
    global multi_bet
    sum_bet = 0
    for i in bet_list:
        sum_bet += i

    multi_bet = principal / 10.0 / sum_bet
    bet_counting = [0, 0]
    factor_bet = [max_bet-1, max_bet-1]


try:
    conn = pymysql.connect(**db_opt)
    conn.autocommit(True)
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute(
        ('SELECT bet_timestamp, bet_small, bet_big, bet_single, bet_double FROM rounds '
         'WHERE bet_timestamp BETWEEN %s AND %s ORDER BY bet_timestamp'),
        [str(begin_date), str(end_date)]
    )
    r = cursor.fetchall()
    cursor.close()

    # key: 日期, value: 轮次列表
    rounds = {}
    # key: 日期, value: 大小bet值
    beta_list = {}
    # key: 日期, value: 单双bet值
    betb_list = {}
    principal_list = [principal]
    temp_date = 0
    temp_principal = 0
    for i in range(0, len(r)):
        bet_a = r[i]["bet_big"] if r[i]["bet_big"] else r[i]["bet_small"]
        bet_b = r[i]["bet_single"] if r[i]["bet_single"] else r[i]["bet_double"]
        print "bet_timestamp: {0} - big_small: {1} - single_double: {2}".format(
            r[i]['bet_timestamp'], bet_a, bet_b)

        date = r[i]['bet_timestamp'] / 10000
        rnd = r[i]['bet_timestamp'] % 10000
        # 新的一天
        if date != temp_date:
            temp_principal = principal
            reset_multi(temp_principal)

        temp_date = date
        if not rounds.get(date, None):
            rounds[date] = [rnd]
            beta_list[date] = [bet_a]
            betb_list[date] = [bet_b]
        else:
            rounds[date].append(rnd)
            beta_list[date].append(bet_a)
            betb_list[date].append(bet_b)

        if (rnd > 1330 and rnd < 1410):
            # 检查本次是否盈利
            check_bonus(bet_a, 0)
            check_bonus(bet_b, 1)

            # 止盈和止损
            if principal >= 0.7 * temp_principal and principal <= 1.3 * temp_principal:
                do_bet(bet_a, 0)
                do_bet(bet_b, 1)
                principal_list.append(principal)
            else:
                bet_counting = [0, 0]

        print "principal:", principal
        print "--------------------------------------------------"

    if len(sys.argv) == 2 and sys.argv[1] == 'p':
        plt.title('show bet trend')
        plt.xlabel('round')
        plt.ylabel('bet')
        for date in rounds:
            lazer_type_a = 0
            lazer_type_b = 1
            if date == 20191210:
                lazer_type_a = 2
                lazer_type_b = 3

            plt.plot(rounds[date],
                     beta_list[date],
                     lazer_types[lazer_type_a],
                     label='small_big.{0}'.format(date))

            plt.plot(rounds[date],
                     betb_list[date],
                     lazer_types[lazer_type_b],
                     label='single_double.{0}'.format(date))

        plt.legend()
        plt.show()
    else:
        plt.title('show principal trend')
        plt.xlabel('round')
        plt.ylabel('principal')
        plt.plot(range(0, len(principal_list)),
                 principal_list,
                 lazer_types[0],
                 label='principal'.format(date))
        plt.legend()
        plt.show()

except Exception:
    print traceback.format_exc()

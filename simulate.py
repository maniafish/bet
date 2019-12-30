# coding: utf-8

"""
模拟下注
"""

from conf import db_opt
from strategy import BetSmall
import pymysql
import traceback


begin_date = 20191207
end_date = 20191228

try:
    conn = pymysql.connect(**db_opt)
    conn.autocommit(True)
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    s = BetSmall(500, 1)
    for i in range(begin_date, end_date):
        cursor.execute(
            ('SELECT bet_timestamp, bet_small, bet_big, bet_single, bet_double FROM rounds '
             'WHERE bet_timestamp BETWEEN %s AND %s ORDER BY bet_timestamp'),
            [i*10000, (i+1)*10000]
        )
        r = cursor.fetchall()
        bet_dict = s.do_bet(r)
        for j in bet_dict:
            sql = (
                'INSERT INTO principals(bet_timestamp, {0}) '
                'VALUES(%s, %s) ON DUPLICATE KEY UPDATE {0} = %s'
            ).format(s.get_name(), s.get_name())
            cursor.execute(sql, [j, bet_dict[j], bet_dict[j]])

except Exception:
    print traceback.format_exc()

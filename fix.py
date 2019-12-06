# coding: utf-8

import pymysql
import traceback
import sys

db_opt = {
    'host': '127.0.0.1', 'user': 'root', 'passwd': 'test',
    'db': 'bonus',
}

if len(sys.argv) < 2:
    print "1: fix pic"
    print "2: fix bet_small"
    print "3: fix bet_double"
    print "4: fix round"
    sys.exit(1)

try:
    conn = pymysql.connect(**db_opt)
    conn.autocommit(True)
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    for fileline in open("checkout.txt"):
        l = fileline.strip().split()
        bet_timestamp = l[0].rstrip('.png')
        bet_small = l[1]
        cursor.execute(
            'UPDATE rounds SET bet_small=%s, state=1 WHERE bet_timestamp=%s',
            [bet_small, bet_timestamp]
        )

except Exception:
    print traceback.format_exc()

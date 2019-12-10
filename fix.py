# coding: utf-8

"""
从长截图中修复未处理数据
"""

import pymysql
import traceback
from PIL import Image
from utils import parse_image

db_opt = {
    'host': '127.0.0.1', 'user': 'root', 'passwd': 'test',
    'db': 'bonus',
}


date = 20191210
begin = 2128
end = 2152


try:
    conn = pymysql.connect(**db_opt)
    conn.autocommit(True)
    img = Image.open("raw.png")
    for i in range(begin, end + 1):
        # 时间超过59分，跳过
        if i % 100 >= 60:
            continue

        j = i - begin
        region = img.crop((0, j*696, 800, (j+1)*696))
        filename = "./images/{0}{1}.png".format(date, i)
        region.save(filename)
        img_tmp = Image.open(filename)
        region_tmp = img_tmp.crop((125, 140, 125+400, 140+210))
        img_name = "{0}_tmp.png".format(filename.rstrip('.png'))
        region_tmp.save(img_name)
        print "parse file {0}".format(filename)
        roundid, bet_map = parse_image(img_name, False)
        # 3. 错误处理
        state = 0
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
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute(
            ('INSERT INTO rounds(bet_timestamp, bet_single, bet_double, '
             'bet_big, bet_small, roundid, state) '
             'VALUES(%s,%s,%s,%s,%s,%s,%s)'
             ),
            ["{0}{1}".format(date, i),
             str(bet_map[roundid].get('bet_single', 0)),
             str(bet_map[roundid].get('bet_double', 0)),
             str(bet_map[roundid].get('bet_big', 0)),
             str(bet_map[roundid].get('bet_small', 0)),
             str(roundid),
             str(state)]
        )
        cursor.close()

except Exception:
    print traceback.format_exc()

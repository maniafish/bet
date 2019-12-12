# coding: utf-8

"""
从长截图中修复未处理数据
"""

import os
import pymysql
import traceback
from PIL import Image
from utils import parse_image

db_opt = {
    'host': '127.0.0.1', 'user': 'root', 'passwd': 'test',
    'db': 'bonus',
}


round_height = 696


def set_skip_height(skip, begin):
    """ 设置需要跳过的头部高度 """
    skip_height = 192
    for i in range(skip, begin):
        # 时间超过59分，跳过
        if i % 100 >= 60:
            continue

        skip_height += round_height

    return skip_height


def do_fix(bet_timestamp, conn):
    """ 处理图片执行fix记录 """
    # 1. 裁剪图片
    filename = "./images/{0}.png".format(bet_timestamp)
    img = Image.open(filename)
    region = img.crop((125, 140, 125+400, 140+210))
    img_name = "{0}_tmp.png".format(filename.rstrip('.png'))
    region.save(img_name)
    print "parse file {0}".format(filename)
    # 2. 处理图片
    roundid, bet_map = parse_image(img_name, False)
    # 3. 错误处理
    state = 2
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
        [bet_timestamp,
         str(bet_map[roundid].get('bet_single', 0)),
         str(bet_map[roundid].get('bet_double', 0)),
         str(bet_map[roundid].get('bet_big', 0)),
         str(bet_map[roundid].get('bet_small', 0)),
         str(roundid),
         str(state)]
    )
    cursor.close()


try:
    conn = pymysql.connect(**db_opt)
    conn.autocommit(True)
    for _, _, f_list in os.walk("./fix_images"):
        for filename in f_list:
            date, skip, begin, end = filename.rstrip('.png').split('-')
            skip = int(skip)
            begin = int(begin)
            end = int(end)
            skip_height = set_skip_height(skip, begin)
            img = Image.open("./fix_images/{0}".format(filename))
            _, total_height = img.size
            region = img.crop((0, skip_height, 800, total_height))
            fn = "./images/{0}".format(filename)
            region.save(fn)
            img = Image.open(fn)
            j = 0
            for i in range(begin, end + 1):
                # 时间超过59分，跳过
                if i % 100 >= 60:
                    continue

                region = img.crop((0, j*round_height, 800, (j+1)*round_height))
                bet_timestamp = "%s%04d" % (date, i)
                region.save("./images/{0}.png".format(bet_timestamp))
                do_fix(bet_timestamp, conn)
                j += 1

except Exception:
    print traceback.format_exc()

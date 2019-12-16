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


factor = 1
round_height = 696 * factor


def set_skip_height(skip, begin):
    """ 设置需要跳过的头部高度 """
    skip_height = 192 * factor
    for i in range(skip, begin):
        # 时间超过59分，跳过
        if i % 100 >= 60:
            continue

        skip_height += round_height

    return skip_height


def do_fix(bet_timestamp, conn):
    """ 处理图片执行fix记录 """
    # 1. 处理图片
    filename = "./images/{0}.png".format(bet_timestamp)
    print "parse file {0}".format(filename)
    roundid, bet_map = parse_image(filename, 2, factor)
    # 2. 错误处理
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

    # 3. 入库
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
            # 提高图片处理像素上限
            Image.MAX_IMAGE_PIXELS = 3 * Image.MAX_IMAGE_PIXELS
            img = Image.open("./fix_images/{0}".format(filename))
            _, total_height = img.size
            region = img.crop((0, skip_height, 800 * factor, total_height))
            fn = "./images/{0}".format(filename)
            region.save(fn)
            img = Image.open(fn)
            j = 0
            for i in range(begin, end + 1):
                # 时间超过59分，跳过
                if i % 100 >= 60:
                    continue

                region = img.crop((0, j*round_height, 800 * factor, (j+1)*round_height))
                bet_timestamp = "%s%04d" % (date, i)
                region.save("./images/{0}.png".format(bet_timestamp))
                do_fix(bet_timestamp, conn)
                j += 1

except Exception:
    print traceback.format_exc()

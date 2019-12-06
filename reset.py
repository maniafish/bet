# coding: utf-8

"""
重新识别数据库中状态为-1的轮次
"""

from PIL import Image
import pytesseract
import pymysql
import traceback


db_opt = {
    'host': '127.0.0.1', 'user': 'root', 'passwd': 'test',
    'db': 'bonus',
}


def set_multi(line):
    """ 解析行中的轮次和倍率 """
    print line
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


try:
    conn = pymysql.connect(**db_opt)
    conn.autocommit(True)
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute('SELECT bet_timestamp FROM rounds WHERE state = -1')
    ret = cursor.fetchall()
    cursor.close()
    for r in ret:
        filename = './images/{0}.png'.format(r['bet_timestamp'])
        print "parse file: {0}".format(filename)
        img = Image.open(filename)
        wide, height = img.size
        w_factor = wide / 800.0
        h_factor = height / 600.0
        # 图像截取
        img_x = 56 * w_factor
        img_y = 180 * h_factor
        img_w = 200 * w_factor
        img_h = 120 * h_factor
        region = img.crop((img_x, img_y, img_x+img_w, img_y+img_h))
        img_name = './images/{0}_tmp.png'.format(r['bet_timestamp'])
        region.save(img_name)
        out = pytesseract.image_to_string(Image.open(img_name), lang='chi_sim')
        bet_map = {}
        roundid = -1
        # 永远以最近的一条为准
        for line in out.split('\n'):
            bet_type = ''
            bet = 0
            if line.find(u'期') > 0:
                if line.find(u'双') > 0:
                    roundid, bet = set_multi(line)
                    bet_type = 'double'
                elif line.find(u'单') > 0:
                    roundid, bet = set_multi(line)
                    bet_type = 'single'
                elif line.find(u'大') > 0:
                    roundid, bet = set_multi(line)
                    bet_type = 'big'
                elif line.find(u'小') > 0 or line.find('JJ') > 0:
                    roundid, bet = set_multi(line)
                    bet_type = 'small'

                # 没有就创建
                if not bet_map.get(roundid):
                    bet_map[roundid] = {bet_type: bet}
                else:
                    bet_map[roundid][bet_type] = bet

        if roundid == -1:
            # 完全没解出来的，就不用挣扎了
            print "invalid file: {0}".format(img_name)
            continue

        # 当bet_a和bet_b有且仅有一个>0，另一个为0时，记录有效
        # 单双没解出来的，递归预测出一个结果来
        if not ((bet_map[roundid].get('single', 0) > 0 and bet_map[roundid].get('double', 0) == 0) or (bet_map[roundid].get('double', 0) > 0 and bet_map[roundid].get('single', 0) == 0)):

        # 大小没解出来的，递归预测出一个结果来
        if not ((bet_map[roundid].get('small', 0) > 0 and bet_map[roundid].get('big', 0) == 0) or (bet_map[roundid].get('big', 0) > 0 and bet_map[roundid].get('small', 0) == 0)):

        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute(
            ('UPDATE rounds SET bet_single = %s, bet_double = %s, '
             'bet_big = %s, bet_small = %s, roundid = %s, state = 1 '
             'WHERE bet_timestamp = %s'),
            [str(bet_map[roundid].get('single', 0)),
             str(bet_map[roundid].get('double', 0)),
             str(bet_map[roundid].get('big', 0)),
             str(bet_map[roundid].get('small', 0)),
             str(roundid),
             str(r['bet_timestamp'])]
        )
        cursor.close()

except Exception:
    print traceback.format_exc()

# coding: utf-8

from PIL import Image
import pytesseract
import traceback


def set_multi(line):
    """ 解析行中的轮次和倍率 """
    s = line.split()
    try:
        roundid = int(s[0])
    except Exception:
        print traceback.format_exc()
        # 没解出来的，roundid = 0
        roundid = 0

    try:
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


def parse_image(filename):
    """ 图像解析 """
    try:
        img = Image.open(filename)
        wide, height = img.size
        w_factor = wide / 800.0
        h_factor = height / 600.0
        # 图像截取
        img_x = 56 * w_factor
        img_y = 180 * h_factor
        img_w = 180 * w_factor
        img_h = 120 * h_factor
        region = img.crop((img_x, img_y, img_x+img_w, img_y+img_h))
        img_name = "{0}_tmp.png".format(filename.rstrip('.png'))
        region.save(img_name)
        out = pytesseract.image_to_string(Image.open(img_name), lang='chi_sim')
        bet_map = {}
        roundid = -1
        tmp_roundid = -1
        bet_type = ''
        bet = 0
        for line in out.split('\n'):
            if line.find(u'期') > 0:
                print line
                if line.find(u'双') > 0 or line.find('XX') > 0 or line.find('X') > 0:
                    tmp_roundid, bet = set_multi(line)
                    bet_type = 'bet_double'
                elif line.find(u'单') > 0:
                    tmp_roundid, bet = set_multi(line)
                    bet_type = 'bet_single'
                elif line.find(u'大') > 0:
                    tmp_roundid, bet = set_multi(line)
                    bet_type = 'bet_big'
                elif line.find(u'小') > 0 or line.find('JJ') > 0 or line.find('J') > 0:
                    tmp_roundid, bet = set_multi(line)
                    bet_type = 'bet_small'

                # 读到有效数据
                if tmp_roundid != -1:
                    # 原来没有就创建
                    if roundid == -1:
                        roundid = tmp_roundid
                        bet_map[roundid] = {bet_type: bet}
                    else:
                        # 延用原roundid
                        bet_map[roundid][bet_type] = bet

        return roundid, bet_map

    except Exception:
        print traceback.format_exc()
        return -1, {}

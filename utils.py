# coding: utf-8

from PIL import Image
import pytesseract
import traceback
import re


def set_multi(line):
    """ 解析行中的轮次和倍率 """
    try:
        s = re.findall(r"\d+", line)
        if len(s) < 1:
            return 0, 0
        elif len(s) == 1:
            # 只有轮次
            return int(s[0]), 0
        else:
            # 第一个是轮次，最后一个是倍率
            return int(s[0]), int(s[len(s)-1])
    except Exception:
        print traceback.format_exc()
        return 0, 0


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
                else:
                    tmp_roundid, bet = set_multi(line)
                    # 解不出类型的就是【小】和【双】
                    bet_type = 'bet_unkown'

                # 读到有效数据
                if tmp_roundid != -1:
                    # 原来没有就创建
                    if roundid == -1:
                        roundid = tmp_roundid
                        bet_map[roundid] = {bet_type: bet}
                    else:
                        # 延用原roundid
                        bet_map[roundid][bet_type] = bet

        # 给unkown赋值
        if roundid != -1 and bet_map[roundid].get('bet_unkown'):
            if bet_map[roundid].get('bet_big') is not None or bet_map[roundid].get('bet_small') is not None:
                # 有大小了，赋值双
                bet_map[roundid]['bet_double'] = bet_map[roundid]['bet_unkown']
            elif bet_map[roundid].get('bet_single') is not None or bet_map[roundid].get('bet_double') is not None:
                # 有单双了，赋值小
                bet_map[roundid]['bet_small'] = bet_map[roundid]['bet_unkown']

        return roundid, bet_map

    except Exception:
        print traceback.format_exc()
        return -1, {}

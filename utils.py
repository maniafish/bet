# coding: utf-8

from PIL import Image
import pytesseract
import traceback
import re
import os


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


def parse_image(filename, cut_type=1):
    """ 图像解析 """
    try:
        img = Image.open(filename)
        img_name = "{0}_tmp.png".format(filename.rstrip('.png'))
        if cut_type == 1:
            wide, height = img.size
            w_factor = wide / 800.0
            h_factor = height / 600.0
            # 图像截取
            img_x = 56 * w_factor
            img_y = 180 * h_factor
            img_w = 180 * w_factor
            img_h = 120 * h_factor
            region = img.crop((img_x, img_y, img_x+img_w, img_y+img_h))
            region.save(img_name)
        elif cut_type == 2:
            region = img.crop((125, 140, 125+400, 140+210))
            region.save(img_name)
        else:
            print "invalid cut_type: {0}".format(cut_type)
            return -1, {}

        # 分上下两半，上为大小，下为单双
        tmp = Image.open(img_name)
        wide, height = tmp.size
        region1 = tmp.crop((0, 0, wide, height / 2.0))
        tmp1 = "{0}1.png".format(img_name.rstrip('.png'))
        region1.save(tmp1)
        region2 = tmp.crop((0, height / 2.0, wide, height))
        tmp2 = "{0}2.png".format(img_name.rstrip('.png'))
        region2.save(tmp2)

        bet_map = {}
        roundid = -1

        # 解析大小
        out = pytesseract.image_to_string(Image.open(tmp1), lang='chi_sim')
        for line in out.split('\n'):
            if line.find(u'期') > 0 or line.find(u'服') > 0:
                print line
                if line.find(u'大') > 0:
                    roundid, bet = set_multi(line)
                    bet_type = 'bet_big'
                elif line.find(u'小') > 0 or line.find('JJ') > 0 or line.find('J') > 0:
                    roundid, bet = set_multi(line)
                    bet_type = 'bet_small'
                else:
                    roundid, bet = set_multi(line)
                    # 解不出类型的就是【小】
                    bet_type = 'bet_small'

                # 修复无效bet
                if bet == 89:
                    bet = 9
                # 创建roundid
                bet_map[roundid] = {bet_type: bet}
                break

        # 解析单双
        out = pytesseract.image_to_string(Image.open(tmp2), lang='chi_sim')
        for line in out.split('\n'):
            if line.find(u'期') > 0 or line.find(u'服') > 0:
                print line
                if line.find(u'双') > 0 or line.find('XX') > 0 or line.find('X') > 0:
                    tmp_roundid, bet = set_multi(line)
                    bet_type = 'bet_double'
                elif line.find(u'单') > 0:
                    tmp_roundid, bet = set_multi(line)
                    bet_type = 'bet_single'
                else:
                    tmp_roundid, bet = set_multi(line)
                    # 解不出类型的就是【双】
                    bet_type = 'bet_double'

                # 修复无效bet
                if bet == 89:
                    bet = 9
                if roundid == -1:
                    # 没有就创建
                    bet_map[tmp_roundid] = {bet_type: bet}
                elif roundid == 0:
                    # 前一个roundid无效，将无效的赋值到有效的roundid
                    bet_map[tmp_roundid] = bet_map[0]
                    bet_map[tmp_roundid][bet_type] = bet
                else:
                    # 上一个roundid有效，延用上一个roundid
                    bet_map[roundid][bet_type] = bet

                roundid = tmp_roundid
                break

        os.remove(img_name)
        os.remove(tmp1)
        os.remove(tmp2)
        return roundid, bet_map

    except Exception:
        print traceback.format_exc()
        return -1, {}

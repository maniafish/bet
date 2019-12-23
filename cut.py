# coding: utf-8

"""
处理长截图
"""

import traceback
from PIL import Image

factor = 1
round_height = 696 * factor
filename = '20191219-1749-1801-1810.png'


def set_skip_height(skip, begin):
    """ 设置需要跳过的头部高度 """
    skip_height = 192 * factor
    for i in range(skip, begin):
        # 时间超过59分，跳过
        if i % 100 >= 60:
            continue

        skip_height += round_height

    return skip_height


try:
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
    region.save(filename)

except Exception:
    print traceback.format_exc()

# coding: utf-8

""" 策略 """

import math

bet_list = [1, 3, 9, 27]


def cal_bet(bet_index):
    if bet_index <= 3:
        return bet_list[bet_index]
    else:
        return bet_list[3] * math.pow(2, bet_index-3)


class BaseStg(object):
    """ 统计基类 """
    def __init__(self, principal, bet_factor):
        self.principal = principal
        self.bet_factor = bet_factor

    def get_name(self):
        return self.name


class BetSmall(BaseStg):
    def __init__(self, principal, bet_factor):
        super(BetSmall, self).__init__(principal, bet_factor)
        self.name = 'small'

    """ 小倍率下注 """
    def do_bet(self, r):
        # 本金矩阵
        d = {}
        # 下注索引
        bet_index = 0
        # 下注金额
        current_bet = 0
        # 当前下注类型, 1: 大小, 2: 单双
        bet_type = 0
        for i, v in enumerate(r):
            d[v['bet_timestamp']] = self.principal
            # 判断上轮下注是否成功
            if (bet_type == 1 and v['bet_big'] + v['bet_small'] == 1) or (
                    bet_type == 2 and v['bet_single'] + v['bet_double'] == 1):
                self.principal += current_bet * 1.96
                bet_index = 0
                current_bet = 0
                continue

            # 选择倍率小的下注
            if v['bet_big'] + v['bet_small'] < v['bet_single'] + v['bet_double']:
                bet_type = 1
            else:
                bet_type = 2

            current_bet = cal_bet(bet_index)
            self.principal -= current_bet
            bet_index += 1

        return d

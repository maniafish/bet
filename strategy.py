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
        # TODO: 达到max_index后如何判断是否中
        self.max_index = 10

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

            if bet_index >= self.max_index:
                bet_index = 0
            current_bet = self.bet_factor * cal_bet(bet_index)
            self.principal -= current_bet
            bet_index += 1

        return d


class BetNormal(BaseStg):
    def __init__(self, principal, bet_factor):
        super(BetNormal, self).__init__(principal, bet_factor)
        self.name = 'normal'
        self.max_index = 10

    """ 常规下注 """
    def do_bet(self, r):
        # 本金矩阵
        d = {}
        # 下注索引
        bet_index_1 = 0
        bet_index_2 = 0
        # 下注金额
        current_bet_1 = 0
        current_bet_2 = 0
        # 当前下注类型, 1: 大小, 2: 单双
        for i, v in enumerate(r):
            print v['bet_timestamp'], self.principal, bet_index_1, current_bet_1, bet_index_2, current_bet_2
            d[v['bet_timestamp']] = self.principal
            # 判断上轮下注是否成功
            if v['bet_big'] + v['bet_small'] == 1:
                self.principal += current_bet_1 * 1.96
                bet_index_1 = -1

            # 超过最大下注
            bet_index_1 += 1
            if bet_index_1 >= self.max_index:
                bet_index_1 = 0

            current_bet_1 = self.bet_factor * cal_bet(bet_index_1)
            self.principal -= current_bet_1

            if v['bet_single'] + v['bet_double'] == 1:
                self.principal += current_bet_2 * 1.96
                bet_index_2 = -1

            # 超过最大下注
            bet_index_2 += 1
            if bet_index_2 >= self.max_index:
                bet_index_2 = 0
            current_bet_2 = self.bet_factor * cal_bet(bet_index_2)
            self.principal -= current_bet_2

        return d


class BetN(BaseStg):
    def __init__(self, principal, bet_factor, n):
        super(BetN, self).__init__(principal, bet_factor)
        self.name = 'no1'
        self.max_index = 11
        self.n = n

    """ 仅在n下注 """
    def do_bet(self, r):
        # 本金矩阵
        d = {}
        # 下注索引
        bet_index_1 = 0
        bet_index_2 = 0
        # 下注金额
        current_bet_1 = 0
        current_bet_2 = 0
        # 非下注区间
        cool_down = False
        # 当前下注类型, 1: 大小, 2: 单双
        for i, v in enumerate(r):
            tm = v['bet_timestamp'] % 10000
            print v['bet_timestamp'], self.principal, bet_index_1, current_bet_1, bet_index_2, current_bet_2
            d[v['bet_timestamp']] = self.principal
            if cool_down:
                if tm < 1500 or tm > 1900:
                    cool_down = False
            else:
                # 判断上轮下注是否成功
                if v['bet_big'] + v['bet_small'] == 1 and (
                        i > 1 and r[i-1]['bet_big'] + r[i-1]['bet_small'] == self.n):
                    self.principal += current_bet_1 * 1.96
                    bet_index_1 = 0
                    current_bet_1 = 0

                if v['bet_single'] + v['bet_double'] == 1 and (
                        i > 1 and r[i-1]['bet_single'] + r[i-1]['bet_double'] == self.n):
                    self.principal += current_bet_2 * 1.96
                    bet_index_2 = 0
                    current_bet_2 = 0

                # 设置不下注区间
                if tm >= 1500 and tm <= 1900:
                    # 下注索引
                    bet_index_1 = 0
                    bet_index_2 = 0
                    # 下注金额
                    current_bet_1 = 0
                    current_bet_2 = 0
                    # 非下注区间
                    cool_down = True
                    continue

                if v['bet_big'] + v['bet_small'] == self.n:
                    # 超过最大下注
                    if bet_index_1 >= self.max_index:
                        bet_index_1 = 0

                    current_bet_1 = self.bet_factor * cal_bet(bet_index_1)
                    self.principal -= current_bet_1
                    bet_index_1 += 1

                if v['bet_single'] + v['bet_double'] == self.n:
                    # 超过最大下注
                    if bet_index_2 >= self.max_index:
                        bet_index_2 = 0

                    current_bet_2 = self.bet_factor * cal_bet(bet_index_2)
                    self.principal -= current_bet_2
                    bet_index_2 += 1

        return d

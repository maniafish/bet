from strategy import cal_bet

s = 0
for i in range(0, 15):
    bet = cal_bet(i)
    s += bet
    print("{0}: bet {1}, sum {2}, bonus {3}".format(
        i, bet, s, bet * 1.96 - s))

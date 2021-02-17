
import backtrader as bt
import numpy as np
from scipy import stats

class Momentum(bt.Indicator):
    lines = ('tendency',)
    params = dict(period=90)

    def __init__(self):
        self.addminperiod(self.params.period)

    def next(self):
        prices = self.data.get(size=self.params.period)
        # since we are catching the trend, so log return is good enough.
        logReturn = np.log(prices)
        index = np.arange(len(logReturn))
        # Do linear regression on the logReturn for 90 days period to find daily log return ratio
        res = stats.linregress(index,logReturn)
        annualized = (1 + res.slope) ** 252
        # store the momentum
        self.lines.tendency[0] = annualized * (res.rvalue ** 2)

class CrossSectionalMR(bt.Strategy):
    def prenext(self):
        self.next()
    
    def next(self):
        # only look at data that existed yesterday
        available = list(filter(lambda d: len(d), self.datas)) 
        
        rets = np.zeros(len(available))
        for i, d in enumerate(available):
            # calculate individual daily returns
            rets[i] = (d.close[0]- d.close[-1]) / d.close[-1]

        # calculate weights using formula
        market_ret = np.mean(rets)
        weights = -(rets - market_ret)
        weights = weights / np.sum(np.abs(weights))
        
        for i, d in enumerate(available):
            self.order_target_percent(d, target=weights[i])
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import datetime  # For datetime objects
import os.path  # To manage paths
import sys  # To find out the script name (in argv[0])
import numpy as np

import backtrader as bt

# Create a Stratey
# class Strategy(bt.Strategy):
#     def __init__(self):
#         self.i = 0
#         self.inds = {}
#         self.spy = self.datas[0]
#         self.stocks = self.datas[1:]
        
#         self.spy_sma200 = bt.indicators.SimpleMovingAverage(self.spy.close,
#                                                             period=200)
#         for d in self.stocks:
#             self.inds[d] = {}
#             self.inds[d]["momentum"] = Momentum(d.close, period=90)
#             self.inds[d]["sma100"] = bt.indicators.SimpleMovingAverage(d.close, period=100)
#             self.inds[d]["atr20"] = bt.indicators.ATR(d, period=20)

#     def prenext(self):
#         # call next() even when data is not available for all tickers
#         self.next()
    
#     def next(self):
#         if self.i % 5 == 0:
#             self.rebalance_portfolio()
#         if self.i % 10 == 0:
#             self.rebalance_positions()
#         self.i += 1
    
#     def rebalance_portfolio(self):
#         # only look at data that we can have indicators for 
#         self.rankings = list(filter(lambda d: len(d) > 100, self.stocks))
#         self.rankings.sort(key=lambda d: self.inds[d]["momentum"][0])
#         num_stocks = len(self.rankings)
        
#         # sell stocks based on criteria
#         for i, d in enumerate(self.rankings):
#             if self.getposition(self.data).size:
#                 if i > num_stocks * 0.2 or d < self.inds[d]["sma100"]:
#                     self.close(d)
        
#         if self.spy < self.spy_sma200:
#             return
        
#         # buy stocks with remaining cash
#         for i, d in enumerate(self.rankings[:int(num_stocks * 0.2)]):
#             cash = self.broker.get_cash()
#             value = self.broker.get_value()
#             if cash <= 0:
#                 break
#             if not self.getposition(self.data).size:
#                 size = value * 0.001 / self.inds[d]["atr20"]
#                 self.buy(d, size=size)
                
        
#     def rebalance_positions(self):
#         num_stocks = len(self.rankings)
        
#         if self.spy < self.spy_sma200:
#             return

#         # rebalance all stocks
#         for i, d in enumerate(self.rankings[:int(num_stocks * 0.2)]):
#             cash = self.broker.get_cash()
#             value = self.broker.get_value()
#             if cash <= 0:
#                 break
#             size = value * 0.001 / self.inds[d]["atr20"]
#             self.order_target_size(d, size)
            
            
            
            
class TestStrategy(bt.Strategy):
    params = (
        ('exitbars', 5),
    )

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
#         print(self.datas[0])
        self.dataclose = self.datas[0].close
        self.dataopen = self.datas[0].open
        self.datahigh = self.datas[0].high
        self.datalow = self.datas[0].low
        self.volume = self.datas[0].volume
        
#         print(self.dataclose[0], self.dataopen[0], self.datahigh[0], self.volume[0], '=====')
        
        self.order = None
        self.buyprice = None
        self.buycomm = None
        self.bar_executed = 0
#         self.sma = bt.indicators.SimpleMovingAverage(self.data)

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))

    def next(self):
        # Simply log the closing price of the series from the reference
        self.log('Close, %.2f' % self.dataclose[0])

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        # Check if we are in the market
        if not self.position:

            # Not yet ... we MIGHT BUY if ...
            if self.dataclose[0] < self.dataclose[-1]:
                    # current close less than previous close

                    if self.dataclose[-1] < self.dataclose[-2]:
                        # previous close less than the previous close

                        # BUY, BUY, BUY!!! (with default parameters)
                        self.log('BUY CREATE, %.2f' % self.dataclose[0])

                        # Keep track of the created order to avoid a 2nd order
                        self.order = self.buy()

        else:
            # Already in the market ... we might sell
            if len(self) >= (self.bar_executed + self.params.exitbars):
                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log('SELL CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.order = self.sell()
                
class CrossSectionalMR(bt.Strategy):
    def __init__(self, models_params = None):
        self.models_params = models_params
        
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
            # trigger order purchase
            self.order_target_percent(d, target=weights[i])
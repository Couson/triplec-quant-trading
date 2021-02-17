import os
import sys
from getopt import getopt

import pandas as pd
import json

import backtrader as bt
import datetime

import sys
if 'src' not in sys.path:
    sys.path.insert(0, 'src')
    
from strategy import *

LOG_PATH = 'logs/sys_log.txt'
DATA_PATH = 'config/data-params.json'
STRATEGY_PATH = 'config/strategy-params.json'

ACCOUNT_PATH = 'config/account-params.json'

def load_params(fp):
    with open(fp) as fh:
        param = json.load(fh)
    return param
            
        
def display_menu():
    print('writing something !')
    ### TODO

def write_sys_log(msg):
    ## put this func in utils.py
    now = datetime.datetime.now()
    
    with open(LOG_PATH, 'a') as log:
        to_write = str(now) + ' %s' %msg + '\n'
        log.write(to_write)
    
def create_account(params):
    acc = bt.Cerebro(cheat_on_open = params['cheat_on_open'])
    acc.broker.setcash(params['initial_cash'])
    acc.broker.setcommission(params['commission'])
    
    msg = '--> Successfully Created Account with %s$' % params['initial_cash']
    print(msg)
    write_sys_log(msg)
    
    return acc

def ingest_data(params, acc):
    
    end = datetime.datetime.strptime(params['end'], '%Y-%m-%d') 
    start = datetime.datetime.strptime(params['start'], '%Y-%m-%d')
    data_dir = params['data_dir']
    price_column = params['price_column']
    date_column = params['date_column']
    fp = params['data_dir']
    
    # may need a mechanism to check if the selected time span have valid data
    ### TODO
    tickers = pd.read_csv(os.path.join(data_dir, "tickers.csv"), header=None, index_col = 0)[1].tolist()
    
    stocks = pd.concat(
            [pd.read_csv(os.path.join(data_dir, f"{ticker}.csv"), index_col = date_column, \
                         parse_dates=True)[price_column].rename(ticker) for ticker in tickers], \
            axis=1, \
            sort=True)
    
    # create ckpts to save time
    stocks = stocks.loc[:,~stocks.columns.duplicated()]
    
    for ticker in tickers:
        data = bt.feeds.GenericCSVData(
            fromdate = start,
            todate = end,
            dataname = os.path.join(data_dir, f"{ticker}.csv"),
            dtformat = ('%Y-%m-%d'),
            openinterest = -1,
            nullvalue = 0.0,
            plot = False,
            adjclose = False
        )
        acc.adddata(data)
        
    msg = '--> Successfully Ingested Data'
    print(msg)
    write_sys_log(msg)
    return acc
    
def invest(params, acc):
    ###### TODO 把下面的分开
#     params
    acc.addstrategy(CrossSectionalMR)
#     acc.addsizer(bt.sizers.PercentSizer, percents = 50) ##### cheat-on-open
    acc.addobserver(bt.observers.Value)
    
    msg = '--> Investing ...'
    print(msg)
    write_sys_log(msg)
    
    acc.run()
    
    msg = '--> End with %s$' % acc.broker.getvalue()
    print(msg)
    write_sys_log(msg)
    
    return acc
    


def main(argv):
    account_params = load_params(ACCOUNT_PATH)
    data_params = load_params(DATA_PATH)
    strategy_params = load_params(STRATEGY_PATH)
    
        
    
    try:
        opts, args = getopt(argv, "hrm:", ["help", "run", "model="])
    except getopt.GetoptError:
        display_menu()
        sys.exit()

    for opt, arg in opts:
        if opt == '-h':
            display_menu()
            sys.exit()
        elif opt in ('-r', '--run'):
            cerebro = create_account(account_params)
            cerebro = ingest_data(data_params, cerebro)
            _ = invest(strategy_params, cerebro)
            
    

if __name__== "__main__": 
    comm = sys.argv[1:]
    main(comm)
    
    
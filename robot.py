from collections import OrderedDict,defaultdict
import pandas as pd
import numpy as np
from config import cfg
from logger import log,hist
from framework import fwk
from market import mkt
from tanalyse import Bbands, Macd, Stoch
from signalslot import sslot
from utils import *

import time

class Robot():
    def __init__(self):
        self.simulate = True

        if cfg.is_future():
            self.orig_user_info = {
                cfg.get_coin1():{
                    'balance':0            #账户余额(可用保证金)
                    'contracts':[{
                        'available':0      #合约可用(可用保证金)
                        'balance':0        #账户(合约)余额
                        'bond':0           #固定保证金(已用保证金)
                        'contract_id':0    #合约ID
                        'contract_type':0   #合约类别
                        'freeze':0          #冻结保证金
                        'profit':0          #已实现盈亏
                        'unprofit':0        #未实现盈亏
                    }]
                    'rights':0              #账户权益
                }
            }
            self.orig_future_position = {
                'buy_amount':0                #多仓数量
                'buy_available':0            #多仓可平仓数量 
                'buy_bond':0                 #多仓保证金
                'buy_flatprice':0            #多仓强平价格
                'buy_profit_lossratio':0     #多仓盈亏比
                'buy_price_avg':0            #开仓平均价
                'buy_price_cost':0           #结算基准价
                'buy_profit_real':0          #多仓已实现盈余
                'contract_id':0              #合约id
                'contract_type':0            #合约类型
                'create_date':0              #创建日期
                'sell_amount':0              #空仓数量
                'sell_available':0           #空仓可平仓数量 
                'sell_bond':0                #空仓保证金
                'sell_flatprice':0           #空仓强平价格
                'sell_profit_lossratio':0    #空仓盈亏比
                'sell_price_avg':0           #开仓平均价
                'sell_price_cost':0          #结算基准价
                'sell_profit_real':0         #空仓已实现盈余
                'symbol':cfg.get_pair()      #btc_usd   ltc_usd    eth_usd    etc_usd    bch_usd
                'lever_rate':0               #杠杆倍数
            }
            
        #variables for mine
        self.coin1_fee=0.0
        self.coin2_fee=0.0
        self.order_id = []
        self.deficit_allowed = cfg.get_fee() * cfg.get_trans_fee() 
        self.exchange = 0
        
        #variables for trade record
        self.update_variables()
        self.trade_type = {'open_buy':1, 'open_sell':2, 'loss_buy':3, 'loss_sell':4, 'margin_buy':3,'margin_sell':4}


        #variables for technical indicator
        self.bbands = Bbands()
        self.macd = Macd()
        self.stoch = Stoch()

        #variables for log print
        self.n_depth_handle = 0

        #variables for automatic running
        self.running = 0

        #variables for test back
        self.testing = False

    def update_variables(self, *trade_param):
        if len(trade_param) == 0: ###init
            self.n_depth_handle = 0
            self.price_history = pd.DataFrame(columns=['t','p'])
            self.trade_history = pd.DataFrame(columns=['t','type', 'price', 'amount', 'match_price'])
        else:
            if self.trade_history.index.size > 100:
                self.trade_history = self.trade_history.drop(0)
            else:
                self.trade_history.loc[self.trade_history.index.size] = trade_param[0]

        if self.simulate:
            if len(trade_param) == 0: ###init
                if cfg.is_future():
                    self.user_info = self.orig_user_info
                    self.future_position = self.orig_future_position
            else: ##update
                param = self.trade_history.iloc[-1]
                if param['type'] == 'open_buy':
                    if cfg.is_future():
                        a = param['amount'] * (1-0.001) ##take off trans fee
                        oldfund = self.future_position['buy_amount'] * self.future_position['buy_price_avg']
                        newfund = a * param['price']
                        self.future_position['buy_amount'] += a
                        self.future_position['buy_available'] += a
                        self.future_position['buy_price_avg'] = (oldfund + newfund) / self.future_position['buy_amount']
                        self.future_position['buy_bond'] += a/cfg.get_future_buy_lever()

                        self.user_info[self.get_coin1()]['contracts']['available'] -= param['amount']/cfg.get_future_buy_lever()
                        self.user_info[self.get_coin1()]['contracts']['bond'] += a/cfg.get_future_buy_lever()

                if param['type'] == 'margin_buy':
                    if cfg.is_future():
                        self.future_position['buy_amount'] -= param['amount']
                        self.future_position['buy_available'] -= param['amount']
                        self.future_position['buy_bond'] -= param['amount']/cfg.get_future_buy_lever()

                        self.user_info[self.get_coin1()]['contracts']['available'] += param['amount']/cfg.get_future_buy_lever()
                        self.user_info[self.get_coin1()]['contracts']['bond'] -= param['amount']/cfg.get_future_buy_lever()
                        profit = (param['price'] - self.future_position['buy_price_avg']) * param['amount']
                        self.user_info[self.get_coin1()]['contracts']['profit'] += profit

                if param['type'] == 'open_sell':
                    if cfg.is_future():
                        oldfund = self.future_position['sell_amount'] * self.future_position['sell_price_avg']
                        newfund = param['amount'] * param['price']
                        self.future_position['sell_amount'] += param['amount']
                        self.future_position['sell_available'] += param['amount']
                        self.future_position['sell_price_avg'] = (oldfund + newfund) / self.future_position['sell_amount']
                        self.future_position['sell_bond'] += param['amount']/cfg.get_future_buy_lever()

                        self.user_info[self.get_coin1()]['contracts']['available'] -= param['amount']/cfg.get_future_buy_lever()
                        self.user_info[self.get_coin1()]['contracts']['bond'] += param['amount']/cfg.get_future_buy_lever()

                if param['type'] == 'margin_sell':
                    if cfg.is_future():
                        self.future_position['sell_amount'] -= param['amount']
                        self.future_position['sell_available'] -= param['amount']
                        self.future_position['sell_bond'] -= param['amount']/cfg.get_future_buy_lever()

                        self.user_info[self.get_coin1()]['contracts']['available'] += param['amount']/cfg.get_future_buy_lever()
                        self.user_info[self.get_coin1()]['contracts']['bond'] -= param['amount']/cfg.get_future_buy_lever()
                        profit = (param['price'] - self.future_position['buy_price_avg']) * param['amount']
                        self.user_info[self.get_coin1()]['contracts']['profit'] += profit
        else:
            ##init or update directly
            if cfg.get_cfg_plat() == '': #reserve
                pass
            else:
                if cfg.is_future():
                    self.user_info = fwk.get_user_info()
                    self.future_position = fwk.get_future_position(cfg.get_pair())
                else:
                    pass

    def _trade(self,timestamp, type_key, price, amount, match_price=0):
        ttype = self.trade_type[type_key]
        if self.simulate:
            ret = True
        else:
            ret = fwk.trade(cfg.get_pair(), ttype, price, amount, match_price)
        if ret == True:
            ##record the trade history
            trade_param = [timestamp, type_key, price, amount, match_price]
            hist.info("%s"%trade_param)
            sslot.trade_log(trade_param)
            self.update_variables(trade_param)
        
    def trade(self, timestamp, signal, bp, ba, sp, sa):
        price = amount = 0
        if signal == 'buy':
            if cfg.get_cfg_plat() == 'okex':
                if cfg.is_future():
                    if self.future_position['sell_available'] > 0:
                        #orders = fwk.list_orders(cfg.get_pair(), -1, 1) #
                        #if len(orders) > 0:
                        #    for o in orders:
                        #        if o['type'] == self.trade_type['margin_sell']:
                        type_key = 'margin_sell'
                        price = sp
                        amount = min(sa, self.future_position['sell_available'])
                    else:
                        contracts = self.user_info[self.get_coin1()]['contracts']
                        a = contracts['available'] - (contracts['available'] + contracts['bond']) * 0.9
                        if a > 0:
                            price = sp
                            amount = min(sa, a * cfg.get_future_buy_lever())
                            type_key = 'open_buy'
                else:
                    pass
            elif cfg.get_cfg_plat() == 'coinex':
                pass

        elif signal == 'sell':
            if cfg.get_cfg_plat() == 'okex':
                if cfg.is_future():
                    if self.future_position['buy_available'] > 0:
                        #orders = fwk.list_orders(cfg.get_pair(), -1, 1) #
                        #if len(orders) > 0:
                        #    for o in orders:
                        #        if o['type'] == self.trade_type['margin_sell']:
                        type_key = 'margin_buy'
                        price = bp
                        amount = min(ba, self.future_position['buy_available'])
                    else:
                        contracts = self.user_info[self.get_coin1()]['contracts']
                        a = contracts['available'] - (contracts['available'] + contracts['bond']) * 0.9
                        if a > 0:
                            price = bp
                            amount = min(ba, a * cfg.get_future_sell_lever())
                            type_key = 'open_sell'
                else: ###spot have no sell type
                    pass
            elif cfg.get_cfg_plat() == 'coinex':
                pass
        else: ## standby
            pass

        if price > 0 and amount > 0:
            log.info("going to trade! type:%s price:%f, amount:%f"%(type_key, price, amount))
            self._trade(timestamp, type_key, price, amount) 

    def handle_depth(self, timestamp, depth):
        bp = depth['buy'][0][0]  #price buy
        ba = depth['buy'][0][1]  #amount buy
        sp = depth['sell'][0][0] #price sell
        sa = depth['sell'][0][1] #amount sell
        self.n_depth_handle += 1
        if self.n_depth_handle%60 == 0:
            ##logs
            if cfg.is_future():
                log.dbg("user_info:%s future_position:%s"%(self.user_info, self.future_position))
                sslot.robot_log("user_info:%s future_position:%s"%(self.user_info, self.future_position))
            else:
                log.dbg("user_info:%s"%(self.user_info))
                sslot.robot_log("user_info:%s"%(self.user_info))

        gap = gaps(bp, sp)
        if gap > 0.2:
            log.dbg("gap=%f low volume, don't operate!"%(gap))
            sslot.robot_log("gap=%f low volume, don't operate!"%(gap))
            return

        indicator = cfg.get_indicator()
        if indicator == 'bbands':
            self.bbands.ta_signal(timestamp, (bp+sp)/2)
            signal = self.stoch.sig
        elif indicator == 'macd':
            self.macd.ta_signal(timestamp, (bp+sp)/2)
            signal = self.macd.sig
        elif indicator == 'stoch':
            self.stoch.ta_signal(timestamp, (bp+sp)/2)
            signal = self.stoch.sig
        else:
            signal = 'standby'
        #log.dbg("get signal! %s"%signal)
        self.trade(timestamp, signal, bp, ba, sp, sa, 0)

    def start(self):
        if self.running == 0:
            log.dbg("robot starting...")
            self.running = 1
            self.update_variables()
            self.bbands.start()
            self.macd.start()
            self.stoch.start()
            mkt.register_handle('depth', self.handle_depth)
        else:
            log.dbg("robot already running!")

    def stop(self):
        if self.running == 1:
            log.dbg("robot stopping...")
            mkt.unregister_handle('depth', self.handle_depth)
            self.bbands.stop()
            self.macd.stop()
            self.stoch.stop()
            self.running = 0


    def testback(self):
        self.testing = True
        days = 10
        kl_1hour = fwk.get_kline(cfg.get_pair(), dtype="1hour", limit=min(days*24, 2000))
        if kl_1hour.size > 0:
            self.bbands.handle_data(kl_1hour)
            self.macd.handle_data(kl_1hour)
            self.stoch.handle_data(kl_1hour)
            
        #kl_1min = fwk.get_kline(cfg.get_pair(), dtype="1min", limit=min(days*24*60, 2000))
        #if(kl_1min.size <= 0):
        #    return
        #p = kl_1min['c']
        #t = kl_1min['t']
        p = kl_1hour['c']
        t = kl_1hour['t']
        for i in range(t.size):
            dummy_depth = {'buy':[[p[i]*0.999, 1000]],'sell':[[p[i]*1.001, 1000]]}
            self.handle_depth(t[i], dummy_depth)
        self.testing = False
                

if __name__ == '__main__':
    rbt = Robot()
    rbt.start()
    time.sleep(10000000)
    rbt.stop()

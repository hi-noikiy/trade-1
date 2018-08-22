#!/usr/bin/python
# -*- coding: UTF-8 -*-

#from tkinter import *
import tkinter as tk
from tkinter import ttk
from collections import OrderedDict

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg,NavigationToolbar2TkAgg
#from matplotlib.figure import Figure

from mpl_finance import candlestick_ochl,candlestick2_ochl
from datetime import datetime,timedelta
import numpy as np
import pandas as pd
from market import mkt
from tanalyse import Bbands,Macd,Stoch
from robot import rbt


def ta_graphic(indicator, ax, *params):
    df = params[0]
    if indicator == 'kline':
        candlestick_ochl(ax, np.array(df))#, width=0.4, colorup='#77d879', colordown='#db3f3f')
    else:
        line_color = ('b','g','r','c','m','y','k')#,'w')
        line_maker = ('.',',','o') ###...
        line_style = ('-', '--', '-.', ':')
        t = list(map(datetime.fromtimestamp, df['t']))
        for i in range(df.columns.size): #exclude 't'
            if df.columns[i] == 't':
                continue
            col = df[df.columns[i]]
            cms = line_color[int(i%len(line_color))]+line_style[int(i/len(line_color))]
            ax.plot(t, col, cms)

    ax.set_title(indicator, fontproperties="SimHei")
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H')) #%H:%M:%S'))
    ax.xaxis.set_major_locator(mdates.DayLocator()) #HourLocator())
    ax.legend()
    plt.xticks(rotation=45)
    #plt.show()

    if len(params) > 1:
        hist = params[1]
        if len(hist) > 0:
            for i in range(len(hist)):
                time = datetime.fromtimestamp(hist[i][0])
                type = hist[i][1]
                price = hist[i][2]
                if type == 'open_buy':
                    cms = 'ro'
                elif type == 'open_sell':
                    cms = 'bo'
                elif type == 'margin_sell' or type == 'loss_sell' or type == 'margin_buy' or type == 'loss_buy':
                    cms = 'go'
                ax.plot([time], [price], cms)

class windows:
    def __init__(self):
        self.win = tk.Tk()
        #bind exit method
        self.win.protocol("WM_DELETE_WINDOW", self.exit)
        self.win.bind('<Escape>', lambda e: self.exit())

        #self.win.geometry('800x600') #主窗口大小
        self.win.title("trade")
        matplotlib.use('TkAgg')


    def mainloop(self):
        self.layout()
        self.win.mainloop()

    def layout(self):
        f = tk.Frame(self.win)
        self.param_select_layout(f)
        f.pack(side=tk.TOP)
        f = tk.Frame(self.win)
        self.tab_layout(f)
        f.pack(side=tk.TOP,fill=tk.BOTH, expand=tk.YES)

    def param_select_layout(self, parent):
        self.indicator_opt = ['bbands','macd', 'stoch']
        self.plat_opt = ['coinex','okex']
        self.pair_opt = ['btc_usdt','etc_usdt','eos_usdt','eth_usdt']
        self._opt = ['1','2']
        self.add_frame_combobox(parent, self.indicator_opt, self.indicator_select, side=tk.LEFT)
        self.add_frame_combobox(parent, self.plat_opt, self.plat_select, side=tk.LEFT)
        self.add_frame_combobox(parent, self.pair_opt, self.pair_select, side=tk.LEFT)
        self.add_frame_combobox(parent, self._opt, self._select, side=tk.LEFT)
        pass

    def add_frame_combobox(self, parent, options, func, **params):
        f = tk.Frame(parent, height=80, width=100)
        f.pack(**params)
        comb = ttk.Combobox(f,textvariable=tk.StringVar())
        comb['values'] = options
        comb.bind('<<ComboboxSelected>>', func)
        comb.pack()

    def indicator_select(self, event):
        self.indicator = event.widget.get()
        rbt.indicator = self.indicator
        if self.indicator == 'bbands':
            kl = self.bbands.get_kl()
        elif self.indicator == 'macd':
            kl = self.macd.get_kl()
        elif self.indicator == 'stoch':
            kl = self.stoch.get_kl()
        self.handle_kline(kl)

    def plat_select(self, event):
        pass

    def pair_select(self, event):
        pass

    def _select(self, event):
        pass

    def tab_layout(self, parent):
        tabs=OrderedDict([("分析",None), ("行情",None), ("交易",None), ("机器人",None), ("debug", None)])
        tab = ttk.Notebook(parent)
        
        for key in tabs.keys():#sorted(tabs.keys()):
            tabs[key] = ttk.Frame(tab)
            tab.add(tabs[key], text=key)
        tab.pack(expand=1, fill="both")

        self.tab_market_layout(tabs['行情'])
        self.tab_trade_layout(tabs['交易'])
        self.tab_analysis_layout(tabs['分析'])
        self.tab_robot_layout(tabs['机器人'])
        self.tab_debug_layout(tabs['debug'])


    def tab_market_layout(self, parent):
        return

    def tab_trade_layout(self, parent):
        return

    def tab_analysis_layout(self, parent):
        fig,self.ta_axes = plt.subplots(2,1,sharex=True)
        self.ta_canva =FigureCanvasTkAgg(fig, master=parent)
        self.ta_canva.get_tk_widget().pack(fill=tk.BOTH, expand=1)
        self.ta_canva._tkcanvas.pack(fill=tk.BOTH, expand=1)
        toolbar = NavigationToolbar2TkAgg(self.ta_canva, parent)
        toolbar.update()
        ###data graphic
        self.indicator = 'bbands'
        self.bbands = Bbands()
        self.macd = Macd()
        self.stoch = Stoch()
        mkt.register_handle('kline', self.bbands.handle_data)
        mkt.register_handle('kline', self.macd.handle_data)
        mkt.register_handle('kline', self.stoch.handle_data)
        #mkt.register_handle('depth', win.handle_depth)
        mkt.register_handle('kline', self.handle_kline)

    def tab_robot_layout(self, parent):
        #btn = ttk.Button(parent,text='test',command=self.btn_click)
        #btn.pack()
        return
        
    def tab_debug_layout(self, parent):
        self.plat_select_widget(parent)
        self.debug_label=tk.Label(parent,bg='pink', text='empty')
        self.debug_label.pack()


    def handle_depth(self, timestamp, depth):
#        print("win handle depth",price_history)
#        ta_graphic('price', self.ta_axes[0], pd.DataFrame(price_history, columns = ['t','price']))
#        self.ta_canva.draw()
        pass

    def handle_kline(self, kl):
        self.ta_axes[0].cla()
        self.ta_axes[1].cla()
        if self.indicator == 'bbands':
            ta_graphic('price', self.ta_axes[1], kl.loc[:,['t','c']], rbt.trade_history)
            ta_graphic('bbands', self.ta_axes[1], self.bbands.get_data())
        elif self.indicator == 'macd':
            ta_graphic('price', self.ta_axes[0], kl.loc[:,['t','c']], rbt.trade_history)
            ta_graphic('macd', self.ta_axes[1], self.macd.get_data())
        elif self.indicator == 'stoch':
            ta_graphic('price', self.ta_axes[0], kl.loc[:,['t','c']], rbt.trade_history)
            ta_graphic('stoch', self.ta_axes[1], self.stoch.get_data())
        else:
            pass
        self.ta_canva.draw()

    def btn_click(self):
        pass
        
    def plat_select_widget(self, parent):
        self.plat=("okex","coinex","fcoin")
        self.platvar = tk.StringVar()
        self.platvar.set(0)

        lf=tk.LabelFrame(parent,  text="平台选择")
        for i in range(len(self.plat)):
            tk.Radiobutton(lf, variable=self.platvar, value=self.plat[i],
                        text=self.plat[i],indicatoron=0, width=10,
                        command=self.debug_label_update).pack()
        lf.pack()

    def debug_label_update(self):
        p = self.platvar.get()
        self.debug_label.config(text='platform selected:  '+p)


    def exit(self):
        mkt.unregister_handle('kline', self.bbands.handle_data)
        mkt.unregister_handle('kline', self.macd.handle_data)
        mkt.unregister_handle('kline', self.stoch.handle_data)
        mkt.unregister_handle('kline', self.handle_kline)
#        mkt.unregister_handle('depth', self.handle_depth)
        self.win.quit()
        self.win.destroy()

win = windows()
if __name__ == '__main__':
    win.mainloop()


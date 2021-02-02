import Universe as uv
from Alpha import AlphaBase
from ExprScript import ExprScriptBase
from Niodata import *
from ExprManager import fm
import Oputil as Op
import numpy as np
import pandas as pd
from DataRegistry import dr
from Config import Config
# from scipy.stats.stats import skew
from scipy.stats import rankdata
from scipy.stats.mstats import rankdata as rank2
import copy
import leadlag
'''
WAVE alpha sample, using interval_data
'''


class AlphaWave1(ExprScriptBase):
    def __init__(self, cfg):
        '''
          initialize functions: load data, parse config, init_variables.
        '''
        ExprScriptBase.__init__(self, cfg)
        self.lookback = cfg.getAttributeDefault('lookback', 10)
        self.SNAPCOUNT1 = int(cfg.getAttributeDefault('snapcount', 6))
        self.snapcount = Config.getInstance().getMacros().getAttributeDefault('SNAPCOUNT', 60)
        self.offset = cfg.getAttributeDefault('offset', 1024)

        self.tic = dr.GetData('ticker')
        self.ticIx = dr.GetData('tickerIx')

    def DailyRun(self, di, ti=None):
        '''
          example: alpha = - sum(delta(last_price, 1interval) * interval_volume)
        '''

        def norm(x, normtype=0):
            if normtype == 0:
                return x
            elif normtype == 1:
                return x / np.nansum(x, axis=0)
            elif normtype == 2:
                m = np.nanmean(x, axis=0)
                std = np.nanstd(x, axis=0)
                return (x - m) / std
            elif normtype == 3:
                df = pd.DataFrame(x)
                return df.rank(axis=0).values

        n = self.SNAPCOUNT1
        d1 = (abs(self.avgret[di-1680]) - abs(self.bavgret[di-1680]))/ (abs(self.avgret[di-1680]) + abs(self.bavgret[di-1680]))#split side, rt=3,0.25IR,14.8ret
        d2a = (self.avgflag[di-1680][:n-1] - self.bavgflag[di-1680][:n-1])/ (self.avgflag[di-1680][:n-1] + self.bavgflag[di-1680][:n-1])#split side
        d2b = (self.avgflag[di-1680][n-1:] - self.bavgflag[di-1680][n-1:])/ (self.avgflag[di-1680][n-1:] + self.bavgflag[di-1680][n-1:])#split side
        d2 = np.concatenate((d2a,d2b), axis =0)
        d3a = (self.stdret[di-1680][:n-1] - self.bstdret[di-1680][:n-1])/ (self.stdret[di-1680][:n-1] + self.bstdret[di-1680][:n-1])#split side
        d3b = (self.stdret[di-1680][n-1:] - self.bstdret[di-1680][n-1:])/ (self.stdret[di-1680][n-1:] + self.bstdret[di-1680][n-1:])#split side
        d3 = np.concatenate((d3a,d3b), axis =0)
        d4 = (self.stdvolratio[di-1680] - self.bstdvolratio[di-1680])/ (self.stdvolratio[di-1680] + self.bstdvolratio[di-1680])#split side
        self.bidsize_5min = np.concatenate((self.bidsize[di][:24], self.bidsize[di][-25:]), axis =0 )
        d5 = self.sumbid1sell[di-1680]/self.bidsize_5min#f2(r5),rt=0,5 ,11ret,0.29IR,recent good;
        self.asksize_5min = np.concatenate((self.asksize[di][:24], self.asksize[di][-25:]), axis =0 )
        d6 = self.sumask1buy[di-1680]/self.asksize_5min#f1,IR0.15,rt=0,1,ret8;
        self.volume_5min = np.concatenate((self.volume[di][:24], self.volume[di][-25:]), axis =0 )

        r1 = self.bavgflag[di-1680]
        r2 = self.avgflag[di-1680]
        r3 = self.bavgret[di-1680]#f2(r4),rt=5,ret17,IR0.28,corr0.6;
        r4 = self.bskewvolratio[di-1680]
        r5 = self.avgret[di-1680]
        r6 = self.skewvolratio[di-1680]
        r7 = self.bstdvolratio[di-1680]
        r8 = self.skewbid1sell[di-1680]
        r9 = self.skewask1buy[di-1680]
        f1_d1 = (d5-d6)/(d5+d6)#f1(f1_d1),rt=0,ret25,IR0.7,worst~0.rt=1,ret15,worst-6.pos corr0.34;
        f2_d1 = self.bidsize_5min/self.asksize_5min
        f2_d2 = self.sumbid1sell[di-1680]/self.sumask1buy[di-1680]
        f2_d3 = abs(r3)+abs(r5)#f2(volume),rt=0,ret15,IR0.36;rt=3,5,ret13;
        # af = leadlag.f1(r4, 0, n-1, axis = 0, rettype = self.rtype)
        # af = leadlag.f1(d2, 0, 48, axis = 0, rettype = self.rtype)
        af = leadlag.f2(r6, r9, 0, n-1, axis = 0, rettype = self.rtype)

        self.alpha[self.valid[di, 0:uv.instsz] == True] = af[self.valid[di, 0:uv.instsz] == True]
        self.alpha[self.valid[di, 0:uv.instsz] != True] = np.nan

    #alpha functions
    def vtclockStdRatio(self, v_x, t_x, axis = 0, rtype = 0):
        std1 = self.f1(v_x, 0, 15, axis = axis, rettype=rtype)
        std2 = self.f1(t_x, 0, 61, axis = axis, rettype=rtype)
        return std1/std2
    def vtwapRet(self, vwap, twap, rtype, axis = 0):
        ret1 = (vwap[1:] - vwap[:-1])/vwap[:-1]
        ret2 = (twap[1:] - twap[:-1])/twap[:-1]
        x = (ret1 - ret2)/(ret1 + ret2)
        return self.f1(x,0,15, axis =axis , rettype = rtype)

    def hmlRetDiff(self, hml, price, return1, rtype, axis = 0):
        if rtype == 0:
            std1 = np.nanstd(hml/price, axis = axis)
            std2 = np.nanstd(return1, axis = axis)
            return std1 - std2
        elif rtype == 1:
            pass
    def volStdDiff(self, meanv, stdv,rtype, axis = 0):
        std1 = np.nanstd(meanv, axis = axis)
        std2 = np.nanmean(stdv, axis = axis)
        m1 = np.nanmean(meanv, axis = axis)
        if rtype == 0:
            return (std1 - std2)

    def retPstdDiff(self, stdret, stdp, vwap, rtype, axis = 0):
        if rtype == 0:
            std1 = np.nanmean(stdret, axis = axis)
            std2 = np.nanmean(stdp, axis = axis)/np.nanmean(vwap, axis = axis)
            return (std1 - std2)/(std1 + std2)
        elif rtype == 1:
            return np.nanmean(stdret - stdp, axis = axis)
    def stdNumtrade(self, numPchange, perup, perdn, axis = 0):
        numtrade = numPchange/(perup + perdn)
        return 1/np.nanstd(numtarde, axis = axis)

    #tool functions
    def resample(self, x, size_raw, size_resampled):
        step = int(size_raw/size_resampled)
        res = np.zeros((size_resampled, x.shape[1]))
        for i in range(size_resampled):
            res[i, :] = np.nanmean(x[step*i:step*(i+1),:], axis=0)
            # res[i, :] = (np.nanmax(x[step*i:step*(i+1),:], axis=0) + np.nanmin(x[step*i:step*(i+1),:], axis=0))/2
            # res[i, :] = (np.nanmedian(x[step*i:step*(i+1),:], axis=0) )
        return res
    def norm(self, x, rtype, axis =0 ):
        if rtype == 1:
            return x/np.nansum(x, axis= axis)
        elif rtype == 2:
            m = np.nanmean(x, axis = axis)
            std = np.nanstd(x, axis = axis)
            return (x-m)/std
        elif rtype == 3:
            return pd.DataFrame(x).rank(axis = axis).values
    def tsneutralize(self, x, y):
        mx = np.nanmean(x, axis=0)
        my = np.nanmean(y, axis=0)
        x1 = x - mx
        y1 = y - my
        beta = np.nansum(x1*y1, axis =0 )/np.nansum(x1**2, axis =0)
        return y - beta * x
    def f2(self, x1, y1, st, ed, axis =0, rettype = 0):
     def skew(x, axis=0):
        m = np.nanmean(x, axis=axis)
        std = np.nanstd(x, axis=axis)
        return np.nanmean(np.power((x - m) / std, 3), axis=axis)

     def kurt(x, axis=0):
        m = np.nanmean(x, axis=axis)
        std = np.nanstd(x, axis=axis)
        return np.nanmean(np.power((x - m) / std, 4), axis=axis)
     x = x1[st:ed]
     y = y1[st:ed]
     if rettype == 0:
         return Op.corr(x, y)
     elif rettype == 1:
         m_x = np.nanmean(x, axis=0)
         m_y = np.nanmean(y, axis=0)
         x1 = x - m_x
         y1 = y - m_y
         beta = np.nansum(x1 * y1, axis=0) / np.nansum(x1 ** 2, axis=0)
         return beta
     elif rettype == 2:
         m_x = np.nanmean(x, axis=0)
         m_y = np.nanmean(y, axis=0)
         x1 = x - m_x
         y1 = y - m_y
         beta = np.nansum(x1 * y1, axis=0) / np.nansum(x1 ** 2, axis=0)
         return np.nanmean(y - beta * x, axis=0)
     elif rettype == 3:
         m_x = np.nanmean(x, axis=0)
         m_y = np.nanmean(y, axis=0)
         x1 = x - m_x
         y1 = y - m_y
         beta = np.nansum(x1 * y1, axis=0) / np.nansum(x1 ** 2, axis=0)
         return np.nanstd(y - beta * x, axis=0)
     elif rettype == 4:
         m_x = np.nanmean(x, axis=0)
         m_y = np.nanmean(y, axis=0)
         x1 = x - m_x
         y1 = y - m_y
         beta = np.nansum(x1 * y1, axis=0) / np.nansum(x1 ** 2, axis=0)
         return skew(y - beta * x, axis=0)
     elif rettype == 5:
         m_x = np.nanmean(x, axis=0)
         m_y = np.nanmean(y, axis=0)
         x1 = x - m_x
         y1 = y - m_y
         beta = np.nansum(x1 * y1, axis=0) / np.nansum(x1 ** 2, axis=0)
         return kurt(y - beta * x, axis=0)
     elif rettype == 6:
         return np.nanstd(x, axis=0) / np.nanstd(y, axis=0)

    def f1(self, x1, st, ed, axis=0, rettype=0):
        def skew(x, axis=0):
            m = np.nanmean(x, axis=axis)
            std = np.nanstd(x, axis=axis)
            return np.nanmean(np.power((x - m) / std, 3), axis=axis)

        def kurt(x, axis=0):
            m = np.nanmean(x, axis=axis)
            std = np.nanstd(x, axis=axis)
            return np.nanmean(np.power((x - m) / std, 4), axis=axis)
        x = x1[st:ed]
        if rettype == 0:
            return np.nanmean(x, axis = axis)
        elif rettype == 1:
            return np.nanstd(x, axis = axis)
        elif rettype == 2:
            return skew(x, axis = axis)
        elif rettype == 3:
            return kurt( x, axis=axis)
        elif rettype == 4:
            x_0 = x[st+1:ed-1]
            x_1 = x[st:ed-2]
            # print(x_0.shape)
            # print(x_1.shape)
            m_0 = np.nanmean(x_0, axis=0)
            m_1 = np.nanmean(x_1, axis=0)
            x_2 = x_0 - m_0
            x_3 = x_1 - m_1
            beta = np.nansum(x_2 * x_3, axis=0) / np.nansum(x_3 ** 2, axis=0)
            return beta
        elif rettype == 5:
            x_0 = x[st+1:ed-1]
            x_1 = x[st:ed-2]
            m_0 = np.nanmean(x_0, axis=0)
            m_1 = np.nanmean(x_1, axis=0)
            x_2 = x_0 - m_0
            x_3 = x_1 - m_1
            beta = np.nansum(x_2 * x_3, axis=0) / np.nansum(x_3 ** 2, axis=0)
            return np.nanmean(x_2 - beta * x_3, axis = axis)
        elif rettype == 6:
            arg = np.argsort(x, axis = axis)
            return np.nanmean(arg[-4:] - arg[:4],axis = axis)
        elif rettype == 7:
            nonan = ~np.isnan(x)
            return np.nansum(nonan, axis = axis)

    def lead_lag(self,x, y, rtype, axis = 0, lag = 1):
        x1 = x[:-lag]
        y1 = y[lag:]
        def skew(x, axis=0):
            m = np.nanmean(x, axis=axis)
            std = np.nanstd(x, axis=axis)
            return np.nanmean(np.power((x - m) / std, 3), axis=axis)

        def kurt(x, axis=0):
            m = np.nanmean(x, axis=axis)
            std = np.nanstd(x, axis=axis)
            return np.nanmean(np.power((x - m) / std, 4), axis=axis)
        if rtype == 0:
            return Op.corr(x1, y1)
        elif rtype == 1:
            m_x = np.nanmean(x1, axis = axis)
            m_y = np.nanmean(y1, axis = axis)
            x2 = x1 - m_x
            y2 = y1 - m_y
            beta = np.nansum(y2*x2, axis = axis)/np.nansum(x2**2, axis = axis)
            return beta
        elif rtype == 2:
            m_x = np.nanmean(x1, axis = axis)
            m_y = np.nanmean(y1, axis = axis)
            x2 = x1 - m_x
            y2 = y1 - m_y
            beta = np.nansum(y2*x2, axis = axis)/np.nansum(x2**2, axis = axis)
            return np.nanmean(y1 - beta * x1, axis = axis)
        elif rtype == 3:
            m_x = np.nanmean(x1, axis = axis)
            m_y = np.nanmean(y1, axis = axis)
            x2 = x1 - m_x
            y2 = y1 - m_y
            beta = np.nansum(y2*x2, axis = axis)/np.nansum(x2**2, axis = axis)
            return np.nanstd(y1 - beta * x1, axis = axis)
        elif rtype == 4:
            m_x = np.nanmean(x1, axis = axis)
            m_y = np.nanmean(y1, axis = axis)
            x2 = x1 - m_x
            y2 = y1 - m_y
            beta = np.nansum(y2*x2, axis = axis)/np.nansum(x2**2, axis = axis)
            return skew(y1 - beta * x1, axis = axis)
        elif rtype == 5:
            m_x = np.nanmean(x1, axis = axis)
            m_y = np.nanmean(y1, axis = axis)
            x2 = x1 - m_x
            y2 = y1 - m_y
            beta = np.nansum(y2*x2, axis = axis)/np.nansum(x2**2, axis = axis)
            return kurt(y1 - beta * x1, axis = axis)
        elif rtype == 6:
            return np.nanstd(y1, axis = axis)

# create an instance
def create(cfg):
    return AlphaWave1(cfg)

import Universe as uv
from ExprScript import ExprScriptBase
from Niodata import *
from ExprManager import fm
import Oputil as Op
import numpy as np
from DataRegistry import dr


class AlphaIntraExample(ExprScriptBase):
    def __init__(self, cfg):
        '''
          initialize functions: load data, parse config, init_variables.
        '''
        ExprScriptBase.__init__(self, cfg)
        self.lookback = cfg.getAttributeDefault('lookback', 10)
        self.tic = dr.GetData('ticker')
        self.ticIx = dr.GetData('tickerIx')
        self.asksize = dr.GetData('Interval1min.test_interval_asksize')
        self.bidsize = dr.GetData('Interval1min.interval_bidsize')
        {{GetData}}
        self.vwap_p = dr.GetData('IntervalData15s.vwap_p') 
        
        self.per_pGoUp = dr.GetData('IntervalData15s.per_pGoUp') 
        self.per_buy = dr.GetData('IntervalData15s.per_buy') 
        
        self.num_trade = dr.GetData('IntervalData15s.num_trade') 
        self.buy_vol = dr.GetData('IntervalData15s.buy_vol') 
        self.sum_vol = dr.GetData('IntervalData15s.sum_vol') 
        self.std_vol = dr.GetData('IntervalData15s.std_vol') 
        {{preprocess}}


    def DailyRun(self, di):
        '''
          support slope
        '''

        def skew(x, ax = 0):
          mean = np.nanmean(x, axis = ax)
          std = np.nanstd(x, axis = ax)
          return np.nanmean(np.power((x-mean)/std, 3), axis = ax)       
        def coskew(x, y, ax = 0):
          m_x = np.nanmean(x, axis = ax)
          m_y = np.nanmean(y, axis = ax)
          std_x = np.nanstd(x, axis = ax)
          std_y = np.nanstd(y, axis = ax)
          return np.nanmean(np.power((x-m_x)*(y-m_y)/(std_x * std_y), 3), axis = ax)   
        
        def maxdiff(x, y, ax = 0):
          max_x = np.nanmax(x, axis = ax)
          max_y = np.nanmax(y, axis = ax)
          return (max_x - max_y)/(max_x + max_y)
        def mindiff(x, y, ax = 0):
          min_x = np.nanmin(x, axis = ax)
          min_y = np.nanmin(y, axis = ax)
          return (min_x - min_y)/(min_x + min_y)      
        def maxmindiff(x, y, ax = 0):
          max_x = np.nanmax(x, axis = ax)
          max_y = np.nanmax(y, axis = ax)
          min_x = np.nanmin(x, axis = ax)
          min_y = np.nanmin(y, axis = ax)
          diff_x = (max_x - min_x)/(max_x + min_x)
          diff_y = (max_y - min_y)/(max_y + min_y)
          return (diff_x - diff_y)/(diff_x + diff_y)            
        def diff(x, y, ax = 0, rettype = 0):
          """rettype 0.mean 1.std 2.skew"""
          if rettype == 0:
            return np.nanmean((x-y)/(x+y), axis = ax)
          elif rettype ==1:
            return np.nanstd((x-y)/(x+y), axis = ax)
          elif rettype ==2:
            """rely on skew()"""
            return skew((x-y)/(x+y), ax = ax)
        def corr3(x,y,z, axis = 0):
          mx = np.nanmean(x, axis = axis)
          my = np.nanmean(y, axis = axis)
          mz = np.nanmean(z, axis = axis)
          stdx = np.nanstd(x, axis = axis)
          stdy = np.nanstd(y, axis = axis)
          stdz = np.nanstd(z, axis = axis)
          return np.nanmean((x-mx)*(y-my)*(z-mz)/(stdx * stdy * stdz), axis = axis)        
        n = 60
        # ret_p = (self.vwap_p[di-2048][2:(n+2)] - self.vwap_p[di-2048][1:(n+1)])/self.vwap_p[di-2048][1:(n+1)]
        ret_p = (self.vwap_p[di-2048][(949-n):949] - self.vwap_p[di-2048][(948-n):948])/self.vwap_p[di-2048][(948-n):948]
        p_delta = (self.vwap_p[di-2048][(949-n):949] - self.vwap_p[di-2048][(948-n):948])
        buy_gr = (self.buy_vol[di-2048][(949-n):949] - self.buy_vol[di-2048][(948-n):948])/self.buy_vol[di-2048][(948-n):948]
        std_ret = np.nanstd(ret_p, axis =0 )
        std_pd = np.nanstd(p_delta, axis = 0)
        # max_sv = np.nanmax(self.sum_vol[di-2048][(949-n):949][0:uv.instsz])
        # min_sv = np.nanmax(self.sum_vol[di-2048][(949-n):949][0:uv.instsz])
        # maxmindiff_sv = max_sv - min_sv
        # where1 = self.iter1[di-2048][1:(n+1)][0:uv.instsz] > min_sv + 0.4 *maxmindiff_sv
        # where2 = self.iter1[di-2048][1:(n+1)][0:uv.instsz] < max_sv - 0.4 *maxmindiff_sv

        {{paras}}

        """2 elements filter"""
        # temp1 = np.zeros((n, uv.instsz))
        # temp2 = np.zeros((n, uv.instsz))
        # temp1[:,:] = para1
        # temp2[:,:] = para2
        # temp1[where1] = np.nan
        # temp2[where2] = np.nan
        # para1 = temp1
        # para2 = temp2

        {{alpha}}

    def SaveVar(self, checkpoint):
        '''
          save local variables
        '''
        print('process checkpointSave')
        # print "sum1 = ", np.nansum(self.oldAlpha)
        checkpoint.save(self.oldAlpha)

    def LoadVar(self, checkpoint):
        '''
          load local variables
        '''
        print('process checkpointLoad')

        oldAlpha = checkpoint.load(1)
        # print "sum2 = ", np.nansum(oldAlpha)
        if (oldAlpha.shape > self.oldAlpha.shape):
            raise "Error: Vector loaded from checkpoint is larger than universe. Cannot continue"
        else:
            self.oldAlpha[:oldAlpha.shape[0]] = oldAlpha

# create an instance


def create(cfg):
    return AlphaIntraExample(cfg)

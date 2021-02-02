import Universe as uv
from ExprScript import ExprScriptBase
from Niodata import *
from ExprManager import fm
import Oputil as Op
import numpy as np
from DataRegistry import dr
import copy

class AlphaIntraExample(ExprScriptBase):
    def __init__(self, cfg):
        '''
          initialize functions: load data, parse config, init_variables.
        '''
        ExprScriptBase.__init__(self, cfg)
        self.lookback = cfg.getAttributeDefault('lookback', 10)
        self.tic = dr.GetData('ticker')
        self.ticIx = dr.GetData('tickerIx')

        self.high_large_buy = dr.GetData('Intervalqueuehlprice.high_large_buy')
        self.high_skew_buy = dr.GetData('Intervalqueuehlprice.high_skew_buy')
        self.low_num_sell = dr.GetData('Intervalqueuehlprice.low_num_sell')
        self.low_skew_sell = dr.GetData('Intervalqueuehlprice.low_skew_sell')
        self.low_large_sell = dr.GetData('Intervalqueuehlprice.low_large_sell')
        self.high_skew_sell = dr.GetData('Intervalqueuehlprice.high_skew_sell')
        self.low_skew_buy = dr.GetData('Intervalqueuehlprice.low_skew_buy')
        self.high_num_buy = dr.GetData('Intervalqueuehlprice.high_num_buy')
        


    def DailyRun(self, di):
        '''
          support slope
        '''



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
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

        self.iter1 = dr.GetData("Intervaldetailedstats.highBpriceNum")
        self.iter2 = dr.GetData("Intervaldetailedstats.lowApriceNum")
        self.iter3 = dr.GetData("Intervalstatsbidask4.instAction_bid1diff")
        self.iter4 = dr.GetData("Intervalextendstats.diff_ask_price")
        self.iter5 = dr.GetData("Intervalextendstats.corr_bid_price")

        


    def DailyRun(self, di):
        '''
          support slope
        '''

        # time slope bid
        # n = 24
        # weight_lst = list(np.arange(24).reshape(24,1))
        # weight = np.array(weight_lst) * uv.instsz
        # para1 = self.data1[di][43:67] * weight/(n*(n+1))

        para1 = self.iter2[di-1024][24:48][0:uv.instsz]
        para2 = self.iter4[di][24:48][0:uv.instsz]

        self.alpha = Op.corr(para1, para2)

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
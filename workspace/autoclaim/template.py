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

        {% for name in dataname -%}
            {{name}}
        {% endfor %}


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

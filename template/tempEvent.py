import Universe as uv
from Alpha import AlphaBase
from Niodata import *
#import Oputil
import numpy as np

class AlphaEventExample(AlphaBase):
  def __init__(self, cfg):
    '''
      initialize functions: load data, parse config, init_variables.
    '''
    AlphaBase.__init__(self, cfg)
    self.lookback = cfg.getAttributeDefault('lookback', 10)
    self.close = self.dr.GetData('close')
    self.cap = self.dr.GetData('cap')
    self.tic = self.dr.GetData('ticker')
    self.ticIx = self.dr.GetData('tickerIx')


    {{GetData}}
    {{preprocess}}

    self.oldAlpha = np.ones(uv.Instruments.size()) * np.nan

  def GenAlpha(self, di, ti = None):
    '''
      example for using event data
    '''
    self.offsets = self.dr.GetData('ZYYQRptforecast.offsets') # we could also load data here
    self.tprice = self.dr.GetData('ZYYQRptforecast.FORECAST_TP') # load target price from dataset ZYYQRptforecast
    for ii in range(len(self.alpha)):
      if self.valid[di][ii]: ## check if the stock is valid
        ## handle the offsets: offsets[di][ii][0] is the start index and offsets[di][ii][1] is the length of events for ii at date di
        st = self.offsets[di-self.delay][ii][0]
        len2 = self.offsets[di-self.delay][ii][1]
        if (nioIsvalid(st) and nioIsvalid(len2) and len2 > 0):
          self.alpha[ii] = np.nanmean(self.tprice[st:st+len2]) / self.cps[di-self.delay][ii] - 1
        if (not nioIsvalid(self.alpha[ii])):
          self.alpha[ii] = self.oldAlpha[ii] # set to old values if it's not valid
    self.oldAlpha[:] = self.alpha[:]

  def SaveVar(self, checkpoint):
    '''
      save local variables
    '''
    print "process checkpointSave"
    checkpoint.save(self.oldAlpha)

  def LoadVar(self, checkpoint):
    '''
      load local variables
    '''
    print "process checkpointLoad"
    oldAlpha = checkpoint.load(1)
    if (oldAlpha.shape > self.oldAlpha.shape):
      raise "Error: Vector loaded from checkpoint is larger than universe. Cannot continue";
    else:
      self.oldAlpha[:oldAlpha.shape[0]] = oldAlpha

# create an instance
def create(cfg):
  return AlphaEventExample(cfg)

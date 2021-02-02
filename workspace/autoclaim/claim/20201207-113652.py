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

        self.perbuy = dr.GetData('Intervalopenvolclockstats1.perbuy')
        self.twap = dr.GetData('Intervalopenvolclockstats1.twap')
        self.meanv = dr.GetData('Intervalopenvolclockstats1.meanv')
        self.numpchange = dr.GetData('Intervalopenvolclockstats1.numpchange')
        self.skewv = dr.GetData('Intervalopenvolclockstats1.skewv')
        self.skewret = dr.GetData('Intervalopenvolclockstats1.skewret')
        self.return1 = dr.GetData('Intervalopenvolclockstats1.return')
        self.hml = dr.GetData('Intervalopenvolclockstats1.hml')
        self.vwap = dr.GetData('Intervalopenvolclockstats1.vwap')
        self.perdn = dr.GetData('Intervalopenvolclockstats1.perdn')
        self.skewp = dr.GetData('Intervalopenvolclockstats1.skewp')
        self.vwapsell = dr.GetData('Intervalopenvolclockstats1.vwapsell')
        self.perup = dr.GetData('Intervalopenvolclockstats1.perup')
        self.stdv = dr.GetData('Intervalopenvolclockstats1.stdv')
        self.vwapbuy = dr.GetData('Intervalopenvolclockstats1.vwapbuy')
        self.stdret = dr.GetData('Intervalopenvolclockstats1.stdret')
        self.corrpv = dr.GetData('Intervalopenvolclockstats1.corrpv')
        self.stdp = dr.GetData('Intervalopenvolclockstats1.stdp')
        self.smallBuyAmount = dr.GetData('Intervalopenstats3.smallBuyAmount')
        self.smallBuyNum = dr.GetData('Intervalopenstats3.smallBuyNum')
        self.buyOrderNum = dr.GetData('Intervalopenstats3.buyOrderNum')
        self.largeBuyAmount = dr.GetData('Intervalopenstats3.largeBuyAmount')
        self.largeSellAmount = dr.GetData('Intervalopenstats3.largeSellAmount')
        self.smallSellNum = dr.GetData('Intervalopenstats3.smallSellNum')
        self.buySize = dr.GetData('Intervalopenstats3.buySize')
        self.buyAmount = dr.GetData('Intervalopenstats3.buyAmount')
        self.sellSize = dr.GetData('Intervalopenstats3.sellSize')
        self.sellOrderNum = dr.GetData('Intervalopenstats3.sellOrderNum')
        self.smallSellAmount = dr.GetData('Intervalopenstats3.smallSellAmount')
        self.largeBuyNum = dr.GetData('Intervalopenstats3.largeBuyNum')
        self.largeSellNum = dr.GetData('Intervalopenstats3.largeSellNum')
        self.sellAmount = dr.GetData('Intervalopenstats3.sellAmount')
        self.vlargesell = dr.GetData('Intervalopenstats4.vlargesell')
        self.vbuy = dr.GetData('Intervalopenstats4.vbuy')
        self.vlargebuy = dr.GetData('Intervalopenstats4.vlargebuy')
        self.numsell = dr.GetData('Intervalopenstats4.numsell')
        self.numbuy = dr.GetData('Intervalopenstats4.numbuy')
        self.skewvolume = dr.GetData('Intervalopenstats4.skewvolume')
        self.vsell = dr.GetData('Intervalopenstats4.vsell')
        self.mean_singleSellAmount = dr.GetData('Intervalopenstats2.mean_singleSellAmount')
        self.mean_sellOrderAmount = dr.GetData('Intervalopenstats2.mean_sellOrderAmount')
        self.largeorderratio = dr.GetData('Intervalopenstats2.largeorderratio')
        self.mean_buyOrderNum = dr.GetData('Intervalopenstats2.mean_buyOrderNum')
        self.mean_singleOrderAmount = dr.GetData('Intervalopenstats2.mean_singleOrderAmount')
        self.buyorderskew = dr.GetData('Intervalopenstats2.buyorderskew')
        self.mean_orderSize = dr.GetData('Intervalopenstats2.mean_orderSize')
        self.mean_singleBuyAmount = dr.GetData('Intervalopenstats2.mean_singleBuyAmount')
        self.mean_sellOrderNum = dr.GetData('Intervalopenstats2.mean_sellOrderNum')
        self.mean_buyOrderAmount = dr.GetData('Intervalopenstats2.mean_buyOrderAmount')
        self.sellorderskew = dr.GetData('Intervalopenstats2.sellorderskew')
        self.asksize1 = dr.GetData('Intervalopenstats1.asksize1')
        self.sellorderskew = dr.GetData('Intervalopenstats1.sellorderskew')
        self.volume = dr.GetData('Intervalopenstats1.volume')
        self.num_trade = dr.GetData('Intervalopenstats1.num_trade')
        self.asksize2 = dr.GetData('Intervalopenstats1.asksize2')
        self.bidsize2 = dr.GetData('Intervalopenstats1.bidsize2')
        self.buy_vol = dr.GetData('Intervalopenstats1.buy_vol')
        self.ask2 = dr.GetData('Intervalopenstats1.ask2')
        self.sum_vol = dr.GetData('Intervalopenstats1.sum_vol')
        self.per_pGoUp = dr.GetData('Intervalopenstats1.per_pGoUp')
        self.std_ret = dr.GetData('Intervalopenstats1.std_ret')
        self.mean_singleSellAmount = dr.GetData('Intervalopenstats1.mean_singleSellAmount')
        self.bid1 = dr.GetData('Intervalopenstats1.bid1')
        self.vwap_p = dr.GetData('Intervalopenstats1.vwap_p')
        self.mean_sellOrderNum = dr.GetData('Intervalopenstats1.mean_sellOrderNum')
        self.totalbidsize = dr.GetData('Intervalopenstats1.totalbidsize')
        self.max_vol = dr.GetData('Intervalopenstats1.max_vol')
        self.largeorderratio = dr.GetData('Intervalopenstats1.largeorderratio')
        self.num_vol100 = dr.GetData('Intervalopenstats1.num_vol100')
        self.price = dr.GetData('Intervalopenstats1.price')
        self.mean_orderSize = dr.GetData('Intervalopenstats1.mean_orderSize')
        self.diff_bidask_pwv = dr.GetData('Intervalopenstats1.diff_bidask_pwv')
        self.bidsize1 = dr.GetData('Intervalopenstats1.bidsize1')
        self.asksize510 = dr.GetData('Intervalopenstats1.asksize510')
        self.mean_buyOrderNum = dr.GetData('Intervalopenstats1.mean_buyOrderNum')
        self.mean_singleBuyAmount = dr.GetData('Intervalopenstats1.mean_singleBuyAmount')
        self.std_vol = dr.GetData('Intervalopenstats1.std_vol')
        self.mean_singleOrderAmount = dr.GetData('Intervalopenstats1.mean_singleOrderAmount')
        self.std_p = dr.GetData('Intervalopenstats1.std_p')
        self.totalasksize = dr.GetData('Intervalopenstats1.totalasksize')
        self.vwap = dr.GetData('Intervalopenstats1.vwap')
        self.buyorderskew = dr.GetData('Intervalopenstats1.buyorderskew')
        self.wask = dr.GetData('Intervalopenstats1.wask')
        self.wbid = dr.GetData('Intervalopenstats1.wbid')
        self.bid2 = dr.GetData('Intervalopenstats1.bid2')
        self.bidsize510 = dr.GetData('Intervalopenstats1.bidsize510')
        self.mean_sellOrderAmount = dr.GetData('Intervalopenstats1.mean_sellOrderAmount')
        self.mean_buyOrderAmount = dr.GetData('Intervalopenstats1.mean_buyOrderAmount')
        self.ask1 = dr.GetData('Intervalopenstats1.ask1')
        self.per_buy = dr.GetData('Intervalopenstats1.per_buy')
        


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
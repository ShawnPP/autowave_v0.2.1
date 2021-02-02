
import os

from lib.libSSH import SSH

class Alpha():
    def __init__(self):
        self.config = None

        self.pnl_name = None
        self.pair = None

        self.expression = None
        self.performance = None
        self.sharpe = None
        self.ret = None
        self.corr = None
        self.corr_metad0 = None
        self.va = None
        self.performance_pct = None
        self.ret_pct = None
        self.performance_trade = None
        self.ret_trade = None

        self.pnl_flag = False # True: sharpe > bottom sharpe and 2019 sharpe > bottom sharpe
        self.corr_flag = False # True: corr < 0.42 and va < 1.2
        self.pcttrade_flag = False # True: pct ret/ raw ret > 0.5 and trade ret/raw ret > 0.5
        self.net_flag = False # True: running file < 3

    def get_performance(self, pnl_name = None, adv=False):
            simsummary = self.config.remote_dir + '/tools/simsummary.py'
            if pnl_name:
                out = SSH.execute(f'{simsummary} {self.config.pnl_dir}/{pnl_name}')
                print(out)
                return out

            if adv:
                pct_out = SSH.execute(f'{simsummary} {self.config.pnl_dir}/{self.pnl_name}_pct')
                self.performance_pct = ''.join(pct_out)
                print('performance_pct:\n', self.performance_pct, flush=True)

                trade_out = SSH.execute(f'{simsummary} {self.config.pnl_dir}/{self.pnl_name}_trade')
                self.performance_trade = ''.join(trade_out)
                print('performance_trade:\n', self.performance_trade, flush=True)

                self.ret_pct,_ = self.get_sharpe(self.performance_pct)
                self.ret_trade,_ = self.get_sharpe(self.performance_trade)
                self.criteria(method="pcttrade")
                return self.ret_pct, self.ret_trade
            else:
                out = SSH.execute(f'{simsummary} {self.config.pnl_dir}/{self.pnl_name}')
                if len(out) > 3:
                    self.performance = ''.join(out)
                    print(self.performance)
                    self.ret,self.sharpe = self.get_sharpe()
                    self.criteria()
                    return self.ret, self.sharpe
                else:
                    return False, False

    def get_sharpe(self, pfm = None, line_index = -1):
        '''
        retrive the sharpe value within the performance str.

        args
        ----
        performance : str
            the str of performance.
            in fact it's a joined str with several lines.
        line_index: int
            specify which sharpe to be retrived.
            -1 for the total sharpe or -3 for the sharpe of 2019.
        '''
        tpfm = pfm.splitlines()[line_index].split() if pfm else self.performance.splitlines()[line_index].split()
        if len(tpfm) == 15:  # IR is negative
            ret, sharpe = float(tpfm[4]), float(tpfm[6].split('(')[0])
        else:  # IR is positive
            ret, sharpe = float(tpfm[4]), float(tpfm[6].split('(')[0])
        return ret, sharpe

    def criteria(self, method = "pnl"):
        """ method: "pnl", "corr", "pcttrade" """
        if method == "pnl":
            ret19,_ = self.get_sharpe(line_index=-3)
            self.pnl_flag =  abs(self.ret) > 10 and abs(self.sharpe) > self.config.bottom_sharpe and abs(ret19) > 0.7 * abs(self.ret)
            return self.pnl_flag
        if method == "corrva":
            max_corr = max([abs(float(i)) for i in self.corr])
            max_va = (max([float(i) for i in self.va]))
            if len(self.corr) == 41 and len(self.va) == 10:
                if self.config.delay == "1":
                    if max_corr < 0.55 and max_va < 1:
                        self.corr_flag = True
                if self.config.delay == "0":
                    if max_corr < 0.55 and max_va < 1 and self.corr_metad0 < 0.2:
                        self.corr_flag = True
            return self.corr_flag, self.corr, self.va
        if method == "pcttrade":
            self.pcttrade_flag = self.ret_pct/self.ret > 0.5 and self.ret_trade/self.ret >0.5
            return self.pcttrade_flag

    def checkcorr(self, pnl_name = None):
        '''
        check the correlationship of the given pnl file.

        '''
        niubpath = self.config.remote_dir + "/tools/niubwave"
        if pnl_name:
            out = SSH.execute(f'{niubpath} {self.config.pnl_dir}/{pnl_name} ')
        else:
            out = SSH.execute(f'{niubpath} {self.config.pnl_dir}/{self.pnl_name} ')
        refinedOut = [subOut.split("\t")[0] for subOut in out]
        splitIndex = refinedOut.index('----------------------------------------------\n')
        self.corr = refinedOut[:splitIndex]
        self.va = refinedOut[splitIndex+1:]
        print('corr:', ' '.join(self.corr), flush=True)
        print('va:', ' '.join(self.va), flush=True)
        if self.config.delay == "0":
            multicorrpath = self.config.remote_dir + "/tools/multibcorr"
            out = SSH.execute(f"{multicorrpath} /dropbox/xiongzhang/alpha/meta.cquser.d0noon {self.config.pnl_dir}/{self.pnl_name} 2 2")
            print("corr with meta d0: ", out[0].split("\t")[0])
            self.corr_metad0 = float( out[0].split("\t")[0])
        try:
            self.criteria(method="corrva")
        except:
            return False, False, False
        return self.corr_flag, self.corr, self.va

    @staticmethod
    def write(outputFilePath, alphaInfo):
        output = open(os.path.join(outputFilePath), 'a+')

        output.write('\npreprocessing: ' + ' '.join([" ".join(alphaInfo["pair"][i]['dataname']) for i in range(len(self.pair))]) + "\n")
        for i,ipara in enumerate(alphaInfo["intraparas"]):
            output.write(f"para{i+1}:"+ " ".join(ipara['paras']) +"\n")
            output.write(f"alpha{i+1}:{ipara['alpha']}\n")
            output.write(f"process{i+1}:{ipara['process']}\n")
        templatePyPath = alphaInfo["templatePyPath"]
        output.write(f"template:{templatePyPath}\n")
        output.write('expression:' + alphaInfo["expression"] + '\n')
        output.write(f'pnl_name: {alphaInfo["pnlName"]}\n')
        output.write(alphaInfo["performance"])
        if alphaInfo["pnlFlag"]:
            if alphaInfo["pnlCorr"]:
                output.write('corr:\t' + ' '.join(alphaInfo["pnlCorr"]) + '\n')
                output.write('va:\t' + ' '.join(alphaInfo["pnlVa"]) + '\n')
        if alphaInfo["corrFlag"]:
            if alphaInfo["performancePct"]:
                output.write('performance_pct:\n')
                output.write(alphaInfo["performancePct"])
                output.write('performance_trade:\n')
                output.write(alphaInfo["performanceTrade"])
        output.write("*"*120)
        output.flush()

    def clean(self, pnl = True, adv = True):
        if adv:
            SSH.execute(f'rm {self.config.pnl_dir}/{self.pnl_name}_pct')
            SSH.execute(f'rm {self.config.pnl_dir}/{self.pnl_name}_trade')
        if self.pcttrade_flag == False:
            SSH.execute(f"rm {self.config.remote_dir}/dumppath/{self.pnl_name}.N,5120f")
            if pnl:
                SSH.execute(f'rm {self.config.pnl_dir}/{self.pnl_name}')
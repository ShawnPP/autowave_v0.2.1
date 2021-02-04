import threading
from lib.libSSH import SSH

def checkcorr(pnl_name=None):
    '''
    check the correlationship of the given pnl file.
    '''
    niubpath ="./OF/OFFita/tools/niub"
    out = SSH.execute(f'{niubpath} ./OF/OFFita/pnl/{pnl_name} ')
    refinedOut = [subOut.split("\t")[0] for subOut in out]
    splitIndex = refinedOut.index('----------------------------------------------\n')
    corr = refinedOut[:splitIndex]
    va = refinedOut[splitIndex + 1:]
    print("checkcorr successfully. corr: ", corr[-3:], "va: ", va[-3:])
    return corr,va

class Multithread:
    @staticmethod
    def run(pnlNames):
        for pName in pnlNames:
            thread = threading.Thread(target=checkcorr, args = (pName,))
            thread.start()

class Test:
    @staticmethod
    def test_checkcorr():
        pnlNameList = ["b1", "toolsauto2020-09-14-114814", "toolsauto2020-09-14-132647", "toolsauto2020-09-14-135226", "zxtest2020-09-10-092419", "zxtest2020-09-11-162444"]
        return checkcorr(pnlNameList[0])

    @staticmethod
    def test_Multithread_run():
        pnlNames = ["b1", "toolsauto2020-09-14-114814", "toolsauto2020-09-14-132647", "toolsauto2020-09-14-135226", "zxtest2020-09-10-092419", "zxtest2020-09-11-162444"]
        Multithread.run(pnlNames)

    @staticmethod
    def test_tuple():
        lst = ["af0", "af1", "af3"]
        tuple1 = tuple(lst)
        print(tuple1)
        lst[0] = "qt0"
        lst[1] = "qt1"
        lst[2] = "qt2"
        print(tuple1)

    @staticmethod
    def test_queue_Multithread1():
        numLst = list(range(16))


if __name__ == "__main__":
    # Test.test_checkcorr()
    # Test.test_Multithread_run()
    Test.test_tuple()
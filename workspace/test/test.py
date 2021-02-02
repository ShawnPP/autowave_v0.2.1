from lib.libSSH import SSH

def checkcorr_wave(pnl_name = None):
    niubpath = "./OF/OFFita/tools/niubwave"
    if pnl_name:
        out = SSH.execute(f'{niubpath} ./OF/OFFita/pnl/b1')
    else:
        out = SSH.execute(f'{niubpath} ./OF/OFFita/pnl/b1')

    print(out)
    refinedOut = [subOut.split("\t")[0] for subOut in out]
    splitIndex = refinedOut.index('----------------------------------------------\n')
    print("corr len:", len(refinedOut[:splitIndex]))
    print("va len: ", len(refinedOut[splitIndex+1:]))
    print("corr: ", refinedOut[:splitIndex])

    print("va: ", refinedOut[splitIndex+1:])
    result = ''.join(refinedOut)

class Test:
    @staticmethod
    def testCheckcorrWave():
        checkcorr_wave()

if __name__ == "__main__":
    Test.testCheckcorrWave()
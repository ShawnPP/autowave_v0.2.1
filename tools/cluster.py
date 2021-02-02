import warnings
warnings.filterwarnings('ignore')


import os
import matplotlib.pyplot as plt
import numpy as np
import random
import sys



from mpl_toolkits.mplot3d import Axes3D
from sklearn.cluster import KMeans, AgglomerativeClustering

from lib.libSSH import SSH




def load_pnl(dirpath):
    '''load pnl files'''

    pnl_names = list(os.walk(dirpath))[0][2]

    pnls = []

    for filename in pnl_names:
        with open(os.path.join(dirpath, filename)) as f:
            pnl = np.array([float(line.split(' ')[4]) for line in f.readlines()])
            pnls.append(pnl)

    return pnl_names, np.array(pnls)


def load_summary(local_pnl_dir, remote_pnl_dir, simsummary_path):
    '''load pnl files and get summary'''

    pnl_names = list(os.walk(local_pnl_dir))[0][2]
    # pnl_names = ['test_Intervaldetailbuyret.kurtbuyvol']
    pnls = []

    for pnl_name in pnl_names:
        out = SSH.execute(f'{simsummary_path} {remote_pnl_dir}/{pnl_name}', True, True)
        out = out[1:-2] + [out[-1]]

        # pnl
        # all 6 pnl
        # pnl = [float(line.split()[3]) for line in out]

        # if len(pnl) == 5:
        #     pnl.insert(0, 0.0)

        # pnl of 5 year
        pnl = float(out[-1].split()[3])

        # ret
        # all 6 ret
        # ret = [float(line.split()[4]) for line in out]

        # ret of 5 year
        ret = float(out[-1].split()[4])

        # sharpe of 5 year
        if len(out[-1].split()) == 15:  # IR is negative
            sharpe = float(out[-1].split()[6].split('(')[0])
        else:  # IR is positive
            sharpe = float(out[-1].split()[6][:-1])

        val = [pnl, ret, sharpe]
        print(val)

        pnls.append(np.array(val))

    return pnl_names, np.array(pnls)


def load_summary_from_npy(local_pnl_dir, npy_path):
    pnl_names = list(os.walk(local_pnl_dir))[0][2]
    pnls = np.load(npy_path)
    return pnl_names, pnls


'''load data'''
# filenames, x = load_pnl('')
# print(x.shape)


# filenames, x = load_summary('C:\\Users/YYQ/Desktop/auto_intra/autobatch/Data_PNL',
#                             './pysim_4/pnl',
#                             './pysim_4/tools/simsummary.py')

# np.save('summarys', x)


def load_test_data(length, feature_length):
    pnl_names = ['pnl ' + str(i) for i in range(length)]
    pnls = np.random.rand(length, feature_length)
    return pnl_names, pnls


# filenames, x = load_summary_from_npy('C:\\Users/YYQ/Desktop/auto_intra/autobatch/Data_PNL',
#                                      'C:\\Users/YYQ/Desktop/auto_intra/autobatch/3.npy')
#
#
# # filenames, x = load_test_data(250, 3)
# print(x.shape)
#
# '''cluster'''
#
# # N_CLUSTERS = 10
# # y = KMeans(n_clusters=N_CLUSTERS, n_jobs=16).fit_predict(x)
#
# y = AgglomerativeClustering(None, distance_threshold=10).fit_predict(x)
#
# '''output'''
#
# for i in range(len(y)):
#     print(f'{i}\t{filenames[i]}\t{y[i]}\t{x[i]}')
#
# cluster = np.unique(y)
# for i in cluster:
#     print(i, np.count_nonzero(y == i))
#
# ax = plt.subplot(111, projection='3d')
#
# coords = [[] for i in cluster]
# for i in range(len(y)):
#     coords[y[i]].append(np.log2(np.log10(x[i])))
#
# for i in range(len(coords)):
#     coords[i] = np.array(coords[i])
#
# coords = np.array(coords)
#
# for coord in coords:
#     color = random.uniform(0, 0.5), random.uniform(0, 0.5), random.uniform(0, 0.5)
#     ax.scatter(coord.T[0], coord.T[1], coord.T[2], c=color)
#
#
# plt.show()
# path = ("/").join(sys.argv[0].split("/")[:-2]) + "/pnls/test_interval_ask"
path = ("/").join(sys.argv[0].split("/")[:-2]) + "/pnls/"
a = os.walk(path)
pnls = next(a)[2]
data = []
for pnl in pnls[:]:
    name = path + pnl
    with open(name) as f:
        # data.append([i.split(" ")[1,6,7,8,9,10] for i in f.read().split("\n")])
        a = np.array([i.split(" ") for i in f.read().split("\n")][:-1])
        # data.append(a[:,[1,6,7,8,9,10]].astype(np.float))
        data.append(a[:,[1]].reshape(-1).astype(np.float))
print(len(data))
print(data)

estimator = KMeans(n_clusters=5)#构造聚类器
estimator.fit(data)#聚类
label_pred = estimator.labels_ #获取聚类标签
centroids = estimator.cluster_centers_ #获取聚类中心
inertia = estimator.inertia_ # 获取聚类准则的总和
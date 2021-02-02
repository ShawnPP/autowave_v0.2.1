import os,sys
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans, AgglomerativeClustering
import xml.etree.ElementTree as ET

class Cluster():
    def __init__(self, pnldir_path = None, n_clusters = 5):
        self.pnldir_path = pnldir_path
        self.pnls = None
        self.n_clusters = n_clusters

    def cluster(self, data, n_clusters = None):
        if not n_clusters:
            n_clusters = self.n_clusters
        estimator = KMeans(n_clusters=n_clusters)  # 构造聚类器
        estimator.fit(data)  # 聚类
        label_pred = estimator.labels_  # 获取聚类标签
        # centroids = estimator.cluster_centers_  # 获取聚类中心
        # inertia = estimator.inertia_  # 获取聚类准则的总和
        return label_pred

    def get_pnl(self, pnldir_path = None):
        if not pnldir_path:
            pnldir_path = self.pnldir_path
        a = os.walk(pnldir_path)
        self.pnls = next(a)[2]
        data = []

        for pnl in self.pnls:
            name = pnldir_path + pnl
            with open(name) as f:
                a = np.array([i.split(" ") for i in f.read().split("\n")][:-1])
                data.append(a[:, [1]].reshape(-1).astype(np.float))

        print(len(data))
        return data, self.pnls

    def main(self, pnldir_path = None, n_clusters = 5, rettype = 0):
        """
        rettype: 0. { "i" : [name for name belongs to cluster i] }   1. {"dataname": cluster num}
        """
        if not pnldir_path:
            pnldir_path = self.pnldir_path
        data, pnls = self.get_pnl(pnldir_path)
        label = self.cluster(data)
        res = {}
        if rettype == 0:
            for i in range(self.n_clusters):
                res[f"{i}"] = []
            for i, pnl in enumerate(pnls):
                res[f"{label[i]}"].append(pnl)
        elif rettype == 1:
            for i,pnl in enumerate(pnls):
                res[pnl[5:]] = label[i] # default format: test_dataname
        return res

    def dataframe(self, res, group = False):
        df = pd.DataFrame(res)
        if group == True:
            return df.groupby(1)
        return df
        pass

    def data_write(self, write_path = ("/").join(sys.argv[0].split("/")[:-2]) + "/pnls/xml/data.xml",
                   data_path = ("/").join(sys.argv[0].split("/")[:-2]) + "/data/Intervaltest.xml",
                   lack_path = ("/").join(sys.argv[0].split("/")[:-2]) + "/data/Intervaltest_lacking.xml"):
        """write corresponding data name of pnl to xml with the right format """
        cfg = ET.parse(data_path)
        root = cfg.getroot()
        rt1 = ET.Element("cqfunds")
        rt2 = ET.Element("stockdata")
        for i in range(self.n_clusters):
            sdata = ET.SubElement(rt1, "stockdata")
            cluster = ET.SubElement(sdata, "cluster")
            cluster.text = str(i)
        for stockdata in root.findall("stockdata"):
            for dataname in stockdata.findall("dataname"):
                try:
                    res[dataname.text]
                    cnum = res[dataname.text]
                except:
                    print("Lacking dataname: ", dataname.text)
                    dname = ET.SubElement(rt2, "dataname")
                    dname.text = dataname.text
                    dname.set("datapath", dataname.attrib["datapath"])
                    dname.set("datasize", dataname.attrib["datasize"])
                    dname.set("datastorage", dataname.attrib["datastorage"])
                    continue
                for sdata in rt1.findall("stockdata"):
                    if f"{cnum}" == sdata.find("cluster").text:
                        dname = ET.SubElement(sdata, "dataname")
                        dname.text = dataname.text
                        dname.set("datapath", dataname.attrib["datapath"])
                        dname.set("datasize", dataname.attrib["datasize"])
                        dname.set("datastorage", dataname.attrib["datastorage"])

        with open(write_path, "w") as f:
            f.write(ET.tostring(rt1, encoding="unicode"))
        with open(lack_path, "w") as f:
            f.write(ET.tostring(rt2, encoding="unicode"))

path = ("/").join(sys.argv[0].split("/")[:-2]) + "/pnls/Wind/"
# path = ("/").join(sys.argv[0].split("/")[:-2]) + "/pnls/pnls/"
data_path  =  ("/").join(sys.argv[0].split("/")[:-2]) + "/data/Wind.xml"
write_path = ("/").join(sys.argv[0].split("/")[:-2]) + "/pnls/xml/cluster_Wind.xml"
lack_path =  ("/").join(sys.argv[0].split("/")[:-2]) + "/pnls/xml/cluster_Wind_lacking.xml"

cluster = Cluster(path, n_clusters=20)
res = cluster.main(rettype=1)
n = cluster.n_clusters
print(res)
cluster.data_write(data_path=data_path, write_path=write_path, lack_path = lack_path)


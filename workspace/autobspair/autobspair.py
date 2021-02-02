import xml.etree.ElementTree as ET
import sys, os, jinja2, re
import time



class AutoSymPair():
    def __init__(self, xmlpath = os.path.abspath("") + "\\data.xml"):
        self.xmlpath = xmlpath
        self.wordpairs = [
                    ["buy","sell"],
                     ["Buy","Sell"],
                     ["bid","ask"],
                     ["Bid","Ask"],
                     ["large", "small"],
                     ["Large", "Small"],
                     ['high', "low"],
                     ['High', "Low"]
                     ]

    def parse_xml(self, xmlpath):
        tree = ET.parse(datapath)
        root = tree.getroot()
        datanames = []
        for stockdata in root.findall("stockdata"):
            for dataname in stockdata.findall('dataname'):
                datanames.append(dataname.text)
        return datanames

    def findsympair2(self, res, wordpair):
        if len(res) == 0:
            return None
        pattern =f"{wordpair[0]}|{wordpair[1]}"
        subpattern = "&"
        sympairs = []
        # fmt = "name1: {name1}, name2: {name2}"
        fmt = "res1: {res1}, res2: {res2}, res1 == res2: {rescompare}"
        for i,fullname1 in enumerate(res):
            if i == len(res) - 1:
                break
            name1 = fullname1.split(".")[-1]
            res1 = re.sub(pattern, subpattern, name1)
            for j,fullname2 in enumerate(res[i+1:]):
                name2 = fullname2.split(".")[-1]
                res2 = re.sub(pattern, subpattern, name2)
                rescompare = res1 == res2
                print(fmt.format(**locals()))
                if res1 == res2:
                    sympair = []
                    sympair.append(fullname1)
                    sympair.append(fullname2)
                    sympairs.append(sympair)
        return sympairs

    def findsympair1(self, datanames, wordpair):
        res1 = []
        pattern = re.compile(f"{wordpair[0]}|{wordpair[1]}")
        for fullname in datanames:
            name = fullname.split(".")[-1]
            res2 = pattern.search(name)
            if not res2 == None:
                res1.append(fullname)
        return res1

    def findsympair(self, datanames):

        res = []
        for wordpair in self.wordpairs:
            res1 = self.findsympair1(datanames, wordpair)
            if (len(res1)) != 0:
                res2 = self.findsympair2(res1, wordpair)
                res.append(res2)
        res1 = []
        for i in res:
            for j in i:
                res1.append(j)
        return res1

    def main(self):
        datanames = self.parse_xml(self.xmlpath)
        res = self.findsympair(datanames)
        for i, r in enumerate(res):
            print(i, " ", r)
        return res
if __name__ == "__main__":
    """"""
    datapath = os.path.abspath("") + "\\data.xml"
    atsym = AutoSymPair(datapath)
    atsym.main()

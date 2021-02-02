import os, json
import xml.etree.ElementTree as ET

path = os.path.abspath(__file__)
filepath = ("\\").join(path.split("\\")[:-2]) + "\\data\\"
filename = ("\\").join(path.split("\\")[:-2]) + "\\data\\datadict.json"
def get_json(filepath, filename):
    json_data = {}
    for i in os.listdir(filepath):
        print(i)
        if os.path.splitext(i)[-1] == ".xml":
            root = ET.parse(filepath + i).getroot()
            for stockdata in root.findall("stockdata"):
                for dataname in stockdata.findall("dataname"):
                    data = {}
                    data['datasize'] = dataname.attrib["datasize"]
                    data['datastorage'] = dataname.attrib["datastorage"]
                    data['dataname'] = dataname.text
                    data['cut_off_middle'] = data['datasize'].split('*')[0] == '67'
                    data['di_offset_2048'] = data['datastorage'] in ['3.77G', '14.00G']
                    data['di_offset_1680'] = data['datastorage'] in ['5.12G', '1.04G', '1.30G']
                    data['di_offset_1024'] = data['datastorage'] == "1.53G"
                    data['datanames'] = [dataname.text]
                    json_data[dataname.text] = data
    with open(filename, "a+") as f:
        json.dump(json_data, f, ensure_ascii=False)
        f.write("\n")

"""load json"""
# get_json(filepath, filename)
with open(filename, "r") as f:
    for line in f:
        json_data = json.loads(line)
    print(json_data["interval_high"])
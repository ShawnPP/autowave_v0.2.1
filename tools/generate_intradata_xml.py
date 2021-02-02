import os
import sys
import xml.etree.ElementTree as ET

if len(sys.argv) < 2:
    info = '''
    data path required.

    usage: $ python3 generate_xml.py data_path
    '''
    raise SystemExit(info)

def get_data(path,dir_pre,suffix = "f"):
    dir_pre = dir_pre
    dirs = list(os.walk(path))[0][1]

    print("dirs lens: ", len(dirs))
    dataset = []

    root = ET.Element('cqfunds')
    for dir in dirs:
        if dir[:len(dir_pre)] != dir_pre:
            continue
        print(dir)
        stockdata = ET.SubElement(root, "stockdata")
        filenames = os.listdir(os.path.join(path, dir))
        filenames.remove(".meta.info")
        filenames.remove(".meta")   
        print(filenames)
        for name in filenames:

            try:
                datasize = str(int(int(name.split(',')[-1][0:-1])/5120)) #4096
                if name.split(',')[-1][-len(suffix):] != suffix:
                    continue
            except Exception as e:
                print(e)
                continue
            dataname = ET.SubElement(stockdata, "dataname")
            datastorage = os.stat(
                os.path.join(path, dir, name)
            ).st_size / (1024.0**3)

            # For daily data, remove the last 8
            # dataname.text = name[:-8]

            # For interval data
            dataname.text = ".".join(name.split(".")[:-1])
            dataname.set("datapath", dir)
            dataname.set("datastorage", '%.2fG' %datastorage)
            dataname.set("datasize", datasize + "*5210")
        dataset.append(dir)
    print(" ".join(dataset))
    with open(dir_pre+".xml", "w") as f:
        f.write(ET.tostring(root, encoding='unicode'))

path = sys.argv[1]

if not os.path.exists(path):
    raise FileExistsError('path "' + path + '" not exist')
if not os.path.isdir(path):
    raise NotADirectoryError('path "' + path + '" is not a dir')

get_data(path, "Intervalbidask12stats")
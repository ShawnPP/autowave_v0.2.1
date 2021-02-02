import os
import sys
import xml.etree.ElementTree as ET

if len(sys.argv) < 2:
    info = '''
    data path required.

    usage: $ python3 generate_xml.py data_path
    '''
    raise SystemExit(info)


path = sys.argv[1]

if not os.path.exists(path):
    raise FileExistsError('path "' + path + '" not exist')
if not os.path.isdir(path):
    raise NotADirectoryError('path "' + path + '" is not a dir')


dirs = list(os.walk(path))[0][1]

dataset = []

for dir in dirs:

    if dir[:8] != 'Interval':
        continue

    filenames = os.listdir(os.path.join(path, dir))

    datastorage = os.stat(
        os.path.join(path, dir, filenames[0])
    ).st_size / (1024**3)

    datasize = int(filenames[0].split(',')[-1][0:-1]) // 4096

    if datasize != 1:

        dataset.append({
            'datapath': dir,
            'datanames': [name.split(',')[0][:-2] for name in filenames],
            'datastorage': '%.2fG' % datastorage,
            'datasize': str(datasize) + '*4096'
        })

print('stockdata start with "Interval"', len(dataset))


root = ET.Element('cqfunds')

for data in dataset:
    print(data)
    stockdata = ET.SubElement(root, 'stockdata')
    for name in data['datanames']:
        dataname = ET.SubElement(stockdata, 'dataname')
        dataname.text = name
    datapath = ET.SubElement(stockdata, 'datapath')
    datapath.text = data['datapath']
    datasize = ET.SubElement(stockdata, 'datasize')
    datasize.text = data['datasize']
    datastorage = ET.SubElement(stockdata, 'datastorage')
    datastorage.text = data['datastorage']

with open("intradata.xml", "w") as f:
    f.write(ET.tostring(root, encoding='unicode'))

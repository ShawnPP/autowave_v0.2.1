
import argparse
import copy
import datetime
import functools
import itertools
import jinja2
import json
import os
import paramiko
import socket
import pathlib
import sys
import time
import xml.etree.ElementTree as ET
import random
import re
from scp import SCPClient, SCPException


class Config(object):
    '''
    a model class to store config arguments.
    '''

    def __init__(self, config_path = None):
        self.stockdatas = None

        self.intraparas = None
        self.expressions = None
        self.bottom_sharpe = None
        self.delay = "1"
        self.startdate = '20160101'
        self.enddate = "TODAY"
        self.sample_num = None

        self.local_dir = None
        self.config_path = config_path
        self.script_template_path = None
        self.zxconfig_template_path = None
        self.zxadvconfig_template_path = None
        self.remote_dir = None
        self.pnl_dir = None
        self.root = ET.parse(self.config_path).getroot() if self.config_path else None

    def get_config_path(self, config_path):
        self.config_path = config_path
        print('using', self.config_path, flush=True)
        self.root = ET.parse(self.config_path).getroot()
    def get_delay(self):
        if self.root.find('delay').text:
            if self.root.find('delay').text in ["1", "0"]:
                self.delay = self.root.find('delay').text
            else:
                self.delay = "1"
            print("delay:", self.delay)
    def get_date(self):
        try:
            if self.root.find('startdate').text:
                self.startdate = self.root.find('startdate').text
            if self.root.find('enddate').text:
                self.enddate = self.root.find('enddate').text
        except Exception as e:
            print(e)
    def get_sample_num(self):
        try:
            if self.root.find('sample_num').text:
                self.sample_num = int(self.root.find('sample_num').text)
        except Exception as e:
            print("e")
            self.samplenum = None
    def get_path(self):
        self.remote_dir = self.root.find('remote_dir').text
        self.pnl_dir = self.root.find('pnl_dir').text

        '''
        get self path, set local dir and load template files besides.
        make sure template.py, zxconfig.xml and zxadvconfig.xml is placed besides auto_batch.py
        '''
        self_dir = ("/").join(str(pathlib.Path(__file__).parent.absolute()).split("\\")[:-1])
        self.local_dir = ("/").join((self_dir, 'tmp'))

        template_name = self.root.find('template_name').text
        self.script_template_path = ("/").join((self_dir, 'template', template_name))
        self.zxconfig_template_path = os.path.join(self_dir, 'zxwaveconfig_template.xml')
        self.zxadvconfig_template_path = os.path.join(self_dir, 'zxwaveadvconfig_template.xml')
    def get_stockdatas(self, sample_num = None):
        sample_num = self.sample_num
        def generate_datadict(i):
            data = i.attrib
            data['cut_off_middle'] = data['datasize'].split('*')[0] == '67'
            data['di_offset_2048'] = data['datastorage'] in ['3.77G', '14.00G']
            data['di_offset_1680'] = data['datastorage'] in ['5.12G', '1.04G', '1.30G']
            data['di_offset_1024'] = data['datastorage'] == "1.53G"
            data['dataname'] = [i.text]
            return data

        set_offset = ['di_offset_1024', 'di_offset_1680', "di_offset_2048"]
        di_offset = ['di-1024', 'di-1680', "di-2048"]

        def print_data(stockdatas, di_offset=di_offset, set_offset=set_offset):
            for j, stockdata in enumerate(stockdatas):
                print(f"stockdata{j + 1}")
                for i, s in enumerate(stockdata):
                    try:
                        di = di_offset[di_offset_index(stockdata, set_offset)]
                    except:
                        di = "di"
                    print('    '.join([
                        str(i + 1),
                        di,
                        s['datastorage'],
                        " ".join(s['dataname'])
                    ]))

        self.stockdatas = []
        if not sample_num:
            for data_argv in self.root.findall('data_argv'):
                sdata = []
                for stockdata in data_argv.findall('stockdata'):
                    for i in stockdata.findall("dataname"):
                        sdata.append(generate_datadict(i))
                self.stockdatas.append(sdata)
        elif sample_num:
            for data_argv in self.root.findall("data_argv"):
                sdata = []
                for stockdata in data_argv.findall("stockdata"):
                    n = len(stockdata.findall("dataname"))
                    snum = sample_num if sample_num < n else n
                    rdindex = random.sample(range(n), snum)
                    print("sample index:", rdindex)
                    for i in rdindex:
                        sdata.append(generate_datadict(stockdata.findall("dataname")[i]))
                self.stockdatas.append(sdata)
        print_data(self.stockdatas)
    def get_intraparas(self):
        self.intraparas = []
        for i, intrapara in enumerate(self.root.find('intraparas').findall('intrapara')):
            paras = [node.text for node in intrapara.find('paras').findall('para')]
            af = intrapara.find('alpha').text
            process = intrapara.find('process').text
            lst= process.split("\n")
            lst1 = []
            for i,l in enumerate(lst):
                if len(l) > 0:
                    lst1.append(l[16:])

            procs = ("\n").join(lst1)

            self.intraparas.append({
                'paras': paras,
                'process':procs,
                'alpha': af
            })
            print('\nintrapara', i + 1, flush=True)
            print('paras:\n\t' + '\n\t'.join(paras), flush=True)
            print('alpha:\n\t' + af, flush=True)
    def get_expressions(self):
        expressions = self.root.find("expressions")
        self.expressions = [i.text for i in expressions.findall('expression')]
        print('\nexpressions:\n', "\n".join(self.expressions), flush=True)
    def get_bottom_sharpe(self):
        self.bottom_sharpe = float(self.root.find('bottom_sharpe').text)
        print('\nbottom_sharpe:', self.bottom_sharpe, flush=True)

    def create_local_dir(self):
        '''
        create local working directory.
        used to store the generated intra_para.py, zxconfig.xml and the output result.txt
        '''
        if not os.path.exists(self.local_dir):
            os.makedirs(self.local_dir)
        if not os.path.isdir(self.local_dir):
            raise NotADirectoryError(self.local_dir + ' existed but is not a dir')
    def read_config(self, *args):
        '''
        read the config file and parse the xml.

        args
        ----
        config_path : str
            the path of the config file.
        '''
        if not self.config_path:
            self.get_config_path(args[0])
        self.get_delay()
        self.get_date()
        self.get_sample_num()
        self.get_path()
        self.get_stockdatas()
        self.get_intraparas()
        self.get_expressions()
        self.get_bottom_sharpe()

    def get_dataname_pairs(self):
        '''
        build the datanme pair list by Cartesian product the stockdatas.
        '''

        '''
        concatenate the stockdatas' dataname list to a single list and mark
        each element if it need a middle-cut-off or di-offset operation.
        '''
        def filter(duplicate_list):
            checked_elements = []
            if not len(duplicate_list):
                return

            for a, b in duplicate_list:
                if (b, a) not in checked_elements:
                    checked_elements.append((a, b))

            return checked_elements

        self.dataname_pairs = list(itertools.product(*self.stockdatas))
        print('datanames pair count:', len(self.dataname_pairs), flush=True)

        if len(self.stockdatas)==2:
            print("remove duplicate pairs")
            filtered_list = [(a, b) for a, b in self.dataname_pairs if a != b]
            self.dataname_pairs = filter(self.dataname_pairs)
            print('datanames pair count after removing duplicate:', len(self.dataname_pairs), flush=True)

        random_seed=4
        random.Random(random_seed).shuffle(self.dataname_pairs)

        print(f"shuffle pairs with seed {random_seed}")
        return self.dataname_pairs
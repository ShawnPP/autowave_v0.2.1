
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

from scp import SCPClient, SCPException


class ComConfig(object):
    '''
    a model class to store config arguments.
    '''

    def __init__(self, config_path = None):
        self.stockdatas = None

        self.intraparas = None
        self.expressions = None
        self.delay = "1"

        self.local_dir = None
        self.config_path = config_path
        self.script_template_path = None
        self.zxconfig_template_path = None
        self.zxadvconfig_template_path = None
        self.startdate = "20180101"
        self.enddate = "TODAY"
        self.alphas = 0

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
    def get_path(self):
        self.remote_dir = self.root.find('remote_dir').text
        self.pnl_dir = self.root.find('pnl_dir').text

        '''
        get self path, set local dir and load template files besides.
        make sure template.py, zxconfig.xml and zxadvconfig.xml is placed besides auto_batch.py
        '''
        self_dir = ("/").join(str(pathlib.Path(__file__).parent.absolute()).split("\\"))
        self.local_dir = ("/").join([self_dir, '/tmp'])
        print("self_dir:", self_dir)
        template_name = self.root.find('template_name').text
        self.script_template_path = ("/").join([self_dir, 'template', template_name])
        # self.script_template_path = 'C:/Users/Administrator/Desktop/CQintern05/template/template.py'
        if self.delay == "1":
            self.zxconfig_template_path = os.path.join(self_dir, 'zxcomconfig_template.xml')
        elif self.delay == "0":
            self.zxconfig_template_path = os.path.join(self_dir, 'zxcomconfig_templated0.xml')

    def get_stockdatas(self):
        print('\nalpha counts:', len(self.root.findall('simple_alpha')))
        def generate_datadict(i):
            data = i.attrib
            data['cut_off_middle'] = data['datasize'].split('*')[0] == '67'
            data['di_offset_2048'] = data['datastorage'] in ['3.77G', '14.00G']
            data['di_offset_1680'] = data['datastorage'] in ['5.12G', '1.04G', '1.30G']
            data['di_offset_1024'] = data['datastorage'] == "1.53G"
            data['dataname'] = i.text
            return data
        self.stockdatas = []
        for simple_alpha in self.root.findall('simple_alpha'):
            sdata = []
            data_argv = simple_alpha.find('data_argv')
            for data in data_argv.findall('dataname'):
                sdata.append(generate_datadict(data))
            self.stockdatas.append(sdata)

    def get_intraparas(self):
        self.intraparas = []
        for simple_alpha in self.root.findall("simple_alpha"):
            ipara = []
            for i, intrapara in enumerate(simple_alpha.find('intraparas').findall('intrapara')):
                paras = [node.text for node in intrapara.find('paras').findall('para')]
                af = intrapara.find('alpha').text

                ipara.append({
                    'paras': paras,
                    'alpha': af
                })
            self.intraparas.append(ipara)
    def get_expressions(self):
        self.expressions = []
        for alpha_node in self.root.findall("simple_alpha"):
            self.expressions.append(alpha_node.find("expression").text)
    def print_cominfo(self):
        set_offset = ['di_offset_1024', 'di_offset_1680', "di_offset_2048"]
        di_offset = ['di-1024', 'di-1680', "di-2048"]
        def print_data(stockdata, di_offset=di_offset, set_offset=set_offset):
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
        for i in range(len(self.stockdatas)):
            print(f"stockdata{i+1}:")
            print_data(self.stockdatas[i])
            print("paras:",(" ").join(self.intraparas[i]["paras"]))
            print("alpha:",self.intraparas[i]['alpha'].split("\n")[0])
            print("expression:", self.expressions[i] + "\n")
    def create_local_dir(self):
        '''
        create local working directory.
        used to store the generated intra_para.py, zxconfig.xml and the output result.txt
        '''
        if not os.path.exists(self.local_dir):
            os.makedirs(self.local_dir)
        if not os.path.isdir(self.local_dir):
            raise NotADirectoryError(self.local_dir + ' existed but is not a dir')
    def read_config(self, sample_num = None, *args):
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
        self.get_path()
        self.get_stockdatas()
        self.get_intraparas()
        self.get_expressions()
        # self.print_cominfo()
    def get_dataname_pairs(self):
        '''
        build the datanme pair list by Cartesian product the stockdatas.
        '''

        '''
        concatenate the stockdatas' dataname list to a single list and mark
        each element if it need a middle-cut-off or di-offset operation.
        '''
        self.dataname_pairs = list(itertools.product(*self.stockdatas))
        print('datanames pair count:', len(self.dataname_pairs), flush=True)
        return self.dataname_pairs

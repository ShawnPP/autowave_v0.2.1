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

from scp import SCPClient, SCPException

from lib.libAlpha import Alpha
from lib.libSSH import SSH
from lib.libConfig import Config




class ClusterBatch:
    '''

    '''

    def __init__(self, config_path = None):
        self.config_path = None
        self.config = None
        self.script_template = None
        self.dataname_pairs = None
        self.alpha = None
        self.output_filename = None
        self.progress_output = None

        if config_path:
            self.config_path = config_path
            self.config = Config(self.config_path)
        ET.register_namespace("", "pysim")

    def read_template(self):
        '''
        load template files.
        including template.py, zxconfig.xml and zxadvconfig.xml.

        load template.py as a jinja template.
        load the 2 xml config file by ET.
        '''
        print(self.config.script_template_path)
        with open(self.config.script_template_path) as f:
            self.script_template = jinja2.Template(''.join(f.readlines()))

        self.zxconfig = ET.parse(self.config.zxconfig_template_path)
        self.zxadvconfig = ET.parse(self.config.zxadvconfig_template_path)

    def generate_script(self, pair):
        '''
        generate a intra_para.py for the given dataname pair.

        args
        ----
        pair : tuple
            a tuple of datanames, also mark if the dataname need a middle-cut-off or di-offset.
            looks like ( {'dataname': ..., 'cut-off-middle': True/False, 'di-offset': True/False},
                         {'dataname': ..., 'cut-off-middle': True/False, 'di-offset': True/False} )
            note that the tuple contains more than 2 elements is supported but not tested yet.

        returns
        -------
        remote_path: str
            the path of generated intra_para.py in remote server.
        (preprocess, paras) : 2-tuple
            the content of preprocess and improved paras. log how the data be loaded and modified.
            can be print out to check if the middle-cut-off and di-offset operation is correct.
        '''

        '''
        prepare the content of init function of AlphaIntraExample class in template.py
        load every dataname by calling dr.GetData(dataname) and name it with 'iter' + index
        '''
        get_data = ['self.iter{0} = dr.GetData("{1}")'.format(i+1, "".join(iter['dataname'])) for i, iter in enumerate(pair)]

        paths = []
        infos = []

        for index, intrapara in enumerate(self.config.intraparas):

            filename = f'intra_para_{index+1}.py'
            # print(filename, flush=True)

            '''set the local and remote path of generated script'''
            path = ("/").join((self.config.local_dir, filename))
            remote_path = self.config.remote_dir + '/' + filename

            '''
            prepare the content of pre-process and paras.
            cut off the middle part or offset the di if needed.

            for data need a middle-cut-off, discard the useless data in the middle
            by concatenate the first 25 rows and last 24 rows of data at axis 1.

            for data need a di offset, replace the '[di' to '[di-1024' in paras.
            take care do not modify other iter's '[di]'.

            a deepcopy of config.paras is needed to avoid unintentionally change
            the global config and influence all following pairs.
            '''
            preprocess = []
            paras = copy.deepcopy(intrapara['paras'])

            for i, iter in enumerate(pair):
                if iter['cut_off_middle']:
                    preprocess.append(
                        f'self.iter{i+1} = np.concatenate((self.iter{i+1}[:,:25], self.iter{i+1}[:,-24:]), axis=1)')
                if iter['di_offset_1024']:
                    paras = [line.replace(f'iter{i+1}[di', f'iter{i+1}[di-1024') for line in paras]
                if iter['di_offset_1680']:
                    paras = [line.replace(f'iter{i+1}[di', f'iter{i+1}[di-1680') for line in paras]
                if iter['di_offset_2048']:
                    paras = [line.replace(f'iter{i+1}[di', f'iter{i+1}[di-2048') for line in paras]

            paras = [f'para{i+1} = {para}' for i, para in enumerate(paras)]

            '''
            render the template.py to generate a intra_para.py for the given dataname pair.
            don't forget the indents.
            '''
            content = self.script_template.render(
                GetData='\n        '.join(get_data),
                preprocess='\n        '.join(preprocess),
                paras='\n        '.join(paras),
                alpha='self.alpha = ' + intrapara['alpha']
            )

            '''save the generate intra_para.py to local directory and transder to remote server'''
            with open(path, 'w') as f:
                f.write(content)

            paths.append(remote_path)
            infos.append([preprocess, paras])

            SSH.transfer(path, remote_path)

        return paths, infos

    def generate_zxconfig(self, script_paths, pnl_name, startdate, enddate, adv=False, expression_negative=False, expression = None):
        '''
        generate a zxconfig.xml for superRun.py.

        args
        ----
        module : str
            the remote path of generated intra_para.py
            use as the module name to in template xml.
        pnl_name : str
            specify the name of pnl file superRun.py generate.

        adv : bool
            specify use zxconfig or zxadvconfig as template

        expression_negative : bool
            specify if it's needed to use a negative expression in config template

        returns
        -------
        remote_path: str
            the path of generated zxconfig.xml in remote server.
        '''

        '''set the local and remote path of generated xml'''
        path = os.path.join(self.config.local_dir, 'zxconfig.xml')
        remote_path = self.config.remote_dir + '/zxconfig.xml'

        '''deepcopy the template to avoid changes influence following pairs'''
        config = copy.deepcopy(self.zxadvconfig if adv else self.zxconfig)

        root = config.getroot()

        '''set startdate and enddate'''
        root.find('{pysim}Consts').set('startdate', startdate)
        root.find('{pysim}Consts').set('enddate', enddate)

        '''set pnl_dir'''
        root.find('{pysim}Port/{pysim}Calc').set('pnlDir', self.config.pnl_dir)
        root.find('{pysim}PortExpr').set('pnlDir', self.config.pnl_dir)

        '''set dumpPath dir'''
        if ~adv:
            for node in root.findall('{pysim}Port/{pysim}Alpha/{pysim}Op'):
                if node.attrib['mId'] == 'OpNio':
                    node.set("dumpPath", self.config.remote_dir + '/dumppath')

        '''set the expression and add '-' if needed'''
        port_expr = root.find('{pysim}PortExpr')
        port_expr.find('{pysim}Expr').set('expression', ('-' if expression_negative else '') +expression)
        print('expression:', port_expr.find('{pysim}Expr').get('expression'), flush=True)

        '''set module (remote path of generated script)'''
        for i, script_path in enumerate(script_paths):
            node = ET.SubElement(port_expr, 'Expr')
            node.set('name', f'a{i+1}')
            node.set('module', script_path)
            node.set('doStats', 'false')
            node.set('doScale', 'false')
            node.set('delay', '1')
        '''set the output pnl name'''
        if adv:
            alphas = root.findall('{pysim}Port/{pysim}Alpha')
            alphas[0].set('id', f'{pnl_name}_trade')
            alphas[1].set('id', f'{pnl_name}_pct')
        else:
            root.find('{pysim}Port/{pysim}Alpha').set('id', pnl_name)
            # print('pnl_name:', pnl_name, flush=True)

        '''save to local working directory and transfer to remote'''
        config.write(path)
        SSH.transfer(path, remote_path)
        return remote_path, port_expr.find('{pysim}Expr').get('expression')


    def alphatest(self, pair, expr, index, processed_index):
        self.alpha = Alpha()
        self.alpha.config = self.config
        self.alpha.pair = pair

        if index <= processed_index:
            return "pass the index"
        print('\nprocessing: ' + ' '.join([" ".join(pair[i]['dataname']) for i in range(len(pair))]), flush=True)

        '''set the pnl name as timestamp'''
        self.alpha.pnl_name = time.strftime('ofwd%Y-%m-%d-%H%M%S', time.localtime())
        # self.alpha.pnl_name = "test_"+ pair[0]["dataname"][0]
        print('pnl_name:', self.alpha.pnl_name, flush=True)

        '''
        generate intra_para.py and zxconfig.xml for 18-19.
        all transfer to remote server and call superRun.py with zxconfig.xml.
        '''
        remote_script_paths, fillup_infos = self.generate_script(pair)
        remote_zxconfig_path, self.alpha.expression = self.generate_zxconfig(script_paths=remote_script_paths,
                                                                             pnl_name=self.alpha.pnl_name,
                                                                             startdate='20160101', enddate='20191231',
                                                                             expression=expr)

        self.superRun(remote_zxconfig_path)

        '''
        call simsummary.py to get the performance of superRun.py generated pnl file,
        and retrieve the total sharpe value.
        '''
        ret, sharpe = self.alpha.get_performance()
        if ret == False:
            print("Pnl File does not exists...")
            return "pass the index"
        '''
        if sharpe < - bottom sharpe, change the expression to negative and call superRun again.
        also call simsummary to get the performance and retrieve the sharpe value.
        '''
        expression_negative = False

        if sharpe < 0 * -1:
            expression_negative = True
            remote_zxconfig_path, self.alpha.expression = self.generate_zxconfig(script_paths=remote_script_paths,
                                                                                 pnl_name=self.alpha.pnl_name,
                                                                                 startdate='20160101',
                                                                                 enddate='20191231',
                                                                                 expression_negative=expression_negative,
                                                                                 expression=expr)
            self.superRun(remote_zxconfig_path)
            ret, sharpe = self.alpha.get_performance()
            if ret == False:
                print("Pnl File does not exists...")
                return "pass the index"

        '''if 18-19 is ok, then check 15-19. the expression_negative is keep'''
        # if sharpe > self.config.bottom_sharpe:
        #     remote_zxconfig_path, self.alpha.expression = self.generate_zxconfig(script_paths=remote_script_paths,
        #                                                                          pnl_name=self.alpha.pnl_name,
        #                                                                          startdate='20160101',
        #                                                                          enddate='20191231',
        #                                                                          expression_negative=expression_negative,
        #                                                                          expression=expr)
        #
        #     self.superRun(remote_zxconfig_path)
        #     ret, sharpe = self.alpha.get_performance()
        #     if ret == False:
        #         print("Pnl File does not exists...")
        #         return "pass the index"
        #     self.alpha.write(self.output_pnl_filename)
        #
        #     '''if all the conditions is fit, check the correlation and get the corr and va value'''
        #     if self.alpha.pnl_flag:
        #         _,corr,va = self.alpha.checkcorr()
        #         if corr == False:
        #             print("Corr does not exists...")
        #             return "pass the index"
        #         '''
        #         if the check correlation result is fit, use the zxadvconfig as template and call superRun again,
        #         and get the performance_pct and performance_trade.
        #         '''
        #         self.alpha.write(self.output_corr_filename)
        #         if self.alpha.corr_flag:
        #             remote_zxconfig_path, self.alpha.expression = self.generate_zxconfig(adv=True,
        #                                                                                  script_paths=remote_script_paths,
        #                                                                                  pnl_name=self.alpha.pnl_name,
        #                                                                                  startdate='20170101',
        #                                                                                  enddate='20191231',
        #                                                                                  expression_negative=expression_negative,
        #                                                                                  expression = expr)
        #             self.superRun(remote_zxconfig_path)
        #             self.alpha.get_performance(adv=True)
        #
        #             if self.alpha.pcttrade_flag:
        #                 print('>>>>>> Netting Return Test >>>>>>', flush=True)
        #                 if self.config.delay == "1":
        #                     SSH.execute(f'cp {self.config.remote_dir}/dumppath/{self.alpha.pnl_name}.N,5120f /home/xiongzhang/dumpqueue/d1')
        #                 elif self.config.delay == "0":
        #                     SSH.execute(f'cp {self.config.remote_dir}/dumppath/{self.alpha.pnl_name}.N,5120f /home/xiongzhang/dumpqueue/d0')
        #                 '''write the key output to file'''
        #                 self.alpha.write(self.output_filename)

        '''
        end of a pair"
        remove pnl file at remote server and write 
        '''
        self.alpha.clean(pnl = False)
        self.progress_output.write(f'{index}\n')
        self.progress_output.flush()

        print("*" * 120, flush=True)

    def run(self, args):
        '''
        key part of auto_batch. run the whole procedures.

        args
        ----
        args : tuple
            tuple of command line args [config, resume].
                config : str. the path of config.xml
                resume : str. the path of progress file.
        '''
        self.config.read_config()
        self.read_template()
        self.config.create_local_dir()
        self.dataname_pairs = self.config.get_dataname_pairs()

        '''
        progress file is named 'progress' under local dir.
        progress file log the filename of result output at the first line and followed by the index of processed dataname pairs.

        normally, the name of output file is combined of remote dir name and timestamp.
        in resume mode, given a progress file path, the name of output file will be read
        from progress file and the new result will append to the previous result file.
        since progress file recorded the processed index in previous running, in resume
        mode, prase the processed index from the last line of progress file and start
        runnuing from processed index + 1.
        '''

        self.output_filename = None
        self.output_corr_filename = None
        self.output_pnl_filename = None
        processed_index = None

        if args.resume:
            progress_filename = args.resume
            with open(progress_filename) as f:
                lines = f.readlines()
                self.output_filename = lines[0].strip()
                self.output_corr_filename = lines[1].strip()
                self.output_pnl_filename = lines[2].strip()
                processed_index = int(lines[-1])
                print(f'resume at pairs[{processed_index + 1}] from ', progress_filename, flush=True)

        else:
            progress_filename = ("/").join((self.config.local_dir, f'progress_{"_".join(self.config.remote_dir[2:].split("/"))}'))

            '''
            if a previous progress is detected, ask user to decide continue or not.
            discard the previous progress only if user press 'y'. for any other input just exit.
            '''
            if os.path.exists(progress_filename):
                print(f'previous progress "{progress_filename}" detected. discard it and run anyway?', flush=True)
                print('(y/n): ', flush=True)
                # print('y', flush=True)
                if input() != 'y':
                    print('quit.')
                    sys.exit()
            self.output_filename = '_'.join(['result',time.strftime('%Y%m%d', time.localtime()),
                                        self.config.remote_dir.split('/')[-1]
                                        ]) + '.txt'
            self.output_corr_filename = '_'.join(['result',time.strftime('%Y%m%d', time.localtime()),
                                        self.config.remote_dir.split('/')[-1],"corr"
                                        ]) + '.txt'
            self.output_pnl_filename = '_'.join(['result',time.strftime('%Y%m%d', time.localtime()),
                                        self.config.remote_dir.split('/')[-1],"pnl"
                                        ]) + '.txt'
            processed_index = -1

        result_output = open(("/").join((self.config.local_dir, self.output_filename)), 'a+')
        print('result', 'append' if args.resume else 'save', 'to', result_output.name, flush=True)

        self.progress_output = open(progress_filename, 'w')
        self.progress_output.write(self.output_filename + '\n')
        self.progress_output.flush()
        print('progress save to', self.progress_output.name, flush=True)
        for expr in self.config.expressions:
            for index, pair in enumerate(self.dataname_pairs):
                message = self.alphatest(pair, expr, index, processed_index)
                if message == "pass the index":
                    continue
        '''end of for loop'''
        self.progress_output.close()
        os.remove(self.progress_output.name)

    def superRun(self, zxconfig_path):
        '''
        call superRun.py at remote server.

        args
        ----
        config_path : str
            the path of the zxconfig.xml at remote server.
        '''
        superRun_path = self.config.remote_dir + '/superRun.py'
        SSH.execute(f'{superRun_path} {zxconfig_path}')


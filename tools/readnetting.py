import argparse
import copy
import datetime
import functools
import itertools
import jinja2
import json 
import os
import paramiko
import pathlib
import sys
import time
import xml.etree.ElementTree as ET

from scp import SCPClient, SCPException


def retry(CustomException: Exception):
    '''
    a decorator handling specified exception.
    print hint and automatically retry.
    can only use to catch random occured network exception.

    do not use it like '@retry(Exception)' as it will handle all exception.
    do not use it to handle inevitable exceptions.

    disable when debug.
    '''

    def decorator(func):
        @functools.wraps(func)
        def wraper(*args, **kwargs):
            while True:
                try:
                    return func(*args, **kwargs)
                except CustomException as e:
                    print(f'"{e.__class__.__name__}" in function "{func.__name__}" handled. retry...')

        return wraper

    return decorator


class SSH:
    '''
    encapsulate connect, execute and file transfer of ssh connection.
    all the 3 function is declared as static method.

    the execute function can handle the server core dump exceptions and automatically retry.
    '''

    @staticmethod
    @retry(TimeoutError)
    @retry(SCPException)
    @retry(paramiko.ssh_exception.SSHException)
    @retry(paramiko.ssh_exception.NoValidConnectionsError)
    def connect():
        '''
        create a ssh connection and return.
        the address, username, password and port is hard-coded.

        an explicit close() is needed after connection.
        '''
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect("58.251.218.105", username="xiongzhang", password="zx5205t0", port=18153)
        return ssh

    @staticmethod
    @retry(TimeoutError)
    @retry(SCPException)
    @retry(paramiko.ssh_exception.SSHException)
    def execute(command, print_stdout=False, print_stderr=False):
        '''
        create a ssh connection and execute the given command at remote server.
        can handle the server core dump exceptions and automatically retry.
        print hint and retry count if met core dump.
        print hint if command is successfully executed.

        args
        ----
        command : str
            the command prepare to be executed at remote server.
        print_stdout : bool = False
            toggle print the stdout of remote server
        print_stderr : bool = False
            toggle print the stderr of remote server

        returns
        -------
        out : list
            a str list contains the output lines of executed command from remote server.
        '''

        ssh = SSH.connect()

        attempt = 1
        while True:
            '''
            ssh.exec_command return a 3-tupled file-like obj,
            representing the stdin, stdout and stderr at remote server.

            the core dump conditions can be detected within the stderr outputs.
            '''
            _, stdout, stderr = ssh.exec_command(command, timeout=180)

            '''
            read outputs of stdout and stderr from server.
            the readlines() method blocked waiting until the
            command execute finish or exceptionally quit and
            return the whole content of stdout and sederr.
            '''
            out = stdout.readlines()
            err = stderr.readlines()

            '''print the content of stdout and stderr'''
            if print_stdout:
                print('stdout:\n' + ''.join(out))
            if print_stderr:
                print('stderr:\n' + ''.join(err))

            '''
                search stderr to check if the command met a core dump.
                if 'Segmentation fault (core dumped)\n' appear
                in stderr means the superRun.py core dumped.
                so print a hint and retry at next loop.
                else means the given command didn't met a core dump.
                print a hint and exit the loop.
            '''
            if 'Segmentation fault (core dumped)\n' in err:
                print(f'command {command} core dumped. retry {attempt}')
                attempt += 1
            else:
                print(f'command {command} execute success')
                break

        ssh.close()
        return out

    @staticmethod
    @retry(TimeoutError)
    @retry(SCPException)
    @retry(paramiko.ssh_exception.SSHException)
    def transfer(src, dest):
        '''
        create a scp connection and transfer file between local and server.

        args
        ----
        src : str
            the path of the source file.

        dest : str
            the path of the transfer destination.
        '''
        ssh = SSH.connect()
        scp = SCPClient(ssh.get_transport())
        scp.put(src, dest)
        scp.close()

def checkcorr(pnl_name):
    '''
    check the correlationship of the given pnl file.

    '''
    out = SSH.execute(f'/dat/pysimrelease/pysim-4.0.0/tools/niub ./zxworka/pnl/{pnl_name} ')

    result = ''.join(out)
    corr = result.split()[0:42:2]
    va = result.split()[43:63:2]
    max_corr = max([abs(float(i)) for i in corr])
    max_va = (max([float(i) for i in va]))
    if len(corr) == 21 and len(va) == 10:
        if max_corr < 0.44 and max_va < 1.5:
            return True, corr, va

    return False, corr, va

def readnetting(prefix = "of1minb", local_dir= None, remote_path = "/dropbox/xiongzhang/addvalue/"):
    output_filename = '_'.join(['result_netting',
                                time.strftime('%Y%m%d', time.localtime())
                                ]) + '.txt'   
    local_path = "".join([local_dir, "\\tmp\\result_netting\\"])
    result_netting_output = open(os.path.join(local_path, output_filename), 'a+')
    out = SSH.execute(f'ls {remote_path}')
    names = []
    for name in "".join(out).split("\n"):
        if len(name.split(".")) == 2:
            if name.split(".")[1]  == "result":
                names.append(name.split(".")[0])
    len_pre = len(prefix)
    for name in names:
        if name[0:len_pre] == prefix:
            out = SSH.execute(f'cat {remote_path}{name}.result')
            result_netting_output.write(f"{name}.result\n")
            result_netting_output.write("  ".join(out))
            result_netting_output.write("*"*120)
            result_netting_output.write("\n")
    SSH.execute(f'rm {remote_path}{prefix}*')        

if __name__ == '__main__':
    '''
    usage

    python3 auto_batch.py [-c/--config config.xml] [-r/--resume progress_file]
    '''
    parser = argparse.ArgumentParser()

    parser.add_argument("-c", "--config", help='path of config.xml. if None then find config.xml besides auto_batch.py')
    parser.add_argument("-r", "--resume", help='path of progress.json. for resume exceptionally exited process only.')

    args = parser.parse_args()

    '''
    path of config.xml is optional. find config.xml besides auto_batch.py if the path is not provided.
    '''
    if not args.config:
        self_dir = str(pathlib.Path(__file__).parent.absolute())
        args.config = os.path.join(self_dir, 'config.xml')

    '''
    pass the args and run the auto batch
    '''
    readnetting(local_dir = self_dir)

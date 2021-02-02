

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


# timeout = 20
# socket.setdefaulttimeout(timeout)
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
                    # time.sleep(1)
                    return func(*args, **kwargs)
                except CustomException as e:
                    print(f'"{e.__class__.__name__}" in function "{func.__name__}" handled. retry...', flush=True)
        return wraper
    return decorator


class SSH:
    '''
    encapsulate connect, execute and file transfer of ssh connection.
    all the 3 function is declared as static method.

    the execute function can handle the server core dump exceptions and automatically retry.
    '''

    @staticmethod
    @retry(EOFError)
    @retry(TimeoutError)
    @retry(ConnectionError)
    @retry(socket.timeout)
    @retry(socket.error)
    @retry(SCPException)
    @retry(paramiko.ssh_exception.SSHException)
    def connect():
        '''
        create a ssh connection and return.
        the address, username, password and port is hard-coded.

        an explicit close() is needed after connection.
        '''
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect("58.251.218.105", username="xiongzhang", password="Test2020", port=18155)
        return ssh


    @staticmethod
    @retry(EOFError)
    @retry(TimeoutError)
    @retry(ConnectionError)
    @retry(socket.timeout)
    @retry(socket.timeout)
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
                print('stdout:\n' + ''.join(out), flush=True)
            if print_stderr:
                print('stderr:\n' + ''.join(err), flush=True)

            '''
                search stderr to check if the command met a core dump.
                if 'Segmentation fault (core dumped)\n' appear
                in stderr means the superRun.py core dumped.
                so print a hint and retry at next loop.
                else means the given command didn't met a core dump.
                print a hint and exit the loop.
            '''
            if 'Segmentation fault (core dumped)\n' in err:
                print(f'command {command} core dumped. retry {attempt}', flush=True)
                attempt += 1
            else:
                print(f'command {command} execute success', flush=True)
                break

        ssh.close()
        return out

    @staticmethod
    @retry(EOFError)
    @retry(TimeoutError)
    @retry(ConnectionError)
    @retry(socket.timeout)
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
        # ssh = SSH.connect()
        # scp = SFTPClient(ssh.get_transport())
        # scp.put(src, dest)
        # scp.close()
        paramiko.util.log_to_file("paramiko.log")
        host,port = "58.251.218.105",18155
        transport = paramiko.Transport((host,port))
        username,password = "xiongzhang","Test2020"
        transport.connect(None, username, password)
        sftp = paramiko.SFTPClient.from_transport(transport)
        sftp.put(src, dest)
        sftp.close()

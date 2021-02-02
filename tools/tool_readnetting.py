
import queue

import argparse
import functools
import os
import paramiko
import socket
import pathlib
import time

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
        host,port = "58.251.218.105",18153
        transport = paramiko.Transport((host,port))
        username,password = "xiongzhang","Test2020"
        transport.connect(None, username, password)
        sftp = paramiko.SFTPClient.from_transport(transport)
        sftp.put(src, dest)
        sftp.close()

class RecordNetting:

    @staticmethod
    def read_netting(prefix = "ofwc", local_dir= None, remote_path = "/dropbox/xiongzhang/addvalue/"):
        output_filename = '_'.join(['result_netting',
                                    time.strftime('%Y%m%d', time.localtime())
                                    ]) + '.txt'
        local_path = "".join([local_dir, "\\result_netting\\"])
        result_netting_output = open(os.path.join(local_path, output_filename), 'a+')
        out = SSH.execute(f'ls {remote_path}')
        result_netting_output.write(f"{remote_path} {prefix}\n")
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




class NetQueue:
    def __init__(self):
        self.running_countd0 = 0
        self.running_countd1 = 0
        self.queued0 = queue.Queue()
        self.queued1 = queue.Queue()
        self.delay = 1

    def check_running(self, delay = 1):
        remote_path = "/dropbox/xiongzhang/addvalue_d0" if delay == 0 else "/dropbox/xiongzhang/addvalue"
        out = SSH.execute(f'ls {remote_path}')
        count = 0
        for name in "".join(out).split("\n"):
            if len(name.split(".")) == 2:
                if name.split(".")[-1] == "running":
                    count+=1
        if delay == 0:
            print("d0 running: ", count)
            self.running_countd0 = count
        else:
            print("d1 running: ", count)
            self.running_countd1 = count

        return count

    def pop(self, delay = 1):
        if delay == 0:
            if not self.queued0.empty():
                nio_name = self.queued0.get_nowait()
                SSH.execute(f"cp /home/xiongzhang/dumpqueue/d0/{nio_name} /dropbox/xiongzhang/addvalue_d0")
                SSH.execute(f"rm /home/xiongzhang/dumpqueue/d0/{nio_name}")
            else:
                print("queue d0 is empty")
        else:
            if not self.queued1.empty():
                nio_name = self.queued1.get_nowait()
                SSH.execute(f"cp /home/xiongzhang/dumpqueue/d1/{nio_name} /dropbox/xiongzhang/addvalue")
                SSH.execute(f"rm /home/xiongzhang/dumpqueue/d1/{nio_name}")
            else:
                print("queue d1 is empty")

    def push(self, nio_name, delay = 1):
        if delay == 0:
            self.queued0.put(nio_name)
        else:
            self.queued1.put(nio_name)

    def get_nio_names(self, delay = 0):
        if delay == 0:
            remote_path = "/home/xiongzhang/dumpqueue/d0"
        else:
            remote_path = "/home/xiongzhang/dumpqueue/d1"
        out = SSH.execute(f'ls {remote_path}')
        for name in "".join(out).split("\n"):
            if name.split(".")[-1] == "N,5120f":
                self.push(name, delay = delay)
    def main(self):
        self.get_nio_names(delay=0)
        self.get_nio_names(delay=1)
        while(not self.queued0.empty() or not self.queued1.empty()):
            self.check_running(1)
            self.check_running(0)
            if not self.queued1.empty():
                for i in range(3-self.running_countd1):
                    self.pop(delay = 1)
            else:
                print('queue d1 is empty')
            if not self.queued0.empty():
                for i in range(3-self.running_countd0):
                    self.pop(delay = 0)
            else:
                print("queue d0 is empty")
            time.sleep(300)


if __name__ == '__main__':
    '''
    usage

    python3 auto_batch.py [-c/--config config.xml] [-r/--resume progress_file]
    '''
    parser = argparse.ArgumentParser()

    parser.add_argument("-c", "--config", help='path of config.xml. if None then find config.xml besides auto_batch.py')
    parser.add_argument("-r", "--resume", help='path of progress.json. for resume exceptionally exited process only.')
    #
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
    RecordNetting.read_netting(local_dir = self_dir, prefix="qt1",remote_path = "/dropbox/xiongzhang/addvalue/")

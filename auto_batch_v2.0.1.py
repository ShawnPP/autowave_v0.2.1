
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
from lib.libAutoBatch import AutoBatch
from lib.libClusterBatch import ClusterBatch

if __name__ == '__main__':
    '''
    usage：    python3 auto_batch.py [-c/--config config.xml] [-r/--resume progress_file]
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", help='path of config.xml. if None then find config.xml besides auto_batch.py')
    parser.add_argument("-r", "--resume", help='path of progress.json. for resume exceptionally exited process only.')
    args = parser.parse_args()
    
    '''    path of config.xml is optional. find config.xml besides auto_batch.py if the path is not provided.'''
    if not args.config:
        self_dir = str(pathlib.Path(__file__).parent.absolute())
        # args.config = os.path.join(self_dir, 'clusterconfig.xml')
        args.config = os.path.join(self_dir, 'config.xml')

    '''    pass the args and run the auto batch   '''

    # autoBatch = AutoBatch(args.config, pnl_prefix = 'zxtest')
    autoBatch = AutoBatch(args.config, pnl_prefix = 'toolsauto')
    autoBatch.run(args,fit = True)
    # autoBatch.generate_script()

    # clusterBatch = ClusterBatch(args.config)
    # clusterBatch.run(args)
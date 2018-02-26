# -*- coding: utf-8 -*-
'''
Salt grains for Grabbr
'''
# Python
import os
import json

# 3rd party
import psutil


def __virtual__():
    '''
    Only requires Salt
    '''
    return True


def process():
    '''
    Return the IDs of any running Grabbr instances
    '''
    ret = {}
    run_dir = __opts__.get('grabbr_run_dir', '/var/run/grabbr')
    for agent in os.listdir(run_dir):
        meta_file = os.path.join(run_dir, agent, 'meta')
        if not os.path.exists(meta_file):
            continue
        with open(meta_file, 'r') as mfh:
            meta = json.load(mfh)
            if psutil.Process(meta['pid']).cmdline()[0]:
                ret[meta['id']] = meta
    return {'grabbr_agents': ret}

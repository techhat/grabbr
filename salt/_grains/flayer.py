# -*- coding: utf-8 -*-
'''
Salt grains for Web Flayer
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
    Return the IDs of any running Web Flayer instances
    '''
    ret = {}
    run_dir = __opts__.get('flayer_run_dir', '/var/run/flayer')
    for agent in os.listdir(run_dir):
        meta_file = os.path.join(run_dir, agent, 'meta')
        if not os.path.exists(meta_file):
            continue
        with open(meta_file, 'r') as mfh:
            meta = json.load(mfh)
            if psutil.Process(meta['pid']).cmdline()[0]:
                ret[meta['id']] = meta
    return {'flayer_agents': ret}

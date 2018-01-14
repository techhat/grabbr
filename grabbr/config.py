# -*- coding: utf-8 -*-
'''
Config for Grabbr
'''
import os
import sys
import copy
import yaml
from salt.loader import LazyLoader
import salt.config


def load():
    '''
    Load configuration
    '''
    config = {
        'pid_file': '/var/run/grabbr/pid',
        'module_dir': '/srv/grabbr-plugins',
        'force': False,
        'random_sleep': False,
        'headers': {
            'User-Agent': ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/536.11 '
                           '(KHTML, like Gecko) Chrome/20.0.1132.47 Safari/536.11'),
        },
        'already_running': True,
    }

    with open('/etc/grabbr/grabbr', 'r') as ifh:
        config.update(yaml.safe_load(ifh.read()))

    if not os.path.exists(config['module_dir']):
        os.makedirs(config['module_dir'])

    urls = copy.copy(sys.argv[1:])

    if '--force' in urls or '-f' in urls:
        config['force'] = True

    if '--random-sleep' in urls or '-r' in urls:
        config['random_sleep'] = True

    if '--single' in urls or '-s' in urls:
        config['single'] = True

    if '--include' in urls or '-i' in urls:
        config['include_headers'] = True

    if '--verbose' in urls or '-v' in urls:
        config['verbose'] = True

    return config, urls

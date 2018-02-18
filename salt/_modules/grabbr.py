# -*- coding: utf-8 -*-
'''
Salt execution module for Grabbr
'''

import os
import json

from salt.ext import six
import salt.utils.http


def __virtual__():
    '''
    Only requires Salt
    '''
    return True


def _query(decode=False, **params):
    '''
    Send a command to the API
    '''
    api_host = __salt__['config.get']('grabbr_host', '127.0.0.1')
    api_port = __salt__['config.get']('grabbr_port', 42424)

    url = 'http://{0}:{1}'.format(api_host, api_port)

    return salt.utils.http.query(
        url,
        params=params,
        decode=decode,
        decode_type='json',
    )


def queue(urls, force=False, data=None):
    '''
    Queue up a URL or URLs for download
    '''
    if isinstance(urls, six.string_types):
        urls = [urls]
    _query(urls=urls, force=force, data=data)


def start(
        config_file='/etc/grabbr/grabbr',
        run_dir='/var/run/grabbr',
        module_dir=None,
    ):
    '''
    Start the Grabbr daemon
    '''
    if not os.path.exists(config_file):
        raise Exception('Config file ({}) not found'.format(config_file))

    if not os.path.exists(os.path.dirname(pid_file)):
        raise Exception('PID dir ({}) not found'.format(os.path.dirname(pid_file)))

    args = (
        'grabbr', '--daemon',
        '--config-file', config_file,
        '--run-dir', run_dir,
    )

    if module_dir is not None:
        if isinstance(module_dir, str):
            module_dir = [module_dir]
        if not isinstance(module_dir, list):
            raise Exception('module_dir must be a string or list')
        for item in module_dir:
            if not os.path.exists(item):
                raise Exception('module_dir {} does not exist')
        args.append('--module-dir')
        args.extend(module_dir)

    __salt__['cmd.run_bg'](args)


def stop():
    '''
    Stop the Grabbr daemon
    '''
    _query(stop=True)


def hard_stop():
    '''
    Hard stop the Grabbr daemon
    '''
    _query(hard_stop=True)


def abort():
    '''
    Abort the Grabbr daemon
    '''
    _query(abort=True)


def list_queue():
    '''
    List the contents of the queue
    '''
    return _query(list_queue=True)


def show_opts():
    '''
    List the opts for the daemon
    '''
    return _query(show_opts=True)


def active_downloads():
    '''
    Show active downloads
    '''
    context = _query(decode=True, show_context=True).get('dict', '')
    return context.get('dl_data', {})

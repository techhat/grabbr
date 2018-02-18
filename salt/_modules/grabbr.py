# -*- coding: utf-8 -*-
'''
Salt execution module for Grabbr
'''
# python
import os
import json

# salt
from salt.exceptions import CommandExecutionError
from salt.ext import six
import salt.utils.http


def __virtual__():
    '''
    Only requires Salt
    '''
    return True


def _query(decode=False, id_=None, **params):
    '''
    Send a command to the API
    '''
    agents = __grains__['grabbr_agents']

    if id_ is None:
        if 'unknown' in agents:
            id_ = 'unknown'
        else:
            if len(list(agents)) == 1:
                id_ = list(agents)[0]
            else:
                raise CommandExecutionError('A valid Grabbr id_ was not specified')
    elif id_ not in agents:
        raise CommandExecutionError('{} is not running'.format(id_))

    api_host = agents[id_].get('api_addr', '127.0.0.1')
    api_port = agents[id_].get('api_port', 42424)

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
        id_=None,
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

    if id_ is not None:
        args.extend(['--id', id_])

    __salt__['cmd.run_bg'](args)


def stop(id_=None):
    '''
    Stop the Grabbr daemon
    '''
    _query(stop=True, id_=id_)


def hard_stop(id_=None):
    '''
    Hard stop the Grabbr daemon
    '''
    _query(hard_stop=True, id_=id_)


def abort(id_=None):
    '''
    Abort the Grabbr daemon
    '''
    _query(abort=True, id_=id_)


def list_queue(id_=None):
    '''
    List the contents of the queue
    '''
    return _query(list_queue=True, id_=id_)


def show_opts(id_=None):
    '''
    List the opts for the daemon
    '''
    return _query(show_opts=True, id_=id_)


def active_downloads(id_=None):
    '''
    Show active downloads
    '''
    context = _query(decode=True, show_context=True, id_=id_).get('dict', '')
    return context.get('dl_data', {})

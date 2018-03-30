# -*- coding: utf-8 -*-
'''
Salt execution module for Web Flayer
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
    agents = __grains__['flayer_agents']

    if id_ is None:
        if 'unknown' in agents:
            id_ = 'unknown'
        else:
            if len(list(agents)) == 1:
                id_ = list(agents)[0]
            else:
                raise CommandExecutionError('A valid Web Flayer id_ was not specified')
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
        config_file='/etc/flayer/flayer',
        run_dir='/var/run/flayer',
        parser_dir=None,
        id_=None,
        api_addr='127.0.0.1',
        api_port=42424,
    ):
    '''
    Start the Web Flayer daemon
    '''
    if not os.path.exists(config_file):
        raise Exception('Config file ({}) not found'.format(config_file))

    if not os.path.exists(os.path.dirname(pid_file)):
        raise Exception('PID dir ({}) not found'.format(os.path.dirname(pid_file)))

    args = (
        'flayer', '--daemon',
        '--config-file', config_file,
        '--run-dir', run_dir,
    )

    if parser_dir is not None:
        if isinstance(parser_dir, str):
            parser_dir = [parser_dir]
        if not isinstance(parser_dir, list):
            raise Exception('parser_dir must be a string or list')
        for item in parser_dir:
            if not os.path.exists(item):
                raise Exception('parser_dir {} does not exist')
        args.append('--parser-dir')
        args.extend(parser_dir)

    if id_ is not None:
        args.extend(['--id', id_])

    if api_addr is not None:
        args.extend(['--api-addr', api_addr])

    if api_port is not None:
        args.extend(['--api-port', api_port])

    __salt__['cmd.run_bg'](args)


def stop(id_=None):
    '''
    Stop the Web Flayer daemon
    '''
    _query(stop=True, id_=id_)


def hard_stop(id_=None):
    '''
    Hard stop the Web Flayer daemon
    '''
    _query(hard_stop=True, id_=id_)


def abort(id_=None):
    '''
    Abort the Web Flayer daemon
    '''
    _query(abort=True, id_=id_)


def list_queue(id_=None):
    '''
    List the contents of the queue
    '''
    return _query(list_queue=True)


def show_opts(id_=None):
    '''
    List the opts for the daemon
    '''
    return _query(show_opts=True, id_=id_)


def active_downloads(id_=None):
    '''
    Show active downloads
    '''
    context = _query(decode=True, show_context=True).get('dict', '')
    return context.get('dl_data', {})

# -*- coding: utf-8 -*-
'''
Salt execution module for Grabbr
'''

from salt.ext import six
import salt.utils.http


def __virtual__():
    '''
    Only requires Salt
    '''
    return True


def _query(**params):
    '''
    Send a command to the API
    '''
    api_host = __salt__['config.get']('grabbr_host', '127.0.0.1')
    api_port = __salt__['config.get']('grabbr_port', 42424)

    url = 'http://{0}:{1}'.format(api_host, api_port)

    salt.utils.http.query(url, params=params)


def queue(urls, force=False, data=None):
    '''
    Queue up a URL or URLs for download
    '''
    if isinstance(urls, six.string_types):
        urls = [urls]
    _query(urls=urls, force=force, data=data)


def start():
    '''
    Start the Grabbr daemon
    '''
    __salt__['cmd.run_bg'](('grabbr', '--daemon'))


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

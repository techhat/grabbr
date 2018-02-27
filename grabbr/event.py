# -*- coding: utf-8 -*-
'''
Handle Salt event bus
'''
# 3rd party
import salt.loader
import salt.config
import salt.client
import salt.utils.event


def bus(opts):
    '''
    Connect to Salt's event bus
    '''
    salt_opts = salt.config.minion_config('/etc/salt/{}'.format(opts['salt_node']))

    event = salt.utils.event.get_event(
        opts['salt_node'],
        salt_opts['sock_dir'],
        salt_opts['transport'],
        opts=salt_opts,
        listen=False,
    )

    client = salt.client.get_local_client(salt_opts['conf_file'])

    return event


def fire(tag, data, opts):
    '''
    Fire a message on the event bus
    '''
    if opts['salt_events'] is True:
        opts['salt_event'].fire_master(data, tag)

# -*- coding: utf-8 -*-
'''
Basic functions for Grabbr
'''
import os
import sys
import copy
import yaml
import psutil
from termcolor import colored

from salt.loader import LazyLoader
import salt.config

import grabbr
import grabbr.db
import grabbr.tools
import grabbr.config

CLI_ARGS = [
    '-f', '--force',
    '-r', '--random-sleep',
    '-l', '--list-queue',
    '-s', '--single',
    '-i', '--include',
    '-v', '--verbose',
]


def loader(config, urls, dbclient):
    '''
    Load spider modules
    '''
    minion_opts = salt.config.minion_config('/etc/salt/minion')
    return LazyLoader(
        [config['module_dir']],
        minion_opts,
        tag=u'grabbr',
        pack={
            u'__opts__': minion_opts,
            u'__config__': config,
            u'__urls__': urls,
            u'__dbclient__': dbclient,
        },
    )


def run():
    '''
    Run the program
    '''
    config, urls = grabbr.config.load()

    dbclient = grabbr.db.client(config)

    if '--list-queue' in urls or '-l' in urls:
        grabbr.db.list_queue(dbclient, config)

    # Write pid file
    if not os.path.exists(config['pid_file']):
        config['already_running'] = False
        with open(config['pid_file'], 'w') as pfh:
            pfh.write(str(os.getpid()))
        pfh.close()

    modules = grabbr.loader(config, urls, dbclient)

    if not config['already_running'] or config.get('single') is True:
        while len(urls) > 0:
            url_id = None
            url = urls.pop(0)
            if url in CLI_ARGS:
                continue
            for mod in modules:
                if isinstance(url_id, int) and url_id == 0:
                    break
                if not mod.endswith('.pre_flight'):
                    continue
                url_id, url, content = modules[mod](url)
            if url_id is None:
                url_id, content = grabbr.tools.get_url(
                    url, dbclient=dbclient, config=config
                )
            grabbr.tools.process_url(url_id, url, content, modules, config)
            if len(urls) < 1:
                grabbr.db.pop_dl_queue(dbclient, urls)
            if os.path.exists('/var/run/grabbr/stop'):
                print(colored('stop file found, exiting', 'yellow', attrs=['bold']))
                os.remove('/var/run/grabbr/stop')
                break
            if config.get('single') is True:
                break
        try:
            os.remove(config['pid_file'])
        except FileNotFoundError:
            pass
    else:
        verified_running = False
        for process in psutil.process_iter():
            try:
                if 'chromium' in process.cmdline()[0]:
                    continue
                if 'python' in process.cmdline()[0]:
                    cmdline = ' '.join(process.cmdline())
                    if 'grabbr' in cmdline:
                        if os.getpid() != process.pid:
                            verified_running = True
                            print(colored(
                                'grabbr already running, adding item(s) to the queue',
                                'yellow',
                                attrs=['bold'],
                            ))
            except IndexError:
                pass
        if verified_running is False:
            print(colored('grabbr not found in process list, check /var/run/grabbr/pid', 'red', attrs=['bold']))
        grabbr.tools.queue_urls(urls, dbclient, config)

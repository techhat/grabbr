# -*- coding: utf-8 -*-
# pylint: disable=too-many-nested-blocks,too-many-branches

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

import grabbr.db
import grabbr.tools
import grabbr.config


def loader(opts, urls, dbclient):
    '''
    Load spider modules
    '''
    minion_opts = salt.config.minion_config('/etc/salt/minion')
    return LazyLoader(
        [opts['module_dir']],
        minion_opts,
        tag=u'grabbr',
        pack={
            #u'__master_opts__': master_opts,
            u'__minion_opts__': minion_opts,
            u'__opts__': opts,
            u'__urls__': urls,
            u'__dbclient__': dbclient,
        },
    )


def run():
    '''
    Run the program
    '''
    opts, urls = grabbr.config.load()

    dbclient = grabbr.db.client(opts)

    if opts.get('list_queue', False) is True:
        grabbr.db.list_queue(dbclient, opts)

    # Write pid file
    if not os.path.exists(opts['pid_file']):
        opts['already_running'] = False
        with open(opts['pid_file'], 'w') as pfh:
            pfh.write(str(os.getpid()))
        pfh.close()

    modules = grabbr.loader(opts, urls, dbclient)
    if opts['reprocess']:
        urls = grabbr.tools.reprocess_urls(urls, opts['reprocess'], dbclient)

    if not opts['already_running'] or opts.get('single') is True:
        while urls:
            url_id = None
            url = urls.pop(0)
            for mod in modules:
                if isinstance(url_id, int) and url_id == 0:
                    break
                if not mod.endswith('.pre_flight'):
                    continue
                url_id, url, content = modules[mod](url)
            if url_id is None:
                url_id, content = grabbr.tools.get_url(
                    url, dbclient=dbclient, opts=opts
                )
            if opts.get('no_plugins', False) is not True:
                grabbr.tools.process_url(url_id, url, content, modules)
            if len(urls) < 1:
                grabbr.db.pop_dl_queue(dbclient, urls)
            if os.path.exists('/var/run/grabbr/stop'):
                print(colored('stop file found, exiting', 'yellow', attrs=['bold']))
                os.remove('/var/run/grabbr/stop')
                break
            if opts.get('single') is True:
                break
        try:
            os.remove(opts['pid_file'])
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
            print(colored(
                'grabbr not found in process list, check /var/run/grabbr/pid',
                'red',
                attrs=['bold'],
            ))
        grabbr.tools.queue_urls(urls, dbclient, opts)

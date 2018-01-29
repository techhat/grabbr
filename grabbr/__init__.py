# -*- coding: utf-8 -*-
# pylint: disable=too-many-nested-blocks,too-many-branches

'''
Basic functions for Grabbr
'''
# Python
import os
import sys
import copy
import urllib

# 3rd party
import psutil
import yaml
from bs4 import BeautifulSoup
from salt.loader import LazyLoader
import salt.config

# Internal
import grabbr.db
import grabbr.tools
import grabbr.config


def loader(opts, urls, dbclient):
    '''
    Load spider modules
    '''
    minion_opts = salt.config.minion_config('/etc/salt/minion')
    return LazyLoader(
        opts['module_dir'],
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
    out = grabbr.tools.Output(opts)

    if opts.get('input_file'):
        if opts['input_file'] == '-':
            grabbr.tools.queue_urls(sys.stdin.readlines(), dbclient, opts)
        else:
            try:
                with open(opts['input_file'], 'r') as ifh:
                    links = ifh.read().splitlines()
                grabbr.tools.queue_urls(links, dbclient, opts)
            except OSError as exc:
                out.error('There was an error reading {}: {}'.format(opts['input_file'], exc))

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
        level = 0
        # Use a while instead of for, because the list is expected to expand
        while urls:
            url_id = None
            url = urls.pop(0)
            if url.strip() == '':
                continue
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
            # Display the source of the URL content
            if opts.get('source', False) is True:
                out.info(content)
            hrefs = grabbr.tools.parse_links(url, content, level, opts)
            level += 1
            if opts.get('links', False) is True:
                out.info('\n'.join(hrefs))
            if opts.get('queuelinks', False) is True:
                grabbr.tools.queue_urls(hrefs, dbclient, opts)
            if opts.get('use_plugins', True) is True:
                try:
                    grabbr.tools.process_url(url_id, url, content, modules)
                except TypeError:
                    out.warn('No matching plugins were found')
            if opts.get('queue_re'):
                grabbr.tools.queue_regexp(hrefs, opts['queue_re'], dbclient, opts)
            if len(urls) < 1:
                grabbr.db.pop_dl_queue(dbclient, urls, opts)
            if os.path.exists('/var/run/grabbr/stop'):
                out.warn('stop file found, exiting')
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
                            out.info('grabbr already running, adding item(s) to the queue')
            except IndexError:
                pass
        if verified_running is False:
            out.error('grabbr not found in process list, check /var/run/grabbr/pid')
        grabbr.tools.queue_urls(urls, dbclient, opts)

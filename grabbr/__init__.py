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
import urllib
from termcolor import colored

from bs4 import BeautifulSoup
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

    if opts.get('input_file'):
        if opts['input_file'] == '-':
            grabbr.tools.queue_urls(sys.stdin.readlines(), dbclient, opts)
        else:
            try:
                with open(opts['input_file'], 'r') as ifh:
                    links = ifh.read().splitlines()
                grabbr.tools.queue_urls(links, dbclient, opts)
            except OSError as exc:
                print(colored(
                    'There was an error reading {}: {}'.format(opts['input_file'], exc),
                    'red',
                ))

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
                print(colored(content, 'cyan'))
            # Get ready to do some html parsing
            soup = BeautifulSoup(content, 'html.parser')
            # Generate absolute URLs for every link on the page
            hrefs = []
            url_comps = urllib.parse.urlparse(url)
            for link in soup.find_all('a'):
                if level > int(opts['level']):
                    continue
                href = urllib.parse.urljoin(url, link.get('href'))
                link_comps = urllib.parse.urlparse(href)
                if link.text.startswith('javascript'):
                    continue
                if int(opts.get('level', 0)) > 0 and int(opts.get('level', 0)) < 2:
                    continue
                if opts['span_hosts'] is not True:
                    if not link_comps[1].startswith(url_comps[1].split(':')[0]):
                        continue
                hrefs.append(href.split('#')[0])
            level += 1
            # Render the page, and print it along with the links
            if opts.get('render', False) is True:
                print(colored(soup.get_text(), 'cyan'))
            if opts.get('links', False) is True:
                print(colored('\n'.join(hrefs) , 'cyan'))
            if opts.get('dllinks', False) is True:
                grabbr.tools.queue_urls(hrefs, dbclient, opts)
            if opts.get('use_plugins', True) is True:
                try:
                    grabbr.tools.process_url(url_id, url, content, modules)
                except TypeError:
                    print(colored('No matching plugins were found', 'yellow'))
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

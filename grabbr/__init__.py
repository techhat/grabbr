# -*- coding: utf-8 -*-
# pylint: disable=too-many-nested-blocks,too-many-branches

'''
Basic functions for Grabbr
'''
# Python
import os
import sys
import time
import copy
import json
import pprint
import urllib

# 3rd party
import psutil
import yaml
from bs4 import BeautifulSoup
from salt.loader import LazyLoader
import salt.config

# Internal
import grabbr.db
import grabbr.api
import grabbr.tools
import grabbr.config
import grabbr.loader
from grabbr.version import __version__


def daemonize(opts, context):
    '''
    Spawn a new process
    '''
    out = grabbr.tools.Output(opts)
    try:
        pid = os.fork()
        if pid > 0:
            # exit first parent
            sys.exit(0)
    except OSError as exc:
        out.error('fork #1 failed: {} ({})'.format(exc.errno, exc))
        sys.exit(1)

    os.chdir('/')
    os.setsid()
    os.umask(0)

    # do second fork
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError as exc:
        out.error('fork #2 failed: {} ({})'.format(exc.errno, exc))
        sys.exit(1)

    grabbr.api.run(opts, context)


def run(run_opts=None):
    '''
    Run the program
    '''
    if run_opts is None:
        run_opts = {}

    opts, urls, parser = grabbr.config.load(run_opts)
    context = {}

    if opts.get('stop') or opts.get('hard_stop') or opts.get('abort'):
        open(opts['stop_file'], 'a').close()
        return

    if opts['daemon']:
        daemonize(opts, context)

    out = grabbr.tools.Output(opts)
    dbclient = grabbr.db.client(opts)

    if opts.get('version'):
        out.info(__version__)
        return

    if opts.get('show_opts'):
        out.info(pprint.pformat(opts))
        return

    if context.get('show_context'):
        out.info(pprint.pformat(context))
        return

    if opts.get('list_queue', False) is True:
        grabbr.db.list_queue(dbclient, opts)
        return

    if opts.get('pause'):
        grabbr.db.pause(dbclient, opts, opts['pause'])
        return

    if opts.get('unpause'):
        grabbr.db.unpause(dbclient, opts, opts['unpause'])
        return

    organizers = grabbr.loader.organize(opts, dbclient, context)
    organize_engine = None
    organize_fun = None
    if opts.get('search_organize'):
        organize_engine = opts['search_organize'][0]
        organize_fun = '.'.join([organize_engine, 'organize'])
        if organize_fun not in organizers:
            out.error('The {} organizer is not available'.format(organize_engine))

    if opts.get('search'):
        searches = grabbr.loader.search(opts, dbclient)
        engine = opts['search'][0]
        fun = '.'.join([engine, 'search'])
        if fun not in searches:
            out.error('The {} search engine is not available'.format(engine))
        else:
            for item in searches[fun]():
                if organize_engine is not None:
                    ret = organizers[organize_fun](item)
                    if ret:
                        out.info(pprint.pformat(ret))
                else:
                    out.info(item)
        return

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

    if opts.get('queue', False) is True:
        out.info('Adding item(s) to the queue')
        grabbr.tools.queue_urls(urls, dbclient, opts)
        return

    modules = grabbr.loader.plugin(opts, context, urls, dbclient)

    if opts['reprocess']:
        urls = grabbr.tools.reprocess_urls(urls, opts['reprocess'], dbclient)

    if not urls and opts['use_queue'] is True:
        grabbr.db.pop_dl_queue(dbclient, urls, opts)

    if not urls:
        if not opts['daemon']:
            parser.print_help()
            return

    # Write pid file
    pid = os.getpid()
    if not os.path.exists(opts['pid_file']):
        opts['already_running'] = False
        os.makedirs(os.path.dirname(opts['pid_file']), mode=0o700, exist_ok=True)
        with open(opts['pid_file'], 'w') as pfh:
            pfh.write(str(pid))
        pfh.close()

    # Write the metadata file
    metadata = {
        'id': opts['id'],
        'pid': pid,
        'api_addr': opts['api_addr'],
        'api_port': opts['api_port'],
    }
    with open(opts['meta_file'], 'w') as fh_:
        json.dump(metadata, fh_, indent=4)

    if not opts['already_running'] or opts.get('single') is True:
        level = 0
        # Use a while instead of for, because the list is expected to expand
        while True:
            url_uuid = None
            if opts['stop']:
                opts['http_api'].shutdown()
                break
            if os.path.exists(opts['stop_file']):
                out.warn('stop file found, exiting')
                os.remove(opts['stop_file'])
                opts['http_api'].shutdown()
                break
            if len(urls) < 1 and opts['use_queue'] is True:
                grabbr.db.pop_dl_queue(dbclient, urls, opts)
            if opts['urls']:
                grabbr.tools.queue_urls(opts['urls'], dbclient, opts)
                opts['urls'] = []
            try:
                url = urls.pop(0)
            except IndexError:
                if opts['daemon']:
                    time.sleep(.1)
                    continue
                else:
                    break
            if url.strip() == '':
                continue
            for mod in modules:
                if isinstance(url_uuid, int) and url_uuid == 0:
                    break
                if not mod.endswith('.pre_flight'):
                    continue
                url_uuid, url, content = modules[mod](url)
            if url_uuid is None:
                url_uuid, content = grabbr.tools.get_url(
                    url, dbclient=dbclient, opts=opts, context=context
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
                    grabbr.tools.process_url(url_uuid, url, content, modules)
                except TypeError:
                    out.warn('No matching plugins were found')
            if opts.get('queue_re'):
                grabbr.tools.queue_regexp(hrefs, opts['queue_re'], dbclient, opts)
            if opts.get('single') is True:
                break
        try:
            os.remove(opts['pid_file'])
        except FileNotFoundError:
            pass
        try:
            os.remove(opts['meta_file'])
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
                            if opts['daemon']:
                                out.error(
                                    'grabbr already running, or improperly stopped',
                                    force=True,
                                )
                                sys.exit(1)
                            else:
                                out.info('grabbr already running, adding item(s) to the queue')
            except IndexError:
                pass
        if verified_running is False:
            out.error('grabbr not found in process list, check /var/run/grabbr/pid', force=True)
        grabbr.tools.queue_urls(urls, dbclient, opts)

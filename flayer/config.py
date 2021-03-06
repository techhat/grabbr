# -*- coding: utf-8 -*-
'''
Config for Web Flayer
'''
# Python
import os
import argparse

# 3rd party
import yaml

# Internal
from flayer.version import __version__


def load(opts):
    '''
    Load configuration
    '''
    opts['already_running'] = True
    opts['parser_dir'] = []
    opts['search_dir'] = []
    opts['organize_dir'] = []
    opts['filter_dir'] = []

    parser = argparse.ArgumentParser()

    # Basic configuration
    parser.add_argument(
        '--config-file',
        dest='config_file',
        action='store',
        default='/etc/flayer/flayer',
        help='Default location for the config file',
    )
    parser.add_argument(
        '--run-dir',
        dest='run_dir',
        action='store',
        default=None,  # This is defined further down
        help='Default location for the PID file, stop file, etc',
    )
    parser.add_argument(
        '--parser-dir',
        dest='parser_dir',
        action='append',
        default=[],
        help='Location for flayer parser plugins',
    )
    parser.add_argument(
        '--search-dir',
        dest='search_dir',
        action='append',
        default=[],
        help='Location for flayer search plugins',
    )
    parser.add_argument(
        '--organize-dir',
        dest='organize_dir',
        action='append',
        default=[],
        help='Location for flayer organizer plugins',
    )
    parser.add_argument(
        '--filter-dir',
        dest='filter_dir',
        action='append',
        default=[],
        help='Location for flayer filter plugins',
    )
    parser.add_argument(
        '--salt-node',
        dest='salt_node',
        action='store',
        default='minion',
        help='master or minion, default minion',
    )

    # Control
    parser.add_argument(
        '--id',
        dest='id',
        action='store',
        help='The ID of the flay agent to control',
    )
    parser.add_argument(
        '--daemon',
        dest='daemon',
        action='store_true',
        default=False,
        help='Start as a background service',
    )
    parser.add_argument(
        '--stop',
        dest='stop',
        action='store_true',
        help='Stop after the current download',
    )
    parser.add_argument(
        '--hard-stop',
        dest='hard_stop',
        action='store_true',
        help='Stop, delete and requeue current download, then exit',
    )
    parser.add_argument(
        '--abort',
        dest='abort',
        action='store_true',
        help='Stop, delete current download, exit',
    )
    parser.add_argument(
        '--api-addr',
        dest='api_addr',
        action='store',
        default='127.0.0.1',
        help='The host address of the API',
    )
    parser.add_argument(
        '--api-port',
        dest='api_port',
        action='store',
        default=42424,
        help='The host port of the API',
    )
    parser.add_argument(
        '--salt-events',
        dest='salt_events',
        action='store_true',
        default=False,
        help="Whether to fire events on Salt's event bus",
    )

    # Downloading
    parser.add_argument(
        '-f', '--force',
        dest='force',
        action='store_true',
        default=False,
        help='Force flayer to re-download the URL(s)',
    )
    parser.add_argument(
        '--overwrite',
        dest='overwrite',
        action='store_true',
        default=False,
        help='Force flayer to overwrite an existing file',
    )
    parser.add_argument(
        '-w', '--wait',
        dest='wait',
        action='store',
        default=0,
        help='Amount of time to wait between requests',
    )
    parser.add_argument(
        '--domain-wait',
        dest='domain_wait',
        action='store',
        default=0,
        help='Amount of time to wait between requests, per domain',
    )
    parser.add_argument(
        '--random-wait',
        dest='random_wait',
        action='store_true',
        default=False,
        help='Random wait (default from 1 to 10 seconds) between requests',
    )
    parser.add_argument(
        '-s', '--single',
        dest='single',
        action='store_true',
        default=False,
        help='Process a single URL, separate from any other current processes',
    )
    parser.add_argument(
        '-S', '--server-response',
        dest='include_headers',
        action='store_true',
        default=False,
        help='Whether to display (pprint) the headers when requesting a URL',
    )
    parser.add_argument(
        '-i', '--input-file',
        dest='input_file',
        action='store',
        help='A file containing a list of links to download',
    )
    parser.add_argument(
        '-H', '--header',
        dest='headers',
        action='append',
        help='A header line to be included with the request',
    )
    parser.add_argument(
        '-d', '--data',
        dest='data',
        action='store',
        default=None,
        help='Data to be POSTed in the request',
    )
    parser.add_argument(
        '--use-queue',
        dest='use_queue',
        action='store_true',
        default=True,
        help="Process the items in the download queue (default)",
    )
    parser.add_argument(
        '--no-queue',
        dest='use_queue',
        action='store_false',
        help="Don't process any of the items in the download queue",
    )
    parser.add_argument(
        '--queue',
        dest='queue',
        action='store_true',
        default=False,
        help='Add the URLs to the download queue and exit',
    )
    parser.add_argument(
        '-p', '--reprocess',
        dest='reprocess',
        action='store',
        default=None,
        nargs='+',
        help='Reprocess URLs matching a postgresql-style regexp',
    )
    parser.add_argument(
        '--no-db-cache',
        dest='no_db_cache',
        action='store_true',
        default=False,
        help="Don't cache the target in the database",
    )
    parser.add_argument(
        '--queue-links',
        dest='queuelinks',
        action='store_true',
        default=False,
        help='Add the absolute URLs from the page to the download queue',
    )
    parser.add_argument(
        '--queue-re', '--queue-regex', '--queue-regexp',
        dest='queue_re',
        action='store',
        default=None,
        help='Add the absolute URLs matching the regexp to the download queue',
    )
    parser.add_argument(
        '--search-src',
        dest='search_src',
        action='store_true',
        default=False,
        help='Search tags with src attribute, in addition to hrefs',
    )
    parser.add_argument(
        '-x', '--force-directories',
        dest='force_directories',
        action='store_true',
        default=False,
        help='When downloading, force a directory structure',
    )
    parser.add_argument(
        '--save-path',
        dest='save_path',
        action='store',
        default=None,
        help='When downloading, use this path as the download root',
    )
    parser.add_argument(
        '--save-html',
        dest='save_html',
        action='store_true',
        default=True,
        help='When downloading, save HTML as well as binary files',
    )
    parser.add_argument(
        '--no-save-html',
        dest='save_html',
        action='store_false',
        help='When downloading (with --save-path), do NOT save HTML files',
    )
    parser.add_argument(
        '--use-parsers',
        dest='use_parsers',
        action='store_true',
        default=True,
        help="Download the URL, using the parsers to process it (default)",
    )
    parser.add_argument(
        '--no-parsers',
        dest='use_parsers',
        action='store_false',
        help="Just download the URL; don't call any parsers to process it",
    )
    parser.add_argument(
        '--user-agent',
        dest='user_agent',
        action='store',
        default='flay {}'.format(__version__),
        help='User agent to report to the server',
    )
    parser.add_argument(
        '--refresh-interval',
        dest='refresh_interval',
        action='store',
        help="Auto-populate the paused_until field in the download queue",
    )
    parser.add_argument(
        '--pause',
        dest='pause',
        action='store',
        nargs='+',
        help='Name of a queued URL to pause',
    )
    parser.add_argument(
        '--unpause',
        dest='unpause',
        action='store',
        nargs='+',
        help='Name of a queued URL to unpause',
    )
    parser.add_argument(
        '--verify',
        dest='verify',
        action='store',
        default=True,
        help='Set to False to ignore SSL errors',
    )

    # Templating
    parser.add_argument(
        '--rename', '--rename-template',
        dest='rename_template',
        action='store',
        help='A template to use for renaming downloads',
    )
    parser.add_argument(
        '--rename-count-start',
        dest='rename_count_start',
        action='store',
        default=0,
        help='Number to start {count} at',
    )
    parser.add_argument(
        '--rename-count-padding',
        dest='rename_count_padding',
        action='store',
        default=0,
        help='Zero-padding to be used for {count}',
    )

    # Recursion
    parser.add_argument(
        '--level',
        dest='level',
        action='store',
        default=0,
        help='Specify recursion maximum depth level depth',
    )
    parser.add_argument(
        '--span-hosts',
        dest='span_hosts',
        action='store_true',
        default=False,
        help='Enable spanning across hosts when doing recursive retrieving',
    )

    # Built-in tools
    parser.add_argument(
        '--search',
        dest='search',
        action='store',
        nargs='+',
        help='Perform a search, using the specified engine',
    )
    parser.add_argument(
        '--search-limit',
        dest='search_limit',
        action='store',
        default=30,
        help='Maximum number of results for searches',
    )
    parser.add_argument(
        '--search-organize',
        dest='search_organize',
        action='store',
        nargs='+',
        help='Send --search results to a organizer engine',
    )

    # Informational
    parser.add_argument(
        '--source',
        dest='source',
        action='store_true',
        default=False,
        help="Display the URL's source",
    )
    parser.add_argument(
        '--render', '--dump',
        dest='render',
        action='store_true',
        default=False,
        help='Render the content',
    )
    parser.add_argument(
        '--links',
        dest='links',
        action='store_true',
        default=False,
        help='Display by a list of the absolute URLs in the page',
    )
    parser.add_argument(
        '-l', '--list-queue',
        dest='list_queue',
        action='store_true',
        default=False,
        help='List the remaining URLS in the download queue',
    )
    parser.add_argument(
        '--show-metadata', '--show-url-metadata',
        dest='show_url_metadata',
        action='append',
        help='Show any metadata for the given URL',
    )
    parser.add_argument(
        '--show-opts',
        dest='show_opts',
        action='store_true',
        default=False,
        help='Return a copy of opts for this instance',
    )
    parser.add_argument(
        '--show-context',
        dest='show_context',
        action='store_true',
        default=False,
        help='Return a copy of the context for this instance',
    )
    parser.add_argument(
        '-v', '--verbose',
        dest='verbose',
        action='store_true',
        default=False,
        help="Display more information about what's going on",
    )
    parser.add_argument(
        '--version',
        dest='version',
        action='store_true',
        help='Display the version and exit',
    )
    parser.add_argument(dest='urls', nargs=argparse.REMAINDER)

    cli_opts = parser.parse_args().__dict__

    # Load in the config file
    with open(cli_opts['config_file'], 'r') as ifh:
        opts.update(yaml.safe_load(ifh.read()))

    # Preserve the ID from being overwritten by "None"
    id_ = opts.get('id')
    if cli_opts.get('id') is None:
        cli_opts['id'] = id_

    cli_opts['parser_dir'].extend(opts['parser_dir'])
    cli_opts['search_dir'].extend(opts['search_dir'])
    cli_opts['organize_dir'].extend(opts['organize_dir'])
    cli_opts['filter_dir'].extend(opts['filter_dir'])

    # Override with any environment variables
    for param in set(list(opts) + list(cli_opts)):
        env_var = 'FLAYER_{}'.format(param.upper())
        if env_var in os.environ:
            cli_opts[param] = os.environ[env_var]

    # Lay down CLI opts on top of config file opts and environment
    opts.update(cli_opts)

    # parser_dir is an array
    if not opts['parser_dir']:
        opts['parser_dir'] = ['/srv/flayer/plugins/parsers']

    # search_dir is an array
    if not opts['search_dir']:
        opts['search_dir'] = ['/srv/flayer/plugins/searchers']

    # organize_dir is an array
    if not opts['organize_dir']:
        opts['organize_dir'] = ['/srv/flayer/plugins/organizers']

    # filter_dir is an array
    if not opts['filter_dir']:
        opts['filter_dir'] = ['/srv/flayer/plugins/filters']

    # Set the verify argument for requests
    if opts['verify'] in ('False', False):
        opts['verify'] = False

    # Set up any headers for the agent
    if opts['headers'] is None:
        opts['headers'] = []
    headers = {}
    for header in list(opts['headers']):
        if isinstance(header, dict):
            headers[header] = opts['headers'][header]
        else:
            headers[header.split(':')[0]] = ':'.join(header.split(':')[1:]).strip()
    opts['headers'] = headers

    if opts['user_agent']:
        opts['headers']['User-Agent'] = opts['user_agent']

    if opts.get('data'):
        opts['method'] = 'POST'
    else:
        opts['method'] = 'GET'

    urls = opts['urls']

    if not opts.get('id'):
        opts['id'] = 'unknown'

    if opts.get('run_dir') is None:
        opts['run_dir'] = os.path.join('/var/run/flayer', opts['id'])

    opts['pid_file'] = os.path.join(opts['run_dir'], 'pid')
    opts['stop_file'] = os.path.join(opts['run_dir'], 'stop')
    opts['meta_file'] = os.path.join(opts['run_dir'], 'meta')

    return opts, urls, parser

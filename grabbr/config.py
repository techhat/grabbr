# -*- coding: utf-8 -*-
'''
Config for Grabbr
'''
# Python
import sys
import argparse

# 3rd party
import yaml


def load(opts):
    '''
    Load configuration
    '''
    opts['already_running'] = True
    opts['module_dir'] = []

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--config-file',
        dest='config_file',
        action='store',
        default='/etc/grabbr/grabbr',
        help='Default location for the config file',
    )
    parser.add_argument(
        '--pid-file',
        dest='pid_file',
        action='store',
        default='/var/run/grabbr/pid',
        help='Default location for the PID file',
    )
    parser.add_argument(
        '--module-dir',
        dest='module_dir',
        action='append',
        help='Location for grabbr plugins',
    )
    parser.add_argument(
        '-f', '--force',
        dest='force',
        action='store_true',
        default=False,
        help='Force grabbr to re-download the URL(s)',
    )
    parser.add_argument(
        '-w', '--wait',
        dest='wait',
        action='store',
        default=0,
        help='Amount of time to wait between requests',
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
        '-v', '--verbose',
        dest='verbose',
        action='store_true',
        default=False,
        help="Display more information about what's going on",
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
        '-l', '--list-queue',
        dest='list_queue',
        action='store_true',
        default=False,
        help='List the remaining URLS in the download queue',
    )
    parser.add_argument(
        '-p', '--reprocess',
        dest='reprocess',
        action='store',
        default=None,
        nargs='+',
        help='Reprocess a URL using a postgresql-style regexp',
    )
    parser.add_argument(
        '--no-db-cache',
        dest='no_db_cache',
        action='store_true',
        default=False,
        help="Don't cache the target in the database",
    )
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
    parser.add_argument(
        '--use-plugins',
        dest='use_plugins',
        action='store_true',
        default=True,
        help="Just download the URL; don't call any plugins to process it",
    )
    parser.add_argument(
        '--no-plugins',
        dest='use_plugins',
        action='store_false',
        help="Just download the URL; don't call any plugins to process it",
    )
    parser.add_argument(
        '--user-agent',
        dest='user_agent',
        action='store',
        default=('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/536.11 '
                 '(KHTML, like Gecko) Chrome/20.0.1132.47 Safari/536.11'),
        help="Just download the URL; don't call any plugins to process it",
    )
    parser.add_argument(dest='urls', nargs=argparse.REMAINDER)

    if len(sys.argv) < 2:
        parser.print_help()

    cli_opts = parser.parse_args().__dict__

    # Load in the config file
    with open(cli_opts['config_file'], 'r') as ifh:
        opts.update(yaml.safe_load(ifh.read()))

    # Lay down CLI opts on top of config file opts
    opts.update(cli_opts)

    # module_dir is an array
    if not opts['module_dir']:
        opts['module_dir'] = ['/srv/grabbr-plugins']

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

    return opts, urls

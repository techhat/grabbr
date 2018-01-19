# -*- coding: utf-8 -*-
'''
Config for Grabbr
'''
# Python
import os
import sys
import argparse

# 3rd party
import yaml


def load():
    '''
    Load configuration
    '''
    opts = {
        'pid_file': '/var/run/grabbr/pid',
        'module_dir': '/srv/grabbr-plugins',
        'force': False,
        'random_wait': False,
        'headers': {
            'User-Agent': ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/536.11 '
                           '(KHTML, like Gecko) Chrome/20.0.1132.47 Safari/536.11'),
        },
        'already_running': True,
    }

    with open('/etc/grabbr/grabbr', 'r') as ifh:
        opts.update(yaml.safe_load(ifh.read()))

    if not os.path.exists(opts['module_dir']):
        os.makedirs(opts['module_dir'])

    parser = argparse.ArgumentParser()
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
    )
    parser.add_argument(
        '-s', '--single',
        dest='single',
        action='store_true',
        default=False,
        help='Process a single URL, separate from any other current processes',
    )
    parser.add_argument(
        '-i', '--include',
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
        '--dl-links', '--download-links',
        dest='dllinks',
        action='store_true',
        default=False,
        help='Add the absolute URLs from the page to the download queue',
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
        '--no-plugins',
        dest='no_plugins',
        action='store_true',
        default=False,
        help="Just download the URL; don't call any plugins to process it",
    )
    parser.add_argument(dest='urls', nargs=argparse.REMAINDER)

    if len(sys.argv) < 2:
        parser.print_help()

    opts.update(parser.parse_args().__dict__)
    urls = opts['urls']

    return opts, urls

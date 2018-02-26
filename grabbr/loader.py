# -*- coding: utf-8 -*-
'''
Basic functions for Grabbr
'''
# 3rd party
from salt.loader import LazyLoader
import salt.config


def parser(opts, context, urls, dbclient):
    '''
    Load spider modules
    '''
    master_opts = salt.config.master_config('/etc/salt/master')
    minion_opts = salt.config.minion_config('/etc/salt/minion')
    return LazyLoader(
        opts['parser_dir'],
        minion_opts,
        tag=u'grabbr/parser',
        pack={
            u'__master_opts__': master_opts,
            u'__minion_opts__': minion_opts,
            u'__opts__': opts,
            u'__context__': context,
            u'__urls__': urls,
            u'__dbclient__': dbclient,
        },
    )


def search(opts, dbclient):
    '''
    Load search modules
    '''
    return LazyLoader(
        opts['search_dir'],
        {},
        tag=u'grabbr/search',
        pack={
            u'__opts__': opts,
            u'__dbclient__': dbclient,
        },
    )


def organize(opts, dbclient, context):
    '''
    Load organizer modules
    '''
    return LazyLoader(
        opts['organize_dir'],
        {},
        tag=u'grabbr/organize',
        pack={
            u'__opts__': opts,
            u'__dbclient__': dbclient,
            u'__context__': context,
        },
    )

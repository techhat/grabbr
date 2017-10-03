# -*- coding: utf-8 -*-
'''
Basic functions for Grabbr
'''
from salt.loader import LazyLoader
import salt.config


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

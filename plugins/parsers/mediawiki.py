# -*- coding: utf-8 -*-
'''
Web Flayer module for wikipedia

Grabs the raw data from a wikipedia page and dump it to a file, with the page's
title as the filename.

``/etc/flayer/flayer`` should have a ``wikipedia_cache_path`` specified to
download files to. However, if that is not specified, the file will be stored
in the current working directory.

Please note that this module exists solely as an example, and should not be
used to abuse the Wikipedia service.

If you like Wikipedia, please consider donating to help keep it alive. You can
donate at https://donate.wikimedia.org/.
'''
import requests
import flayer.tools


def func_map(url):
    '''
    Function map
    '''
    if 'wikipedia' in url:
        return wikipedia_raw
    return None


def wikipedia_raw(url_uuid, url, content):
    '''
    Grab raw wikipedia data
    '''
    cache_path = __opts__.get('wikipedia_cache_path', '.')
    title = url.split('?')[0].split('/')[-1]
    file_name = '{}/{}'.format(cache_path, title)
    req = requests.get(url, stream=True, params={'action': 'raw'})
    flayer.tools.status(
        req,
        url,
        url_uuid,
        file_name,
        dbclient=__dbclient__,
        opts=__opts__,
        context=__context__,
    )

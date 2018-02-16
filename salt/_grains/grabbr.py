# -*- coding: utf-8 -*-
'''
Salt grains for Grabbr
'''
import salt.utils.http


def __virtual__():
    '''
    Only requires Salt
    '''
    return True


def process():
    '''
    Return the ID of this instance of grabbr
    '''
    opts = _query(show_opts=True).get('dict', '')
    ret = {
        'grabbr_id': opts.get('id', 'unknown'),
    }
    return ret


def _query(**params):
    '''
    Send a command to the API
    '''
    api_host = __opts__.get('grabbr_host', '127.0.0.1')
    api_port = __opts__.get('grabbr_port', 42424)

    url = 'http://{0}:{1}'.format(api_host, api_port)

    return salt.utils.http.query(
        url,
        params=params,
        decode=True,
        decode_type='json',
    )

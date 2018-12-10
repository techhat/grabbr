# -*- coding: utf-8 -*-
'''
Logging module for Web Flayer
'''
import os
import logging


def setup():
    '''
    Setup the logs
    '''
    handler = logging.StreamHandler()
    formatter = logging.BASIC_FORMAT
    handler.setFormatter(formatter)
    logging.basicConfig(level=os.environ.get('FLAYER_LOGLEVEL', 'INFO'))

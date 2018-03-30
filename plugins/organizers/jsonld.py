# -*- coding: utf-8 -*-
'''
Web Flayer organizer module for JSON-LD
'''
import json
from bs4 import BeautifulSoup
import flayer.tools


def organize(url):
    '''
    Decide whether a page is using JSON-LD
    '''
    url_uuid, content = flayer.tools.get_url(
        url, dbclient=__dbclient__, opts=__opts__, context=__context__
    )

    types = set()
    soup = BeautifulSoup(content, 'html.parser')
    for tag in soup.find_all('script', attrs={'type': 'application/ld+json'}):
        for data in tag:
            try:
                script = json.loads(data)
                types.add(script['@type'])
            except json.decoder.JSONDecodeError as exc:
                types.add(exc)

    return list(types)

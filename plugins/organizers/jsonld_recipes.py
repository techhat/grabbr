# -*- coding: utf-8 -*-
'''
Grabbr organizer module for JSON-LD Recipes

In order to use this plugin, a ``jsonld_domains`` table needs to be created:

.. code-block:: sql

    create table jsonld_domains (domain text unique);
'''
# Python
import json
import urllib

# 3rd party
import requests
from bs4 import BeautifulSoup

# Internal
import grabbr.tools


def organize(url):
    '''
    Decide whether a page has an JSON-LD recipe
    '''
    out = grabbr.tools.Output(__opts__)
    cur = __dbclient__.cursor()
    insert_sql = '''
        INSERT INTO jsonld_domains (domain)
        VALUES (%s)
        ON CONFLICT DO NOTHING
    '''

    try:
        req = requests.get(url)
        content = req.text
    except requests.exceptions.MissingSchema as exc:
        return []
    except requests.exceptions.ConnectionError:
        return []
    except requests.exceptions.SSLError:
        out.warn('SSL Error with {}, trying again without verification'.format(url))
        req = requests.get(url, verify=False)
        content = req.text

    soup = BeautifulSoup(content, 'html.parser')
    if 'jsonld_domains' not in __context__:
        __context__['jsonld_domains'] = []
    for tag in soup.find_all('script', attrs={'type': 'application/ld+json'}):
        for data in tag:
            try:
                script = json.loads(data)
                try:
                    script_type = script['@type'].lower()
                except (AttributeError, KeyError, TypeError):
                    return []
                if script_type == 'recipe':
                    url_comps = urllib.parse.urlparse(url)
                    netloc = url_comps[1].split(':')[0]
                    cur.execute(insert_sql, [netloc])
                    __dbclient__.commit()
                    if netloc not in __context__['jsonld_domains']:
                        __context__['jsonld_domains'].append(netloc)
                    grabbr.tools.queue_urls(url, __dbclient__, __opts__)
                    return 'Queueing for download: {}'.format(url)
            except json.decoder.JSONDecodeError as exc:
                pass
    return []

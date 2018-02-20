# -*- coding: utf-8 -*-
'''
Grabbr search module for Wikipedia
'''
import html
import urllib
import requests
from bs4 import BeautifulSoup
import grabbr.tools


def search(opts):
    '''
    Perform a search in Google
    '''
    query = opts['search'][1].replace(' ', '+')
    url = ('https://en.wikipedia.org/w/index.php?search={}'
           '&title=Special:Search&profile=default&fulltext=1').format(query)
    req = requests.get(url)

    soup = BeautifulSoup(req.text, 'html.parser')
    urls = set()
    for tag in soup.find_all('a'):
        try:
            link = tag.attrs['href']
        except KeyError:
            continue
        if 'index.php' in link:
            continue
        if 'Portal:' in link:
            continue
        if 'Help:' in link:
            continue
        if 'Special:' in link:
            continue
        if 'Wikipedia:' in link:
            continue
        if '/wiki/' not in link:
            continue
        if link.startswith('/wiki/'):
            link = 'https://en.wikipedia.org' + link
        if 'wikipedia.org' not in link:
            continue
        urls.add(link)

    return list(urls)

# -*- coding: utf-8 -*-
'''
Grabbr module for JSON-LD Recipes

In order to use this plugin, a ``jsonld_domains`` table needs to be created:

.. code-block:: sql

    create table jsonld_domains (domain text unique);
'''
import os
import json
import html
import grabbr.tools
from bs4 import BeautifulSoup


def func_map(url):
    '''
    Function map
    '''
    domains = __context__.get('jsonld_domains')
    if domains is None:
        domains = []
        cur = __dbclient__.cursor()
        cur.execute('SELECT domain FROM jsonld_domains')
        for row in cur.fetchall():
            domains.append(row[0])
        __context__['jsonld_domains'] = domains

    for domain in domains:
        if domain in url:
            return parse_page
    return None


def parse_page(url_uuid, url, content):
    '''
    Route a page with primary data stored in json
    '''
    soup = BeautifulSoup(content, 'html.parser')
    for tag in soup.find_all('script', attrs={'type': 'application/ld+json'}):
        for content in tag:
            script = json.loads(content)
            if script['@type'].lower() == 'recipe':
                parse_recipe(url, content, script)
            if script['@type'].lower() == 'itemlist':
                parse_list(script['itemListElement'])


def parse_list(list_element):
    '''
    Parse an ItemList entity
    '''
    urls = []
    for item in list_element:
        urls.append(item['url'])
    grabbr.tools.queue_urls(urls, __dbclient__, __opts__)


def parse_recipe(url, content, recipe_dict):
    '''
    Download and parse a recipe
    '''
    cache_path = __opts__.get('recipe_cache_path', '')

    text_data = '{}\n\n'.format(recipe_dict['name'])
    for item in recipe_dict['recipeIngredient']:
        text_data += '{}\n'.format(item)
    text_data += '\n'
    if isinstance(recipe_dict.get('recipeInstructions'), str):
        recipe_dict['recipeInstructions'] = [recipe_dict['recipeInstructions']]
    elif recipe_dict.get('recipeInstructions') is None:
        recipe_dict['recipeInstructions'] = []
    for item in recipe_dict['recipeInstructions']:
        text_data += '{}\n'.format(html.unescape(item))

    html_path = os.path.join(cache_path, 'site', url.split('://')[1])
    html_file = os.path.join(html_path, 'index.html')
    try:
        os.makedirs(html_path, mode=0o0755)
    except FileExistsError:
        pass
    with open(html_file, 'w') as hof:
        hof.write(content)

    json_path = os.path.join(cache_path, 'site-json', url.split('://')[1])
    json_file = os.path.join(json_path, 'index.json')
    try:
        os.makedirs(json_path, mode=0o0755)
    except FileExistsError:
        pass
    with open(json_file, 'w') as hof:
        json.dump(recipe_dict, hof, indent=4)

    txt_path = os.path.join(cache_path, 'site-txt', url.split('://')[1])
    txt_file = os.path.join(txt_path, 'index.txt')
    try:
        os.makedirs(txt_path, mode=0o0755)
    except FileExistsError:
        pass
    with open(txt_file, 'w') as hof:
        hof.write(text_data)

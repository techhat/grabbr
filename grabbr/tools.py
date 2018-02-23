# -*- coding: utf-8 -*-
'''
Tools for Grabbr
'''
# Python
import os
import re
import sys
import time
import random
import pprint
import urllib

# 3rd party
import requests
from termcolor import colored
import psycopg2
from psycopg2.extras import Json
from bs4 import BeautifulSoup


class Output(object):
    '''
    Used for outputting data
    '''
    def __init__(self, opts):
        '''
        Initialize
        '''
        self.opts = opts

    def action(self, msg, force=False):
        '''
        Something is currently happening
        '''
        if not self.opts['daemon'] or force is True:
            print(colored(msg, self.opts.get('action_color', 'green')))

    def info(self, msg, force=False):
        '''
        Informational only
        '''
        if not self.opts['daemon'] or force is True:
            print(colored(msg, self.opts.get('info_color', 'cyan')))

    def warn(self, msg, force=False):
        '''
        Something is possibly wrong, but not enough to stop running
        '''
        if not self.opts['daemon'] or force is True:
            print(colored(msg, self.opts.get('warn_color', 'yellow')))

    def error(self, msg, force=False):
        '''
        Something is wrong enough to halt execution
        '''
        if not self.opts['daemon'] or force is True:
            print(colored(msg, self.opts.get('error_color', 'red'), attrs=['bold']))


def process_url(url_uuid, url, content, parsers):
    '''
    Process a URL
    '''
    fun = None
    for mod in parsers:
        if fun is not None:
            break
        if not mod.endswith('.func_map'):
            continue
        fun = parsers[mod](url)
    fun(url_uuid, url, content)


def get_url(
        url,
        parent=None,
        referer=None,
        dbclient=None,
        client=requests,
        opts=None,
        context=None,
    ):
    '''
    Download a URL (if necessary) and store it
    '''
    out = Output(opts)

    headers = opts['headers'].copy()
    data = opts.get('data', None)

    if referer:
        headers['referer'] = referer

    wait = 0
    if opts.get('no_db_cache') is True:
        # Skip all the DB stuff and just download the URL
        req = client.request(opts['method'], url, headers=headers, data=data)
        if opts.get('include_headers') is True:
            out.info(pprint.pformat(dict(req.headers)))
        content = req.text
        if opts['random_wait'] is True:
            wait = opts.get('wait', 10)
            time.sleep(random.randrange(1, wait))
        return 0, content

    cur = dbclient.cursor()
    exists = False

    # Check for URL in DB
    cur.execute('''
        SELECT uuid, url, last_retrieved
        FROM urls
        WHERE url = %s
    ''', [url])

    if cur.rowcount < 1:
        # URL has never been retrieved
        cur.execute('''
            INSERT INTO urls
            (url) VALUES (%s)
            RETURNING uuid
        ''', [url])
        dbclient.commit()
        url_uuid = cur.fetchone()[0]
        out.action('{} has not been retrieved before, new UUID is {}'.format(url, url_uuid))
    else:
        # URL has been retrieved, get its UUID
        url_uuid = cur.fetchone()[0]
        out.warn('{} exists, UUID is {}'.format(url, url_uuid))
        exists = True

    # Save referer relationships
    if parent:
        try:
            cur.execute('''
                INSERT INTO referers
                (url_uuid, referer_uuid)
                VALUES
                (%s, %s)
            ''', [url_uuid, parent])
            dbclient.commit()
        except psycopg2.IntegrityError:
            # This relationship already exists
            dbclient.rollback()

    if opts['force_directories'] and not opts['save_path']:
        opts['save_path'] = '.'

    # Check for content
    cur.execute('''
        SELECT data, uuid
        FROM content
        WHERE url_uuid = %s
        ORDER BY retrieved
        LIMIT 1
    ''', [url_uuid])
    if cur.rowcount < 1:
        if opts['save_path']:
            req = client.request(opts['method'], url, headers=headers, data=data, stream=True)
            content, req_headers = _save_path(url, url_uuid, req, wait, opts, context, dbclient)
        else:
            req = client.request(opts['method'], url, headers=headers, data=data)
            content = req.text
            req_headers = req.headers
        if opts.get('include_headers') is True:
            out.info(pprint.pformat(dict(req_headers)))
        if content:
            cur.execute('''
                    INSERT INTO content
                    (url_uuid, data) VALUES (%s, %s)
                ''',
                [
                    url_uuid,
                    Json({'content': content})
                ]
            )
            dbclient.commit()
    else:
        if opts['force'] is True:
            row_id = cur.fetchone()[1]
            if opts['save_path']:
                req = client.request(opts['method'], url, headers=headers, data=data, stream=True)
                content, req_headers = _save_path(url, url_uuid, req, wait, opts, context, dbclient)
            else:
                req = client.request(opts['method'], url, headers=headers, data=data)
                content = req.text
                req_headers = req.headers
            if opts.get('include_headers') is True:
                out.info(pprint.pformat(dict(req_headers)))
            if content:
                cur.execute('''
                        UPDATE content
                        SET url_uuid = %s, data = %s
                        WHERE uuid = %s
                    ''',
                    [
                        url_uuid,
                        Json({'content': content}),
                        row_id
                    ]
                )
                dbclient.commit()
        else:
            content = cur.fetchone()[0]['content']

    if exists is False:
        if opts['random_wait'] is True:
            wait = opts.get('wait', 10)
            time.sleep(random.randrange(1, wait))
    return url_uuid, content


def _save_path(url, url_uuid, req, wait, opts, context, dbclient):
    '''
    Save the URL to a path
    '''
    urlcomps = urllib.parse.urlparse(url)
    if opts['force_directories']:
        newpath = urlcomps[2].lstrip('/')
        file_name = os.path.join(opts['save_path'], urlcomps[1], newpath)
    else:
        file_name = os.path.join(opts['save_path'], urlcomps[2].split('/')[-1])
    return status(req, url, url_uuid, file_name, wait, opts, context, dbclient)


def status(
        req,
        media_url,
        url_uuid,
        file_name,
        wait=0,
        opts=None,
        context=None,
        dbclient=None,
    ):
    '''
    Show status of the download
    '''
    out = Output(opts)

    if opts is None:
        opts = {}

    if context is None:
        context = {}

    file_name = _rename(media_url, file_name, opts)

    cache_dir = '/'.join(file_name.split('/')[:-1])
    try:
        os.makedirs(cache_dir, mode=0o0755, exist_ok=True)
    except PermissionError as exc:
        out.error('Cannot create directory {}: {}'.format(cache_dir, exc))

    is_text = False
    req_headers = req.headers
    for header in list(req_headers):
        if header.lower().startswith('content-type'):
            if req_headers[header].startswith('text'):
                is_text = True
    content = ''

    cur = dbclient.cursor()
    agent_id = opts.get('id', 'unknown')
    cur.execute(
        'INSERT INTO active_dl (url_uuid, started_by) VALUES (%s, %s)',
        [url_uuid, agent_id]
    )

    cur.execute('SELECT url FROM urls WHERE uuid = %s', [url_uuid])
    root_url = cur.fetchone()[0]

    out.action('Downloading: {}'.format(media_url))
    if os.path.exists(file_name):
        out.warn('... {} exists, skipping'.format(file_name))
        return None, {}
    if not opts['daemon']:
        sys.stdout.write(colored('...Saving to: ', 'green'))
    out.info(file_name)
    buffer_size = 4096
    total = int(req.headers.get('Content-Length', 0))
    count = 0
    try:
        point = int(total / 100)
        #increment = int(total / buffer_size)
    except ZeroDivisionError:
        out.error('Divide by zero error, status not available')
        point = 0
        #increment = 0
    start_time = time.time()
    last_time = time.time()
    delay_blocks = 0
    delay_count = 0

    context['dl_data'] = {
        'url': root_url,
        'media_url': media_url,
        'url_uuid': url_uuid,
        'bytes_total': '',
        'bytes_elapsed': '',
        'time_total': '',
        'time_left': '',
        'kbsec': 0,
    }
    with open(file_name, 'wb') as fhp:
        #old_time = time.time()
        for block in req.iter_content(buffer_size):
            if opts.get('hard_stop'):
                queue_urls([media_url], dbclient, opts)
                break
            if opts.get('abort'):
                break
            if is_text is True:
                content += str(block)
            fhp.write(block)
            count += buffer_size
            delay_blocks += buffer_size
            delay_count += 1
            #old_time = time.time()
            time_delay = time.time() - last_time
            if time_delay >= float(1):
                last_time = time.time()
                try:
                    blocks_left = int((total - count) / buffer_size)
                except ZeroDivisionError:
                    blocks_left = 0
                kbsec = (buffer_size / 1024) * delay_count
                try:
                    seconds_left = ((blocks_left * buffer_size) / 1024) / kbsec
                except ZeroDivisionError:
                    seconds_left = 0
                minutes_left = int(seconds_left / 60)
                minsecs_left = seconds_left % 60
                time_left = '%d:%02d' % (minutes_left, minsecs_left)
                seconds_elapsed = time.time() - start_time
                seconds_total = seconds_elapsed + seconds_left
                minutes_total = int(seconds_total / 60)
                minsecs_total = int(seconds_total % 60)
                time_total = '%d:%02d' % (minutes_total, minsecs_total)
                try:
                    percent = int(count / point)
                except ZeroDivisionError:
                    percent = 0
                context['dl_data']['bytes_total']   = total
                context['dl_data']['bytes_elapsed'] = count
                context['dl_data']['time_total']    = time_total
                context['dl_data']['time_left']     = time_left
                context['dl_data']['kbsec']         = kbsec
                if not opts['daemon']:
                    sys.stdout.write('\x1b[2K\r')
                    sys.stdout.write(
                        colored('Total size is {} '.format(sizeof_fmt(total)), 'green'))
                    sys.stdout.write(colored('({} bytes), '.format(total), 'green'))
                    sys.stdout.write(colored('{}%, '.format(str(percent)), 'cyan'))
                    sys.stdout.write(colored(kbsec, 'cyan'))
                    sys.stdout.write(colored(' KiB/s, ', 'cyan'))
                    sys.stdout.write(colored('{}/{} left'.format(time_left, time_total), 'cyan'))
                    sys.stdout.flush()
                delay_blocks = 0
                delay_count = 0

    del context['dl_data']

    if opts.get('hard_stop') or opts.get('abort'):
        os.remove(file_name)

    if is_text is True and opts.get('save_html', True) is False:
        os.remove(file_name)

    if not content:
        content = None

    cur.execute('DELETE FROM active_dl WHERE url_uuid = %s', [url_uuid])

    if not opts['daemon']:
        print()
    time.sleep(wait)

    return content, req_headers


def sizeof_fmt(num, suffix='B'):
    '''
    Show human-readable sizes
    '''
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s " % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s " % (num, 'Yi', suffix)


def dbsave_media(cur, media_url, url_uuid, file_name, dbclient):
    '''
    Save a media item into the database, once it's been downloaded

    cur: Database cursor

    media_url: The URL of the image/video that was downloaded

    url_uuid: The UUID of the parent of the media_url

    file_name: The place where the media_url was downloaded to
    '''
    try:
        cur.execute('''
            INSERT INTO urls (url) values (%s) RETURNING uuid
        ''', [media_url])
        dbclient.commit()
        new_id = cur.fetchone()[0]
    except psycopg2.IntegrityError:
        # This relationship already exists
        dbclient.rollback()
        cur.execute('''
            SELECT uuid FROM urls WHERE url = %s
        ''', [media_url])
        new_id = cur.fetchone()[0]

    try:
        cur.execute('''
            INSERT INTO referers (url_uuid, referer_uuid) values (%s, %s)
        ''', [new_id, url_uuid])
        dbclient.commit()
    except psycopg2.IntegrityError:
        # This relationship already exists
        dbclient.rollback()

    cur.execute('''
        SELECT COUNT(*) FROM content WHERE url_uuid = %s
    ''', [new_id])
    if cur.fetchone()[0] < 1:
        cur.execute('''
            INSERT INTO content
            (url_uuid, cache_path)
            VALUES
            (%s, %s)
        ''', [new_id, file_name])
        dbclient.commit()


def queue_urls(links, dbclient, opts):
    '''
    Check the database for any queued URLS, and add to the list
    '''
    out = Output(opts)

    cur = dbclient.cursor()
    if isinstance(links, str):
        links = [links]
    for url in links:
        if opts.get('force') is not True and not opts.get('queue_id'):
            # Check for URL in DB
            cur.execute('''
                SELECT uuid
                FROM urls
                WHERE url = %s
            ''', [url])
            if cur.rowcount > 0:
                out.info('URL has already been downloaded; use --force if necessary')
                continue

        fields = ['url']
        args = [url]
        if opts.get('queue_id') is not None:
            fields.append('uuid')
            args.append(opts['queue_id'])

        if 'refresh_interval' in opts:
            fields.append('refresh_interval')
            args.append(opts['refresh_interval'])

        query = 'INSERT INTO dl_queue ({}) VALUES ({})'.format(
            ', '.join(fields),
            ', '.join(['%s' for arg in range(len(args))])
        )

        try:
            cur.execute(query, args)
            dbclient.commit()
        except psycopg2.IntegrityError:
            # This URL is already queued
            dbclient.rollback()


def reprocess_urls(urls, patterns, dbclient=None):
    '''
    Reprocess the cached URLs which matches the pattern(s)
    '''
    if not urls:
        urls = []

    if isinstance(patterns, str):
        patterns = [patterns]

    cur = dbclient.cursor()
    wheres = ['url~%s'] * len(patterns)
    query = 'SELECT url FROM urls WHERE {}'.format(' OR '.join(wheres))
    cur.execute(query, patterns)
    for row in cur.fetchall():
        urls.append(row[0])

    return urls


def queue_regexp(urls, pattern, dbclient, opts):
    '''
    Add the URLs matching the pattern to the download queue
    '''
    expr = re.compile(pattern)
    links = []
    for url in urls:
        if expr.search(url):
            links.append(url)
    queue_urls(links, dbclient, opts)


def _rename(media_url, file_name, opts):
    '''
    When files are downloaded using status, rename as per a template
    '''
    out = Output(opts)

    template = opts.get('rename_template', '')
    if not template:
        return file_name

    urlcomps = urllib.parse.urlparse(media_url)
    replacements = {
        'host': urlcomps[1].split(':')[0],
        'path': '/'.join(urlcomps[2].split('/')[:-2])
    }

    # File extensions
    if '.' in urlcomps[2].split('/')[-1]:
        replacements['ext'] = urlcomps[2].split('/')[-1].split('.')[-1]
    else:
        replacements['ext'] = ''

    if not opts.get('rename_count'):
        opts['rename_count'] = opts.get('rename_count_start', 0)

    if opts.get('rename_count_padding'):
        try:
            opts['rename_count_padding'] = int(opts['rename_count_padding'])
        except ValueError:
            out.warn('--rename-count-padding must be an integer, using 0')
            opts['rename_count_padding'] = 0
        template = template.replace('{count}', '{count:0>{rename_count_padding}}')
        replacements['rename_count_padding'] = opts['rename_count_padding']
    replacements['count'] = str(opts['rename_count'])
    opts['rename_count'] += 1

    file_name = os.path.join(opts['save_path'], template.format(**replacements))

    return file_name


def parse_links(url, content, level, opts):
    '''
    Return the links from an HTML page
    '''
    out = Output(opts)

    hrefs = []
    try:
        # Get ready to do some html parsing
        soup = BeautifulSoup(content, 'html.parser')
        # Generate absolute URLs for every link on the page
        url_comps = urllib.parse.urlparse(url)
        tags = soup.find_all('a')
        if opts['search_src'] is True:
            tags = tags + soup.find_all(src=True)
        for link in tags:
            if level > int(opts['level']):
                continue
            href = urllib.parse.urljoin(url, link.get('href'))
            if opts['search_src'] is True and not link.get('href'):
                href = urllib.parse.urljoin(url, link.get('src'))
            link_comps = urllib.parse.urlparse(href)
            if link.text.startswith('javascript'):
                continue
            if int(opts.get('level', 0)) > 0 and int(opts.get('level', 0)) < 2:
                continue
            if opts['span_hosts'] is not True:
                if not link_comps[1].startswith(url_comps[1].split(':')[0]):
                    continue
            hrefs.append(href.split('#')[0])
        # Render the page, and print it along with the links
        if opts.get('render', False) is True:
            out.info(soup.get_text())
        return hrefs
    except TypeError:
        # This URL probably isn't HTML
        return []

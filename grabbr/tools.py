# -*- coding: utf-8 -*-
'''
Tools for Grabbr
'''
import os
import sys
import time
import random
import pprint
import requests
from termcolor import colored
import psycopg2
from psycopg2.extras import Json


def process_url(url_id, url, content, modules, opts):
    '''
    Process a URL
    '''
    fun = None
    for mod in modules:
        if fun is not None:
            break
        if not mod.endswith('.func_map'):
            continue
        fun = modules[mod](url)
    fun(url_id, url, content)


def get_url(
        url,
        parent=None,
        referer=None,
        dbclient=None,
        client=requests,
        opts=None,
    ):
    '''
    Download a URL (if necessary) and store it
    '''
    cur = dbclient.cursor()
    exists = False

    # Check for URL in DB
    cur.execute('''
        SELECT id, url, last_retrieved
        FROM urls
        WHERE url = %s
    ''', [url])

    if cur.rowcount < 1:
        # URL has never been retrieved
        cur.execute('''
            INSERT INTO urls
            (url) VALUES (%s)
            RETURNING id
        ''', [url])
        dbclient.commit()
        url_id = cur.fetchone()[0]
        print(colored(
            '{} has not been retrieved before, new ID is {}'.format(
                url, url_id
            ), 'green',
        ))
    else:
        # URL has been retrieved, get its ID
        url_id = cur.fetchone()[0]
        print(colored('{} exists, ID is {}'.format(url, url_id), 'yellow'))
        exists = True

    # Save referer relationships
    if parent:
        try:
            cur.execute('''
                INSERT INTO referers
                (url_id, referer_id)
                VALUES
                (%s, %s)
            ''', [url_id, parent])
            dbclient.commit()
        except psycopg2.IntegrityError:
            # This relationship already exists
            dbclient.rollback()

    # Check for content
    cur.execute('''
        SELECT data, id
        FROM content
        WHERE url_id = %s
        ORDER BY retrieved
        LIMIT 1
    ''', [url_id])
    if cur.rowcount < 1:
        headers = opts['headers'].copy()
        if referer:
            headers['referer'] = referer
        req = client.get(url, headers=headers)
        if opts.get('include_headers') is True:
            print(colored(pprint.pformat(dict(req.headers)) , 'cyan'))
        content = req.text
        cur.execute('''
                INSERT INTO content
                (url_id, data) VALUES (%s, %s)
            ''',
            [
                url_id,
                Json({'content': content})
            ]
        )
        dbclient.commit()
    else:
        if opts['force'] is True:
            row_id = cur.fetchone()[1]
            headers = opts['headers'].copy()
            if referer:
                headers['referer'] = referer
            req = client.get(url, headers=headers)
            if opts.get('include_headers') is True:
                print(colored(pprint.pformat(dict(req.headers)) , 'cyan'))
            content = req.text
            cur.execute('''
                    UPDATE content
                    SET url_id = %s, data = %s
                    WHERE id = %s
                ''',
                [
                    url_id,
                    Json({'content': content}),
                    row_id
                ]
            )
            dbclient.commit()
        else:
            content = cur.fetchone()[0]['content']

    if exists is False:
        if opts['random_sleep'] is True:
            time.sleep(random.randrange(1, 10))
    return url_id, content


def status(req, media_url, file_name, sleep=0):
    '''
    Show status of the download
    '''
    try:
        cache_dir = '/'.join(file_name.split('/')[:-1])
        os.makedirs(cache_dir)
    except PermissionError as exc:
        print(colored('Cannot create directory {}: {}'.format(cachedir, exc), 'red', attrs=['bold']))
    except FileExistsError:
        pass

    print(colored('Downloading: {}'.format(media_url), 'green'))
    if os.path.exists(file_name):
        print(colored('... {} exists, skipping'.format(file_name), 'yellow'))
        return
    sys.stdout.write(colored('...Saving to: ', 'green'))
    print(colored(file_name, 'cyan'))
    buffer_size = 4096
    total = int(req.headers.get('Content-Length', 0))
    count = 0
    try:
        point = int(total / 100)
        increment = int(total / buffer_size)
    except ZeroDivisionError:
        print(colored('Divide by zero error, status not available', 'red', attrs=['bold']))
        point = 0
        increment = 0
    start_time = time.time()
    last_time = time.time()
    delay_blocks = 0
    delay_count = 0
    with open(file_name, 'wb') as fhp:
        old_time = time.time()
        for block in req.iter_content(buffer_size):
            fhp.write(block)
            count += buffer_size
            delay_blocks += buffer_size
            delay_count += 1
            old_time = time.time()
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
                sys.stdout.write('\x1b[2K\r')
                sys.stdout.write(colored('Total size is {} '.format(sizeof_fmt(total)), 'green'))
                sys.stdout.write(colored('({} bytes), '.format(total), 'green'))
                sys.stdout.write(colored('{}%, '.format(str(percent)), 'cyan'))
                sys.stdout.write(colored(kbsec, 'cyan'))
                sys.stdout.write(colored(' KiB/s, ', 'cyan'))
                sys.stdout.write(colored('{}/{} left'.format(time_left, time_total), 'cyan'))
                sys.stdout.flush()
                delay_blocks = 0
                delay_count = 0
    print()
    time.sleep(sleep)


def sizeof_fmt(num, suffix='B'):
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s " % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s " % (num, 'Yi', suffix)


def dbsave_media(cur, media_url, url_id, file_name, dbclient):
    '''
    Save a media item into the database, once it's been downloaded

    cur: Database cursor

    media_url: The URL of the image/video that was downloaded

    url_id: The ID of the parent of the media_url

    file_name: The place where the media_url was downloaded to
    '''
    try:
        cur.execute('''
            INSERT INTO urls (url) values (%s) RETURNING id
        ''', [media_url])
        dbclient.commit()
        new_id = cur.fetchone()[0]
    except psycopg2.IntegrityError:
        # This relationship already exists
        dbclient.rollback()
        cur.execute('''
            SELECT id FROM urls WHERE url = %s
        ''', [media_url])
        new_id = cur.fetchone()[0]

    try:
        cur.execute('''
            INSERT INTO referers (url_id, referer_id) values (%s, %s)
        ''', [new_id, url_id])
        dbclient.commit()
    except psycopg2.IntegrityError:
        # This relationship already exists
        dbclient.rollback()

    cur.execute('''
        SELECT COUNT(*) FROM content WHERE url_id = %s
    ''', [new_id])
    if cur.fetchone()[0] < 1:
        cur.execute('''
            INSERT INTO content
            (url_id, cache_path)
            VALUES
            (%s, %s)
        ''', [new_id, file_name])
        dbclient.commit()


def queue_urls(links, dbclient, opts):
    '''
    Check the database for any queued URLS, and add to the list
    '''
    cur = dbclient.cursor()
    if isinstance(links, str):
        links = [links]
    for url in links:
        if opts.get('force') is not True:
            # Check for URL in DB
            cur.execute('''
                SELECT id
                FROM urls
                WHERE url = %s
            ''', [url])
            if cur.rowcount > 0:
                continue

        try:
            cur.execute('INSERT INTO dl_queue (url) VALUES (%s)', [url])
            dbclient.commit()
        except psycopg2.IntegrityError:
            # This URL is already queued
            dbclient.rollback()

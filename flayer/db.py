# -*- coding: utf-8 -*-
'''
Database functions for Web Flayer
'''
# Python
import os
import time
import urllib
import datetime

# 3rd party
import psycopg2
import psycopg2.extras

# Internal
import flayer.tools


def client(config):
    '''
    Return database client
    '''
    dbclient = psycopg2.connect(
        'dbname={0} user={1} password={2} host={3}'.format(
            config.get('dbname', 'flayer'),
            config.get('dbuser', 'postgres'),
            config.get('dbpass', ''),
            config.get('dbhost', 'localhost'),
        )
    )
    psycopg2.extensions.register_adapter(dict, psycopg2.extras.Json)
    return dbclient


def pop_dl_queue(dbclient, urls, opts):
    '''
    Check the database for any queued URLS, and add to the list
    '''
    cur = dbclient.cursor()

    # Unpause jobs past the time limit
    cur.execute('''
        UPDATE dl_queue
        SET paused_until = NULL
        WHERE paused_until IS NOT NULL
        AND paused_until <= NOW()
    ''')
    dbclient.commit()

    # Lock a URL for this instance
    cur.execute('''
        LOCK TABLE ONLY dl_queue;
        UPDATE dl_queue
        SET locked_by = %s
        WHERE uuid = (
            SELECT uuid
            FROM dl_queue
            WHERE paused = FALSE
            AND paused_until IS NULL
            ORDER BY dl_order, added
            LIMIT 1
        )
        RETURNING uuid
    ''', [opts['id']])
    if cur.rowcount > 0:
        data = cur.fetchone()
        url_uuid = data[0]
    else:
        return

    # Helps out with the lock
    time.sleep(.2)

    # Queue the URL and delete it from the queue
    cur.execute('SELECT url, refresh_interval FROM dl_queue WHERE uuid = %s', [url_uuid])
    url, refresh = cur.fetchone()
    urls.append(url)
    if refresh:
        next_refresh = datetime.datetime.now() + datetime.timedelta(**refresh)
        cur.execute('''
            UPDATE dl_queue SET locked_by = '', paused_until = %s WHERE uuid = %s
        ''', [next_refresh, url_uuid])
    else:
        cur.execute('DELETE FROM dl_queue WHERE uuid = %s', [url_uuid])
    dbclient.commit()
    opts['queue_id'] = url_uuid


def update_url_refresh(url_uuid, interval, dbclient, opts):
    '''
    List all queued URLs in the database
    '''
    ret = []
    out = flayer.tools.Output(opts)

    cur = dbclient.cursor()
    cur.execute(
        'UPDATE urls SET refresh_interval = %s WHERE uuid = %s',
        [interval, url_uuid],
    )
    dbclient.commit()


def list_queue(dbclient, opts):
    '''
    List all queued URLs in the database
    '''
    ret = []
    out = flayer.tools.Output(opts)

    cur = dbclient.cursor()
    cur.execute('SELECT url, paused FROM dl_queue')
    if cur.rowcount > 0:
        for row in cur.fetchall():
            if bool(row[1]) is True:
                line = '{} (paused)'.format(row[0])
            else:
                line = row[0]
            ret.append(line)
            out.info(line)
    out.info('{} URLS queued'.format(cur.rowcount))
    if not opts.get('already_running'):
        try:
            os.remove(opts['pid_file'])
        except FileNotFoundError:
            pass
    return {'urls': ret, 'number_queued': cur.rowcount}


def pause(dbclient, opts, urls):
    '''
    Pause URL(s) in the download queue
    '''
    ret = {'urls': urls, 'number_paused': len(urls)}
    out = flayer.tools.Output(opts)

    cur = dbclient.cursor()

    spacer = ', '.join(['%s' for url in range(len(urls))])
    sql = 'UPDATE dl_queue SET paused = true WHERE url IN ({})'.format(spacer)
    cur.execute(sql, urls)
    dbclient.commit()
    out.info(ret)
    return ret


def unpause(dbclient, opts, urls):
    '''
    Unpause URL(s) in the download queue
    '''
    ret = {'urls': urls, 'number_unpaused': len(urls)}
    out = flayer.tools.Output(opts)

    cur = dbclient.cursor()

    spacer = ', '.join(['%s' for url in range(len(urls))])
    sql = 'UPDATE dl_queue SET paused = false WHERE url IN ({})'.format(spacer)
    cur.execute(sql, urls)
    dbclient.commit()
    out.info(ret)
    return ret


def pattern_wait(dbclient, url):
    '''
    Check the URL against the ``pattern_wait`` table, using a regular
    expression. If it matches, then all other URLs that match the pattern will
    have their ``paused_until`` values updated to ``now() + {wait} seconds``.

    Only the first match will be returned, so it's best to make patterns as
    specific as possible. Normally a pattern will only be a domain name, so
    this should not normally be a problem.

    This function should be run before and after any download, such as
    ``get_url()`` and ``status()``. Running before will help prevent other
    agents from hitting the domain again at the same time, and running after
    will keep all agents from hitting a domain again too fast.
    '''
    cur = dbclient.cursor()

    sql = 'SELECT wait FROM pattern_wait WHERE %s ~ pattern LIMIT 1'
    cur.execute(sql, [url])
    try:
        wait = cur.fetchone()[0]
    except TypeError:
        # No matches
        return

    sql = "UPDATE dl_queue SET paused_until = now() + '%s seconds'"
    cur.execute(sql, [wait])
    dbclient.commit()


def check_domain_wait(dbclient, url):
    '''
    Check the URL against the ``domain_wait`` table. If the domain is in the
    table, it will check the ``wait_until`` field. If that time has not yet
    passed, return ``False``.

    Before checking the ``domain_wait`` table for the domain, another query
    will delete any entries from the table that are passed the ``wait_until``
    time.

    This function should be run before any download, such as ``get_url()`` and
    ``status()``. Running before will help prevent other agents from hitting
    the domain again at the same time, or too quickly afterwards.
    '''
    cur = dbclient.cursor()

    sql = 'DELETE from domain_wait WHERE wait_until < now()'
    cur.execute(sql)
    dbclient.commit()

    urlcomps = urllib.parse.urlparse(url)
    domain = urlcomps[1]

    sql = 'SELECT count(*) FROM domain_wait WHERE domain ~ %s'
    cur.execute(sql, [domain])
    try:
        wait = cur.fetchone()[0]
        if int(wait) > 0:
            return False
    except TypeError:
        # No matches
        return True


def set_domain_wait(dbclient, opts, url):
    '''
    This function should be run before any download, such as ``get_url()`` and
    ``status()``. Running before will help prevent other agents from hitting
    the domain again at the same time, or too quickly afterwards.
    '''
    cur = dbclient.cursor()

    urlcomps = urllib.parse.urlparse(url)
    domain = urlcomps[1]

    sql = '''
        INSERT INTO domain_wait (domain, wait_until)
        values (%s, now() + '%s seconds')
        ON CONFLICT DO NOTHING
    '''
    cur.execute(sql, [domain, opts['domain_wait']])


def get_url_metadata(dbclient, opts):
    '''
    This function gets metadata for a URL which may or may not have already
    been retreived itself.
    '''
    out = flayer.tools.Output(opts)
    cur = dbclient.cursor()

    for url in opts['show_url_metadata']:
        sql = 'SELECT uuid FROM urls WHERE url ~ %s'
        cur.execute(sql, (url,))

        uuid = None
        if cur.rowcount > 0:
            uuid = cur.fetchone()[0]

        sql = 'SELECT uuid, metadata FROM url_metadata WHERE url = %s'
        cur.execute(sql, (url,))

        uuidm, metadata = cur.fetchone()
        if uuid and uuid != uuidm:
            out.warn('UUID in URLs does not match UUID in metadata')
            out.warn('{} in URLs'.format(uuid))
            out.warn('{} in metadata'.format(uuid))

        out.action('URL: {}'.format(url))
        out.action('UUID: {}'.format(uuid))
        out.info(pprint.pformat(metadata))


def store_url_metadata(dbclient, opts, url, metadata):
    '''
    This function stores metadata for a URL which may or may not have already
    been retreived itself.
    '''
    cur = dbclient.cursor()

    sql = 'SELECT uuid FROM urls WHERE url ~ %s'
    cur.execute(sql, (url,))

    uuid = None
    data = cur.fetchone()
    if data:
        uuid = data[0]

    sql = '''
        INSERT INTO url_metadata (uuid, url, metadata)
        VALUES (%s, %s, %s)
        ON CONFLICT (url) DO UPDATE
          SET metadata = %s
    '''
    cur.execute(sql, (uuid, url, json.dumps(metadata), json.dumps(metadata)))
    dbclient.commit()

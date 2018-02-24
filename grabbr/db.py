# -*- coding: utf-8 -*-
'''
Database functions for Grabbr
'''
# Python
import os
import time
import datetime

# 3rd party
import psycopg2
import psycopg2.extras

# Internal
import grabbr.tools


def client(config):
    '''
    Return database client
    '''
    dbclient = psycopg2.connect(
        'dbname={0} user={1} password={2} host={3}'.format(
            config.get('dbname', 'grabbr'),
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


def list_queue(dbclient, opts):
    '''
    List all queued URLs in the database
    '''
    ret = []
    out = grabbr.tools.Output(opts)

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
    out = grabbr.tools.Output(opts)

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
    out = grabbr.tools.Output(opts)

    cur = dbclient.cursor()

    spacer = ', '.join(['%s' for url in range(len(urls))])
    sql = 'UPDATE dl_queue SET paused = false WHERE url IN ({})'.format(spacer)
    cur.execute(sql, urls)
    dbclient.commit()
    out.info(ret)
    return ret

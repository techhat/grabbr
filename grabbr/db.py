# -*- coding: utf-8 -*-
'''
Database functions for Grabbr
'''
# Python
import os
import sys

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
        UPDATE dl_queue
        SET locked_by = %s
        WHERE id = (
            SELECT id
            FROM dl_queue
            WHERE paused = FALSE
            AND paused_until IS NULL
            ORDER BY dl_order, id
            LIMIT 1
        )
        RETURNING id
    ''', [opts.get('id', 'unknown')])
    dbclient.commit()
    if cur.rowcount > 0:
        data = cur.fetchone()
        url_id = data[0]
    else:
        return

    # Queue the URL and delete it from the queue
    cur.execute('SELECT url FROM dl_queue WHERE id = %s', [url_id])
    urls.append(cur.fetchone()[0])
    cur.execute('DELETE FROM dl_queue WHERE id = %s', [url_id])
    dbclient.commit()
    opts['queue_id'] = url_id


def list_queue(dbclient, opts):
    '''
    List all queued URLs in the database
    '''
    ret = []
    out = grabbr.tools.Output(opts)

    cur = dbclient.cursor()
    cur.execute('SELECT url FROM dl_queue')
    if cur.rowcount > 0:
        for row in cur.fetchall():
            ret.append(row[0])
            out.info('{}'.format(row[0]))
    out.info('{} URLS queued'.format(cur.rowcount))
    if not opts.get('already_running'):
        try:
            os.remove(opts['pid_file'])
        except FileNotFoundError:
            pass
    return {'urls': ret, 'number_queued': cur.rowcount}

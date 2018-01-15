# -*- coding: utf-8 -*-
'''
Database functions for Grabbr
'''
import os
import sys
from termcolor import colored
import psycopg2
import psycopg2.extras
from psycopg2.extras import Json


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


def pop_dl_queue(dbclient, urls):
    '''
    Check the database for any queued URLS, and add to the list
    '''
    cur = dbclient.cursor()
    cur.execute('SELECT id, url FROM dl_queue LIMIT 1')
    if cur.rowcount > 0:
        data = cur.fetchone()
        urls.append(data[1])
        cur.execute('DELETE FROM dl_queue WHERE id = %s', [data[0]])
        dbclient.commit()


def list_queue(dbclient, opts):
    '''
    List all queued URLs in the database
    '''
    cur = dbclient.cursor()
    cur.execute('SELECT url FROM dl_queue')
    if cur.rowcount > 0:
        for row in cur.fetchall():
            print(colored('{}'.format(row[0]), 'green', attrs=['bold']))
    print(colored('{} URLS queued'.format(cur.rowcount), 'green', attrs=['bold']))
    if not opts.get('already_running'):
        os.remove(opts['pid_file'])
    sys.exit(0)

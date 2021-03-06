# -*- coding: utf-8 -*-
'''
API interface
'''
# Python
import json
import urllib
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn

# Internal
import flayer.db


class FlayerHTTPServer(ThreadingMixIn, HTTPServer):
    '''
    Threaded HTTP Server
    '''

def MakeFlayerHTTPRequestHandler(opts, context):  # pylint: disable=invalid-name
    '''
    Return an HTTP class which can handle opts being passed in
    '''
    class FlayerHTTPRequestHandler(BaseHTTPRequestHandler):
        '''
        Process arguments
        '''
        def __init__(self, *args, **kwargs):
            self.dbclient = flayer.db.client(opts)
            super(FlayerHTTPRequestHandler, self).__init__(*args, **kwargs)

        def do_GET(self):  # pylint: disable=invalid-name
            '''
            Only GET requests are supported at this time
            '''
            qstr = self.path.lstrip('/?')
            data = urllib.parse.parse_qs(qstr)
            if 'list_queue' in data:
                queue = flayer.db.list_queue(self.dbclient, opts)
                self.send(json.dumps(queue))
                return
            if 'show_opts' in data:
                tmp_opts = opts.copy()
                del tmp_opts['http_api']
                del tmp_opts['salt_event']
                for item in opts:
                    if isinstance(item, set):
                        tmp_opts[item] = list(temp_opts[item])
                self.send(json.dumps(tmp_opts, indent=4), content_type='text/json')
                return
            if 'show_context' in data:
                self.send(json.dumps(context, indent=4), content_type='text/json')
                return
            for item in ('headers', 'parser_dir'):
                if item in data:
                    opts[item] = data[item]
                    del data[item]
            for item in data:
                if data[item][0] in ('True', 'False', 'None'):
                    opts[item] = bool(data[item][0])
                elif item == 'user_agent':
                    opts['headers']['User-Agent'] = data[item][0]
                else:
                    opts[item] = data[item][0]
            self.send('True')

            # Stop the server if necessary
            if opts.get('stop') or opts.get('hard_stop') or opts.get('abort'):
                open(opts['stop_file'], 'a').close()

        def send(self, message, response=200, content_type='text/html'):
            '''
            Send a message to the client
            '''
            self.send_response(response)
            self.send_header('Content-type', content_type)
            self.end_headers()
            self.wfile.write(bytes(message, 'utf8'))

        def log_message(self, fmt, *args):  # pylint: disable=arguments-differ,unused-argument
            '''
            Don't log to the console
            '''
            return

    return FlayerHTTPRequestHandler


def run(opts, context):
    '''
    Main HTTP server
    '''
    server_address = ((
        opts.get('api_addr', '127.0.0.1'),
        int(opts.get('api_port', 42424)),
    ))
    flayer_handler = MakeFlayerHTTPRequestHandler(opts, context)
    httpd = FlayerHTTPServer(
        server_address,
        flayer_handler,
    )
    opts['http_api'] = httpd
    thread = threading.Thread(target=httpd.serve_forever)
    thread.start()

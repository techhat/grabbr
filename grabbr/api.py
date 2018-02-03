# -*- coding: utf-8 -*-
'''
API interface
'''
# Python
import urllib
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn


class GrabbrHTTPServer(ThreadingMixIn, HTTPServer):
    '''
    Threaded HTTP Server
    '''

def MakeGrabbrHTTPRequestHandler(opts):
    class GrabbrHTTPRequestHandler(BaseHTTPRequestHandler):
        '''
        Process arguments
        '''
        def __init__(self, *args, **kwargs):
            super(GrabbrHTTPRequestHandler, self).__init__(*args, **kwargs)

        def do_GET(self):
            '''
            Only GET requests are supported at this time
            '''
            qstr = self.path.lstrip('/?')
            data = urllib.parse.parse_qs(qstr)
            for item in ('headers', 'module_dir'):
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
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(bytes('True', 'utf8'))

            # Stop the server if necessary
            if opts.get('stop') or opts.get('hard_stop') or opts.get('abort'):
                open(opts['stop_file'], 'a').close()

    return GrabbrHTTPRequestHandler


def run(opts):
    '''
    Main HTTP server
    '''
    server_address = ((
        opts.get('api_addr', '127.0.0.1'),
        opts.get('api_port', 42424),
    ))
    grabbr_handler = MakeGrabbrHTTPRequestHandler(opts)
    httpd = GrabbrHTTPServer(
        server_address,
        grabbr_handler,
    )
    opts['http_api'] = httpd
    thread = threading.Thread(target=httpd.serve_forever)
    thread.start()

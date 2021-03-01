"""
Dashboard entry point
============================================

..
  Copyright (c) 2018 LG Electronics Inc.
  SPDX-License-Identifier: GPL-3.0-or-later

"""

import os
import sys
import shutil
import logging
import argparse
import subprocess
import threading
import requests
import re
import cgi
import json

import aup.RestAPI.server as be_server
from http.server import SimpleHTTPRequestHandler, HTTPServer
from ..utils import get_available_port

SUCCESS = 0
ERROR = 1
global BACKEND_PORT
FE_BUILD_DIR = 'frontend/febuild/auptimizer-dashboard'

LOGGER = logging.getLogger("dashboard")

class ProxyHTTPRequestHandler(SimpleHTTPRequestHandler):
    global BACKEND_PORT

    def log_message(self, format, *args):
        dir_path = os.environ['PWD']
        log_file_name = "dashboard_logs"
        path = os.path.join(dir_path, log_file_name)
        append_write = 'a'

        if not os.path.exists(path):
            append_write = 'w'
        
        with open (path, append_write) as f:
            f.write("%s - - [%s] %s\n" %
                         (self.address_string(),
                          self.log_date_time_string(),
                          format%args))

    def do_DELETE(self):
        rv = re.search('/api/(.*)$', self.path)
        if rv != None:
            url = 'http://127.0.0.1:{}{}'.format(str(BACKEND_PORT), self.path)

            resp = requests.delete(url)

            self.send_response(resp.status_code)
            self.send_resp_headers(resp)
            self.wfile.write(resp.content)
            return

        super().do_DELETE()
        return

    def do_GET(self):
        rv = re.search('/api/(.*)$', self.path)
        if rv != None:
            url = 'http://127.0.0.1:{}{}'.format(str(BACKEND_PORT), self.path)

            resp = requests.get(url)

            self.send_response(resp.status_code)
            self.send_resp_headers(resp)
            self.wfile.write(resp.content)
            return

        super().do_GET()
        return

    def do_POST(self):
        rv = re.search('/api/(.*)$', self.path)
        if rv != None:
            url = 'http://127.0.0.1:{}{}'.format(str(BACKEND_PORT), self.path)

            content_type = self.headers.get('content-type')
            body = None

            if content_type is not None:
                ctype, pdict = cgi.parse_header(content_type)

                # refuse to receive non-json content
                if ctype != 'application/json':
                    self.send_response(400)
                    self.end_headers()
                    return

                # read the message and convert it into a python dictionary
                length = int(self.headers.get('content-length'))
                encoded_msg = self.rfile.read(length)
                body = json.loads(encoded_msg.decode(sys.stdin.encoding if sys.stdin.encoding is not None else 'UTF-8'))

            resp = requests.post(url, json=body)

            self.send_response(resp.status_code)
            self.send_resp_headers(resp)
            self.wfile.write(resp.content)
            return

        return

    def send_resp_headers(self, resp):
        respheaders = resp.headers
        for key in respheaders:
            if key not in ['Content-Encoding', 'Transfer-Encoding', 'content-encoding', 'transfer-encoding', 'content-length', 'Content-Length']:
                self.send_header(key, respheaders[key])
        self.send_header('Content-Length', len(resp.content))
        self.end_headers()

def start_fe_server(PORT):
    server_address = ('', PORT)
    httpd = HTTPServer(server_address, ProxyHTTPRequestHandler)

    httpd.serve_forever()

def start_servers(path, port, frontend):
    global BACKEND_PORT

    import pathlib
    pa = pathlib.Path(__file__).resolve().parent

    if (path is not None) and (not os.path.exists(path)):
        LOGGER.error('{} does not exist!'.format(path))
        return ERROR

    LOGGER.debug('Backend started on 0.0.0.0:{}'.format(BACKEND_PORT))

    # separate thread
    path = os.path.abspath(path) if path is not None else None
    be_server_thr = threading.Thread(target=be_server.main, args=(path, BACKEND_PORT), daemon=True)
    if frontend:
        fe_server_thr = threading.Thread(target=start_fe_server, args=(port,), daemon=True)

    # for frontend
    os.chdir(os.path.join(str(pa), FE_BUILD_DIR))

    try:
        be_server_thr.start()
        if frontend:
            fe_server_thr.start()

        if frontend:
            fe_server_thr.join()
        be_server_thr.join()
    except Exception as e:
        LOGGER.error('Exception occurred:' + str(e))
        return ERROR

    return SUCCESS

def _start_dashboard(path, port, frontend):
    global BACKEND_PORT

    BACKEND_PORT = get_available_port()
    
    return start_servers(path, port, frontend)

def main():
    global BACKEND_PORT

    """ Main function that parses arguments and opens fe+be."""
    parser = argparse.ArgumentParser(
        description='Open frontend and backend of the auptimizer dashboard')
    parser.add_argument(
        '--path',
        type=str,
        dest='path',
        default=None,
        help='Path of the sqlite db file.'
    )
    parser.add_argument(
        '--port',
        type=int,
        dest='port',
        help='Port for frontend. Leave blank for backend only.',
    )
    parser.add_argument(
        '--backend_port',
        type=int,
        dest='backend_port',
        help='Port for the backend. Optional, for easier debugging.'
    )

    args = parser.parse_args()

    BACKEND_PORT = get_available_port()

    if args.backend_port is not None:
        BACKEND_PORT = args.backend_port

    if args.port is None:
        args.frontend = False
    else:
        args.frontend = True
        print('Dashboard started on 0.0.0.0:{}'.format(args.port))
        print('To exit press CTRL+C...')

    return start_servers(args.path, args.port, args.frontend)


if __name__ == "__main__":
    sys.exit(main())

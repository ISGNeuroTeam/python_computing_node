import json
import cgi
import json
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer

log = logging.getLogger(__name__)


class Server(BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

    def do_HEAD(self):
        self._set_headers()

    # GET sends back a Hello world message
    def do_GET(self):
        self._set_headers()
        self.wfile.write(json.dumps({'hello': 'world', 'received': 'ok'}))

    # POST echoes the message adding a JSON field
    def do_POST(self):

        # read the message and convert it into a python dictionary
        length = int(self.headers.get('content-length'))
        payload_string = self.rfile.read(length).decode('utf-8')
        message = json.loads(payload_string) if payload_string else None
        print(message)

        ctype, pdict = cgi.parse_header(self.headers.get('content-type'))

        # refuse to receive non-json content
        if ctype != 'application/json':
            self.send_response(400)
            self.end_headers()
            return

        # add a property to the object, just to mess with data
        message['received'] = 'ok'

        # TODO get node job and execute it
        # send the message back
        self._set_headers()
        self.wfile.write(json.dumps(message).encode())


def run(server_class=HTTPServer, handler_class=Server, port=8008):
    server_address = ('', port)
    print(port)
    httpd = server_class(server_address, handler_class)
    log.info('Starting httpd on port %d...' % port)
    print('Starting httpd on port %d...' % port)
    httpd.serve_forever()




import socket


class ServerClient:
    def __init__(self, socket_type, port, run_dir):
        self._socket_type = socket_type
        self._port = port
        self._run_dir = run_dir


    def send_status(self, status):
        print('senging status')


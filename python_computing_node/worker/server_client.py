import socket
import json
import logging

from pathlib import Path
from contextlib import contextmanager

log = logging.getLogger('worker')


class ServerClient:
    def __init__(self, socket_type: socket.AddressFamily, port: int, run_dir: str):
        self._socket_type = socket_type
        self._port = port
        self._run_dir = run_dir

    def send_job_status(self, uuid: str, status: str, message: str):
        """
        Sends job status to server
        """
        self._send_json_message(
            '/job_status',
            {
                'uuid': uuid,
                'status': status,
                'message': message
            }
        )

    def _send_json_message(self, uri: str, data: dict):
        """
        Sends json to server
        """
        host = 'localhost'
        data = json.dumps(data)
        data_len = len(data)
        http_message = (
                f"POST {uri} HTTP/1.1\r\nHost: {host}\r\nContent-Type: application/json\r\nContent-Length: " +
                str(data_len) + "\r\n\r\n" + data
        ).encode()
        with self._socket() as sock:
            sock.send(http_message)
            resp = sock.recv(1024)
            # todo log if error response

    @contextmanager
    def _socket(self):
        """
        Contex manager for socket
        """
        s = socket.socket(self._socket_type, socket.SOCK_STREAM)
        if self._socket_type == socket.AF_UNIX:
            s.connect(str(Path(self._run_dir) / f'server{self._port}.socket'))
        elif self._socket_type == socket.AF_INET:
            s.connect(('localhost', 'port'))
        else:
            raise ValueError('Unsupported socket type')
        try:
            yield s
        finally:
            s.close()


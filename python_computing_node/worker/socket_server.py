from typing import Dict
from enum import Enum

from pathlib import Path

from gunicorn.app.base import Application
from bottle import Bottle, request, response




class SocketType(Enum):
    unix_socket = 1
    local_port = 2


class Server:
    def __init__(
            self, port: int,
            inter_proc_storage: str, shared_storage: str,  local_storage: str,
    ):
        self.port = port
        self.command_executor = None  # get command executor from None

        self.app = Bottle()
        self.app.route('/job', method='POST', callback=self.run_job)
        self.gun_app = self.create_gunicorn_app(self.app, port)

    def run_job(self):
        node_job: Dict = request.json
        # self.command_executor.execute(node_job['commands'])
        response.status = 200
        response.content_type = 'application/json'

        return {'message': 'hello world'}

    def create_gunicorn_app(self, app: Bottle, port: int, socket_type: SocketType=SocketType.unix_socket):

        config = dict()

        socket_path = Path(__file__).parent / f'worker{str(port)}.socket'
        config["bind"] = "unix:" + str(socket_path)
        config['timeout'] = 0
        config['loglevel'] = 'error'

        handler = app

        class GunicornApplication(Application):
            def init(self, parser, opts, args):
                return config

            def load(self):
                return handler

        gun_app = GunicornApplication()
        return gun_app

    def run(self):
        self.gun_app.run()











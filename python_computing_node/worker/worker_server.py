import socket
from typing import Dict
from enum import Enum

from pathlib import Path

from gunicorn.app.base import Application
from bottle import Bottle, request, response


class WorkerServer:
    def __init__(
            self,
            socket_type: socket.AddressFamily,
            port: int,
            command_executor,
            server_client,
            run_dir
    ):
        self.port = port
        self.command_executor = command_executor

        self.app = Bottle()
        self.app.route('/job', method='POST', callback=self.run_job)
        self.app.route('/syntax', method='GET', callback=self.get_syntax)
        self.gun_app = self.create_gunicorn_app(self.app, port, socket_type, run_dir)

    def run_job(self):
        node_job: Dict = request.json
        #self.command_executor.execute(node_job['commands'])
        response.status = 200
        response.content_type = 'application/json'

        return {
            'status': 'FINISHED',
        }

    def get_syntax(self):
        response.status = 200
        response.content_type = 'application/json'
        return self.command_executor.get_syntax()

    @staticmethod
    def create_gunicorn_app(app: Bottle, port: int, socket_type: socket.AddressFamily, run_dir):

        config = dict()
        if socket_type == socket.AF_UNIX:
            socket_path = Path(run_dir) / f'worker{str(port)}.socket'
            config["bind"] = "unix:" + str(socket_path)
        else:
            config['bind'] = f'0.0.0.0:{port}'

        config['timeout'] = 0
        config['loglevel'] = 'info'
        config['pidfile'] = str(Path(run_dir) / f'worker{port}.pid')

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











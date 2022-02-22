import logging
import socket
import json
import logging

import traceback

from typing import Dict

from pathlib import Path

from gunicorn.app.base import Application
from bottle import Bottle, request, response

log = logging.getLogger('worker')


class WorkerServer:
    def __init__(
            self,
            socket_type: socket.AddressFamily,
            port: int,
            command_executor,
            progress_notifier,
            run_dir
    ):
        self.port = port
        self.command_executor = command_executor
        self.progress_notifier = progress_notifier

        self.app = Bottle()
        self.app.route('/job', method='POST', callback=self.run_job)
        self.app.route('/syntax', method='GET', callback=self.get_syntax)
        self.gun_app = self.create_gunicorn_app(self.app, port, socket_type, run_dir)

    def run_job(self):
        node_job: Dict = json.load(request.body)
        response.status = 200
        response.content_type = 'application/json'

        try:
            self.progress_notifier.set_cur_job_uuid(node_job['uuid'])

            log.info(f'Get node job {node_job["uuid"]}')
            self.command_executor.execute(node_job['commands'])
            log.info(f'Node job {node_job["uuid"]} finished')

            return {
                'status': 'FINISHED',
                'status_text': f'node job {node_job["uuid"]} finished'
            }
        except Exception as err:
            tb = traceback.format_exc()
            log.error(str(err))
            log.error(str(tb))
            return {
                'status': 'ERROR',
                'status_text': str(err)
            }

    def get_syntax(self):
        response.status = 200
        response.content_type = 'application/json'
        return json.dumps(self.command_executor.get_command_syntax())

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











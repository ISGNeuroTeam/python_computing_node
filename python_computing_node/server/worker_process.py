import os
import json
import sys
import asyncio
import aiohttp
import logging

from aiohttp.client_exceptions import ClientError
from pathlib import Path
from .timings import WORKER_PROCESS_SPAWN_TIME

BASE_SOURCE_DIR = Path(__file__).resolve().parent.parent
WORKER_DIR = BASE_SOURCE_DIR / 'worker'


log = logging.getLogger('server')


class LaunchCommand:
    def __init__(
            self, proc_num_limit, memory_limit,
            execution_environment_dir, execution_environment, commands_dir,
            storages,
            socket_type, port,
            server_socket_type, server_port, run_dir, log_dir, log_level
    ):
        self.commands_dir = commands_dir
        self.socket_type = socket_type
        self.port = port
        self.proc_num_limit = proc_num_limit
        self.memory_limit = memory_limit
        self.storages = storages
        self.execution_environment_dir = execution_environment_dir
        self.execution_environment = execution_environment

        self.server_socket_type = server_socket_type
        self.server_port = server_port

        self.run_dir = run_dir

        self.log_dir = log_dir
        self.log_level = log_level

        self._command = self.create_launch_command()

    def __str__(self):
        return ' '.join(self._command)

    def create_launch_command(self):
        """
        Returns list of program and it's arguments
        """
        raise NotImplementedError

    def exec(self):
        """
        Runs program and return process instance
        """
        raise NotImplementedError


class UlimitLaunchCommand(LaunchCommand):
    def create_launch_command(self):
        command = [
            self._get_main_program(),
            self._get_memory_limit_option(),
            *self._get_python_launch_command(),
        ]
        command = list(filter(None, command))
        return command

    async def exec(self):
        return await asyncio.create_subprocess_exec(
            *self._command,
            env={
              'PYTHONPATH': str(BASE_SOURCE_DIR)
            },
            stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE
        )

    def _get_main_program(self):
        return 'prlimit'

    def _get_proc_num_limit_option(self):
        # this option doesn't work for one process
        return f''

    def _get_memory_limit_option(self):
        if self.memory_limit == 0:
            return ''
        return f'--data={self.memory_limit}'

    def _get_python_launch_command(self):
        storage_json_string = json.dumps(self.storages)
        return [
            self._get_python_executable(),
            '-m', 'worker', self.execution_environment_dir,
            self.execution_environment,
            self.commands_dir,
            storage_json_string,
            str(self.socket_type),
            str(self.port),
            self.server_socket_type,
            str(self.server_port),
            self.run_dir,
            self.log_dir,
            self.log_level,
        ]

    def _get_python_executable(self):
        execution_environment_venv = Path(self.execution_environment_dir) / self.execution_environment / 'venv'

        if execution_environment_venv.exists():
            return str(execution_environment_venv / 'bin/python')

        else:
            return sys.executable


class DockerLaunchCommand(LaunchCommand):
    def create_launch_command(self):
        command = self._get_main_program() + \
                  self._get_proc_num_limit_option() + \
                  self._get_memory_limit_option() + \
                  self._get_port_option() + \
                  self._get_storages_mount_option() + \
                  self._get_commands_dir_mount_option() + \
                  self._get_run_dir_mount_option() + \
                  self._get_log_dir_mount_option() + \
                  self._get_worker_src_moutn_option() + \
                  self._get_execution_environment_mount_option() + \
                  self._get_image_name() + \
                  self._get_python_launch_command()
        # filter empty options
        command = list(filter(None, command))
        return command

    async def exec(self):
        return await asyncio.create_subprocess_exec(
            *self._command,
            stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE
        )

    def _get_main_program(self):
        return [
            'docker',
            'run', '--rm', '-u', f'{os.getuid()}:{os.getgid()}'
        ]

    def _get_memory_limit_option(self):
        if self.memory_limit == 0:
            return ['', ]
        return ['-m', str(self.memory_limit)]

    def _get_proc_num_limit_option(self):
        if self.proc_num_limit == 0:
            return ['', ]
        return ['--pids-limit', str(self.proc_num_limit)]

    def _get_storages_mount_option(self):
        return ' '.join(
            [f'-v {mount_point}:/worker/storages/{storage_type}' for storage_type, mount_point in self.storages.items()]
        ).split(' ')

    def _get_execution_environment_mount_option(self):
        return ['-v', f'{self.execution_environment_dir}:/worker/execution_environment']

    def _get_run_dir_mount_option(self):
        return ['-v', f'{self.run_dir}:/worker/run']

    def _get_log_dir_mount_option(self):
        return ['-v', f'{self.log_dir}:/logs']

    def _get_commands_dir_mount_option(self):
        return ['-v', f'{self.commands_dir}:/worker/commands']

    def _get_worker_src_moutn_option(self):
        return ['-v', f'{WORKER_DIR}:/worker/worker']

    def _get_port_option(self):
        """
        If socket type is inet then provide port option for docket
        Else socket file will be in run directory
        """
        if self.socket_type == 'inet':
            return ['-p', f'{self.port}:{self.port}']
        else:
            return ['', ]

    def _get_python_launch_command(self):
        # get mount points in docker container
        storages = {storage_type: f'/worker/storages/{storage_type}' for storage_type in self.storages.keys()}
        storage_json_string = json.dumps(storages)
        return [
            self._get_python_executalbe(), '-m', 'worker', '/worker/execution_environment',
            self.execution_environment,
            '/worker/commands',
            storage_json_string,
            self.socket_type,
            str(self.port),
            self.server_socket_type,
            str(self.server_port),
            '/worker/run',
            '/logs',
            self.log_level
        ]

    def _get_python_executalbe(self):
        execution_environment_venv = Path(f'/worker/execution_environment/{self.execution_environment}/venv')

        if execution_environment_venv.exists():
            return execution_environment_venv / 'bin' / 'python'
        else:
            return 'python'

    def _get_image_name(self):
        return ['worker', ]


class WorkerProcess:
    def __init__(
            self, spawn_method,
            proc_num_limit, memory_limit,
            execution_environment_dir, execution_environment,
            commands_dir,
            storages,
            socket_type, port,
            server_socket_type, server_port, run_dir, log_dir, log_level
    ):
        """
        :param spawn_method: ulimit, docker
        :param socket_type: 'unix' or 'inet' string
        :param port: port for inet address or index for socket filename
        :param proc_num_limit: max number of processes in worker
        :param memory_limit: max memory usage in worker
        :param storages: dictionary with storage mounts
        :param execution_environment_dir: directory with execution_environments
        :param execution_environment: execution environment package located in execution_environment_dir
        :param server_socket_type: server socket type, 'unix' or 'inet' string
        :param server_port: server port
        :param run_dir: directory with pids and socket files
        :param log_dir: directory with worker logs
        :param log_level: log level
        """
        self.spawn_method = spawn_method
        self.port = port
        self.commands_dir = commands_dir
        self.socket_type = socket_type
        self.proc_num_limit = proc_num_limit
        self.memory_limit = memory_limit
        self.storages = storages
        self.execution_environment_dir = execution_environment_dir
        self.execution_environment = execution_environment

        self.server_socket_type = server_socket_type
        self.server_port = server_port

        self.run_dir = run_dir
        self.log_dir = log_dir
        self.log_level = log_level

        # subprocess object
        self.proc = None

        # command string
        self.command = self.create_launch_command()

        # session and server address to make requests will be created in spawn
        self.process_session = None
        self.address = None

    def create_launch_command(self):

        if self.spawn_method == 'ulimit':
            launch_command_cls = UlimitLaunchCommand

        elif self.spawn_method == 'docker':
            launch_command_cls = DockerLaunchCommand

        else:
            raise ValueError('Unknown spawn method')

        launch_command = launch_command_cls(
            self.proc_num_limit, self.memory_limit,
            self.execution_environment_dir, self.execution_environment, self.commands_dir,
            self.storages, self.socket_type, self.port, self.server_socket_type, self.server_port, self.run_dir,
            self.log_dir, self.log_level
        )
        return launch_command

    async def get_command_syntax(self):
        """
        Makes query to worker and returns command syntax of worker execution environment
        """
        assert self.process_session is not None
        async with self.process_session.get(self.address + 'syntax') as resp:
            resp = await resp.content.read()
            syntax = json.loads(resp)
        return syntax

    def _create_process_session(self):
        if self.socket_type == 'unix':
            socket_path = Path(self.run_dir) / f'worker{self.port}.socket'
            conn = aiohttp.UnixConnector(path=str(socket_path))
            session = aiohttp.ClientSession(connector=conn)
            address = 'http://localhost/'
            log.info(f'create sesssion with worker on socket {socket_path}')
        else:
            address = f'http://localhost:{self.port}/'
            session = aiohttp.ClientSession()
            log.info(f'create session with worker on address {address}')
        return session, address

    async def spawn(self):
        """
        Launch worker process and await ending
        Returns code and stderr output
        """
        log.info(f'Spawing worker: {str(self.command)}')
        self.proc = await self.command.exec()
        # wait for worker server started
        await asyncio.sleep(WORKER_PROCESS_SPAWN_TIME)
        self.process_session, self.address = self._create_process_session()

        await self.proc.wait()
        return self.proc.returncode, self.proc.stderr

    async def send_job(self, node_job):
        try:
            async with self.process_session.post(self.address + 'job', data=json.dumps(node_job)) as resp:
                resp = await resp.content.read()
                try:
                    resp = json.loads(resp)
                    return resp
                except json.decoder.JSONDecodeError:
                    log.error('Worker din\'t return success answer. Some error occurred. See worker log.')
                    return {
                        'status': 'FAILED',
                        'status_text': 'Worker din\'t return success answer. Some error occurred. See worker log.'
                    }
        except ClientError as err:
            log.error(f'Computing node server lost connection with worker. {str(err)}')
            return {
                'status': 'FAILED',
                'status_text': f'Computing node server lost connection with worker. {str(err)}'
            }

    def change_port(self, new_port):
        self.port = new_port
        self.command = self.create_launch_command()

    async def terminate(self):
        """
        Ternminates process session and process
        """
        if self.process_session is not None:
            await self.process_session.close()
        if self.proc is not None:
            self.proc.terminate()

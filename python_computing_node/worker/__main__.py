import importlib
import traceback
import sys
import argparse
import json
import socket
import signal
import logging.config

from pathlib import Path

from .worker_server import WorkerServer
from .server_client import ServerClient
from .progress_notify import ProgressNotifier


def config_logging(log_dir, log_level, worker_number, execution_env_dir):
    """
    Configure logger for worker and  for every execution environment
    """
    log_dir_path = Path(log_dir)
    log_dir_path.mkdir(exist_ok=True)

    config = {
        'version': 1,
        'disable_existing_loggers': True,
        'formatters': {
            'standard': {
                'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
            },
        },
        'handlers': {
            'worker': {
                'class': 'logging.handlers.RotatingFileHandler',
                'maxBytes': 1024 * 1024 * 10,
                'backupCount': 10,
                'level': log_level,
                'formatter': 'standard',
                'filename': str(log_dir_path / f'worker{worker_number}.log')
            },
            'worker_error': {
                'class': 'logging.handlers.RotatingFileHandler',
                'maxBytes': 1024 * 1024 * 10,
                'backupCount': 10,
                'level': 'ERROR',
                'formatter': 'standard',
                'filename': str(log_dir_path / f'worker_errors.log')
            },
            'exec_env': {
                'class': 'logging.handlers.RotatingFileHandler',
                'maxBytes': 1024 * 1024 * 10,
                'backupCount': 10,
                'level': log_level,
                'formatter': 'standard',
                'filename': str(log_dir_path / f'commands.log')
            },
        },
        'loggers': {
            'worker': {
                'handlers': ['worker', 'worker_error'],
                'level': log_level,
                'propagate': False
            },
            'exec_env': {
                'handlers': ['exec_env', ],
                'level': log_level,
                'propagate': False
            },
        }
    }
    for exec_env in Path(execution_env_dir).iterdir():
        exec_env_name = exec_env.name
        exec_env_log_dir = log_dir_path / exec_env_name
        exec_env_log_dir.mkdir(parents=True, exist_ok=True)
        config['handlers'][exec_env_name] = {
                'class': 'logging.handlers.RotatingFileHandler',
                'maxBytes': 1024 * 1024 * 10,
                'backupCount': 10,
                'level': log_level,
                'formatter': 'standard',
                'filename': str(exec_env_log_dir / f'{exec_env_name}.log')
        }
        config['loggers'][exec_env_name] = {
            'handlers': [exec_env_name],
            'level': log_level,
            'propagate': False
        }
    logging.config.dictConfig(config)


def add_projects_venvs(commands_dir: str):
    """
    Adds to sys.path all projects virtual enviroments
    Project virtual environment is directory in commands director which ends with _venv
    """

    log = logging.getLogger('worker')

    venv_relative_dirs_list = [
        f'lib/python{sys.version_info.major}.{sys.version_info.minor}/site-packages',
        f'lib/python{sys.version_info.major}{sys.version_info.minor}.zip',
        f'lib/python{sys.version_info.major}.{sys.version_info.minor}',
        f'lib/python{sys.version_info.major}.{sys.version_info.minor}/lib-dynload',
    ]

    commands_dir = Path(commands_dir)
    project_venvs = [f for f in commands_dir.resolve().glob('*_venv') if f.is_dir()]

    for project_venv in project_venvs:
        log.info(f'Found project virtual environment: {project_venv}')
        sys.path.extend(
            list(
                map(
                    lambda x: str(project_venv / x),
                    venv_relative_dirs_list
                )
            )
        )
        # run configuration script
        venv_config_file = project_venv / 'config.py'
        if venv_config_file.exists():
            log.info(f'Executing configuration script for {str(project_venv)}')
            exec(open(venv_config_file).read())


def main():
    parser = argparse.ArgumentParser(description='Worker for node job execution')

    parser.add_argument('execution_environments_dir', type=str,
                        help='directory with execution environment packages')
    parser.add_argument('execution_environment', type=str,
                        help='execution environment package')
    parser.add_argument('commands_dir', type=str,
                        help='Directory with user commands for execution environment')
    parser.add_argument('storages_json', type=str,
                        help='Storages dictionary as json')
    parser.add_argument('socket_type', type=str, default='unix', choices=['unix', 'inet'],
                        help='socket type for worker server')
    parser.add_argument('port', type=int,
                        help='port or socket number for worker server')
    parser.add_argument('server_socket_type', type=str, default='unix', choices=['unix', 'inet'],
                        help='server socket type ')
    parser.add_argument('server_port', type=int,
                        help='server port')
    parser.add_argument('run_directory', type=str,
                        help='directory for socket files and pid files')
    parser.add_argument('log_dir', type=str,
                        help='worker logs directory ')
    parser.add_argument('log_level', type=str,
                        help='Log level')

    args = parser.parse_args()

    execution_environments_dir = Path(args.execution_environments_dir)
    if not execution_environments_dir.exists():
        raise ValueError('Execution environment directory doesn\'t exist')

    config_logging(args.log_dir, args.log_level, args.port, execution_environments_dir)

    log = logging.getLogger('worker')

    add_projects_venvs(args.commands_dir)

    storages = json.loads(args.storages_json)

    log.info('get storages: ' + str(storages))

    socket_type = socket.AF_UNIX if args.socket_type == 'unix' else socket.AF_INET
    server_socket_type = socket.AF_UNIX if args.server_socket_type == 'unix' else socket.AF_INET

    run_dir = args.run_directory



    sys.path.append(args.execution_environments_dir)

    server_client = ServerClient(server_socket_type, args.server_port, run_dir)

    progress_notifier = ProgressNotifier(server_client)

    # import command executor
    command_executor_module = importlib.import_module(
        f'{args.execution_environment}.command_executor'
    )
    try:
        command_executor_class = command_executor_module.CommandExecutor
        command_executor = command_executor_class(storages, args.commands_dir, progress_notifier.message)
        log.info(f'Command executor with class {str(command_executor_class)} initialized successfully')
    except Exception as err:
        log.error(f'Fail to initialize command executor {err}')
        log.error(traceback.format_exc())
        return

    log.info(f'socket_type: {socket_type}, port: {args.port}, run_dir: {run_dir}')
    # initialize worker server
    worker_server = WorkerServer(
        socket_type, args.port, command_executor, progress_notifier, run_dir
    )

    log.info(f'Starting worker server with options: execution_environment={args.execution_environment} port={args.port}')
    worker_server.run()


def exit_gracefully(*args):
    log = logging.getLogger('worker')
    log.info('Terminating...')
    exit(0)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, exit_gracefully)
    signal.signal(signal.SIGTERM, exit_gracefully)
    main()




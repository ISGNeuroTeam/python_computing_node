import importlib
import sys
import argparse
import json
import socket
import logging.config

from pathlib import Path

from .worker_server import WorkerServer
from .server_client import ServerClient
from .progress_notify import ProgressNotifier


def config_logging(log_dir, log_level, worker_number):
    """
    Configure worker logger
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
        },
        'loggers': {
            'worker': {
                'handlers': ['worker'],
                'level': log_level,
                'propagate': False
            },
        }
    }
    logging.config.dictConfig(config)


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

    config_logging(args.log_dir, args.log_level, args.port)


    storages = json.loads(args.storages_json)

    socket_type = socket.AF_UNIX if args.socket_type == 'unix' else socket.AF_INET
    server_socket_type = socket.AF_UNIX if args.server_socket_type == 'unix' else socket.AF_INET

    run_dir = args.run_directory

    execution_environments_dir = Path(args.execution_environments_dir)
    if not execution_environments_dir.exists():
        raise ValueError('Execution environment directory doesn\'t exist')

    sys.path.append(args.execution_environments_dir)

    server_client = ServerClient(server_socket_type, args.server_port, run_dir)

    # todo make real progress logger
    progress_notifier = ProgressNotifier(server_client)

    # import command executor
    command_executor_module = importlib.import_module(
        f'{args.execution_environment}.command_executor'
    )

    command_executor_class = command_executor_module.CommandExecutor
    command_executor = command_executor_class(storages, args.commands_dir, progress_notifier.message)

    # initialize worker server
    worker_server = WorkerServer(
        socket_type, args.port, command_executor, progress_notifier, run_dir
    )
    log = logging.getLogger('worker')
    log.info(f'Starting worker server with options: execution_environment={args.execution_environment} port={args.port}')
    worker_server.run()


if __name__ == '__main__':
    main()



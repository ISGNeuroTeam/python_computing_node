import logging
import logging.config
import sys
import signal
import asyncio

from pathlib import Path
from config import ini_config
from server import Server, WorkerProcess, WorkerPool


def config_logging(logging_config):
    """
    Configure server logger
    """
    log_dir_path  = Path(logging_config['log_dir'])
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
            'server': {
                'class': 'logging.handlers.RotatingFileHandler',
                'maxBytes': 1024 * 1024 * int(logging_config['rotation_size']),
                'backupCount': logging_config['keep_files'],
                'level': logging_config['level'],
                'formatter': 'standard',
                'filename': str(log_dir_path / 'server.log')
            },
        },
        'loggers': {
            'server': {
                'handlers': ['server'],
                'level': logging_config['level'],
                'propagate': False
            },
        }
    }
    logging.config.dictConfig(config)


async def main_coroutine():

    # read config
    workers_count = int(ini_config['worker']['workers'])
    start_port = int(ini_config['worker']['start_port'])
    memory_limit = int(ini_config['worker']['memory_limit']) * 1024 * 1024
    proc_num_limit = int(ini_config['worker']['proc_num_limit'])
    spawn_method = ini_config['worker']['spawn_method']
    socket_type = ini_config['worker']['socket_type']

    server_config = ini_config['server']
    server_port = int(ini_config['server']['port'])
    server_socket_type = ini_config['server']['socket_type']
    run_dir = ini_config['server']['run_dir']
    log_dir = ini_config['logging']['log_dir']
    log_level = ini_config['logging']['level']

    execution_environment = ini_config['execution_environment']['package']
    commands_dir = ini_config['execution_environment']['commands_dir']

    storages = ini_config['storages']

    # add execution environment directory to sys
    execution_environment_dir = ini_config['execution_environment']['execution_environment_dir']
    sys.path.append(execution_environment_dir)

    worker_pool = None
    server = None

    log = logging.getLogger('server')
    try:
        worker_base_process = WorkerProcess(
            spawn_method,
            proc_num_limit, memory_limit,
            execution_environment_dir, execution_environment,
            commands_dir,
            storages,
            socket_type, start_port,
            server_socket_type, server_port, run_dir, log_dir, log_level
        )

        worker_pool = WorkerPool(
            worker_base_process, workers_count, start_port
        )

        server = Server(
            {
                'producer': ini_config['kafka_producer'],
                'consumer': ini_config['kafka_consumer'],
            },
            server_config,
            ini_config['computing_node'], worker_pool,
        )
        log.info('Starting server...')
        await server.run()

    except asyncio.CancelledError:
        log.info('Gracefully stopping server')
        if worker_pool is not None:
            await worker_pool.terminate()
        if server is not None:
            await server.stop()


async def main():
    main_task = asyncio.create_task(main_coroutine())
    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGINT, main_task.cancel)
    loop.add_signal_handler(signal.SIGTERM, main_task.cancel)
    await main_task

if __name__ == "__main__":
    config_logging(ini_config['logging'])
    asyncio.run(main())

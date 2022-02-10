import logging
import sys
import signal
import asyncio

from config import ini_config
from server import Server, WorkerProcess, WorkerPool

log = logging.getLogger(__name__)


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

    execution_environment = ini_config['execution_environment']['package']
    commands_dir = ini_config['execution_environment']['commands_dir']

    storages = ini_config['storages']

    # add execution environment directory to sys
    execution_environment_dir = ini_config['execution_environment']['execution_environment_dir']
    sys.path.append(execution_environment_dir)

    worker_pool = None
    server = None

    try:
        worker_base_process = WorkerProcess(
            spawn_method,
            proc_num_limit, memory_limit,
            execution_environment_dir, execution_environment,
            commands_dir,
            storages,
            socket_type, start_port,
            server_socket_type, server_port, run_dir
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

        await server.run()

    except asyncio.CancelledError:
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
    log.info('Computing node server started')
    asyncio.run(main())

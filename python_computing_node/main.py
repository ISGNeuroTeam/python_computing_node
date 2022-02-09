import logging
import sys
import signal
import asyncio

from config import ini_config
from server import Server, WorkerProcess, WorkerPool

log = logging.getLogger(__name__)


async def main():

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

    # to ensure that try / finally block will be executed and __exit__ methods of contex manager
    def terminate_handler(signum, frame):
        log.info('server shutdown')
        worker_pool.terminate()
        asyncio.wait_for(server.stop())
        sys.exit(0)

    signal.signal(signal.SIGTERM, terminate_handler)
    signal.signal(signal.SIGINT, terminate_handler)

    await server.run()


if __name__ == "__main__":
    log.info('Post processing server started')
    asyncio.run(main())

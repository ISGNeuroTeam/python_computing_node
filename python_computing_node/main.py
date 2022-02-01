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
    memory_limit = int(ini_config['worker']['memory_limit'])
    proc_num_limit = int(ini_config['worker']['proc_num_limit'])
    spawn_method = ini_config['worker']['spawn_method']

    inter_proc_storage = ini_config['mounts']['inter_proc_storage']
    shared_storage = ini_config['mounts']['shared_storage']
    local_storage = ini_config['mounts']['local_storage']

    # add execution environment directory to sys

    execution_environment_dir = ini_config['execution_environment']['execution_environment_dir']
    sys.path.append(execution_environment_dir)

    worker_base_process = WorkerProcess(
        spawn_method, start_port, proc_num_limit, memory_limit, inter_proc_storage, shared_storage, local_storage
    )

    worker_pool = WorkerPool(
        worker_base_process, workers_count, start_port
    )

    server = Server(
        ini_config['computing_node'], worker_pool,
        ini_config['execution_environment']['package'],
        ini_config['mounts'],
        {
            'producer': ini_config['kafka_producer'],
            'consumer': ini_config['kafka_consumer'],
        }
    )

    # to ensure that try / finally block will be executed and __exit__ methods of contex manager
    def terminate_handler(signum, frame):
        log.info('server shutdown')

        # TODO change to server.terminate()
        worker_pool.terminate()

        sys.exit(0)

    signal.signal(signal.SIGTERM, terminate_handler)

    await server.run()







if __name__ == "__main__":
    log.info('Post processing server started')
    asyncio.run(main())

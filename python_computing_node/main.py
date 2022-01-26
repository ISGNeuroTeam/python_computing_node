import logging
import sys
import signal
import asyncio
from config import ini_config

from server import Server
from server import WorkerPool

log = logging.getLogger(__name__)


async def main():


    # read config
    print(ini_config)

    workers_number = int(ini_config['worker']['workers'])
    start_port = int(ini_config['worker']['start_port'])
    memory_limit = int(ini_config['worker']['memory_limit'])
    proc_num_limit = int(ini_config['worker']['proc_num_limit'])
    spawn_method = ini_config['worker']['spawn_method']

    inter_proc_storage = ini_config['mounts']['inter_proc_storage']
    shared_storage = ini_config['mounts']['shared_storage']
    local_storage = ini_config['mounts']['local_storage']

    worker_pool = WorkerPool(
        workers_number, spawn_method, start_port, proc_num_limit, memory_limit,
        inter_proc_storage, shared_storage, local_storage
    )

    server = Server(worker_pool)

    # to ensure that try / finally block will be executed and __exit__ methods of contex manager
    def terminate_handler(signum, frame):
        log.info('server shutdown')
        worker_pool.terminate()
        sys.exit(0)

    signal.signal(signal.SIGTERM, terminate_handler)

    await server.run()







if __name__ == "__main__":
    log.info('Post processing server started')
    asyncio.run(main())

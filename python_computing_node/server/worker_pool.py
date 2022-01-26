import asyncio

from .worker_process import WorkerProcess


class WorkerPool:
    def __init__(self, workers_number, spawn_method, start_port, proc_num_limit, memory_limit,
                 inter_proc_storage, shared_storage, local_storage,
    ):

        self._current_port = start_port - 1 # get_port function do increment

        # the list of workers
        self._worker_processes = self._create_workers(
            workers_number, spawn_method, proc_num_limit, memory_limit,
            inter_proc_storage, shared_storage, local_storage
        )

    def _create_workers(
            self, workers_number, spawn_method, proc_num_limit, memory_limit,
            inter_proc_storage, shared_storage, local_storage
    ):
        worker_processes = []
        for _ in range(workers_number):
            worker_proc = WorkerProcess(
                spawn_method, self._get_port_for_new_worker(), proc_num_limit, memory_limit,
                inter_proc_storage, shared_storage, local_storage
            )
            worker_processes.append(worker_proc)
        return worker_processes

    def _get_port_for_new_worker(self):
        self._current_port += 1
        return self._current_port

    async def run_worker_process_forever(self, worker_process):
        """
        Spawn worker process
        """
        while True:
            returned_code, stderr = await worker_process.spawn()

            # change port before restart
            worker_process.change_port(self._get_port_for_new_worker())

            print(f'Process exited with code {returned_code}\n {stderr}')
            await asyncio.sleep(5)

    async def run_worker_processes_forever(self):
        for worker_process in self._worker_processes:
            asyncio.create_task(self.run_worker_process_forever(worker_process))

    def terminate(self):
        """
        Terminate all workers gracefully
        """
        pass

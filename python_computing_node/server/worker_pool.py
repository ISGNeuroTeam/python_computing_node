import asyncio
from copy import copy

from .worker_process import WorkerProcess


class WorkerPool:
    def __init__(self, worker_base_process, workers_count, start_port):

        self._current_port = start_port - 1  # get_port function do increment
        self._workers_count = workers_count
        self._worker_base_process = worker_base_process

        # the list of workers
        self._worker_processes = self._create_workers(
            worker_base_process, workers_count
        )

        self._free_workers_indexes = set([i for i in range(workers_count)])

        # dictionary with node job uuid for every worker
        self._current_worker_jobs = {i: None for i in range(workers_count)}

    def _create_workers(
            self, worker_base_process, workers_count
    ):
        worker_processes = []
        for _ in range(workers_count):
            worker_proc = copy(worker_base_process)
            worker_proc.change_port(self._get_port_for_new_worker())
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

    async def make_job(self, node_job: dict):
        """
        Chose a worker and send job to it
        awaits result and return it
        """
        free_worker_index = self._free_workers_indexes.pop()
        self._current_worker_jobs[free_worker_index] = node_job['uuid']

        resp = await self._worker_processes[free_worker_index].send_job(node_job)

        self._free_workers_indexes.add(free_worker_index)
        self._current_worker_jobs[free_worker_index] = None

        return resp['status'], resp['message']

    async def _send_node_node_job_to_worker(self, node_job, worker_port):
        pass

    def get_free_workers_count(self):
        """
        Returns number of free workers
        """
        return len(self._free_workers_indexes)

    def get_workers_count(self):
        """
        Returns total workers count
        """
        return self._workers_count

    def terminate(self):
        """
        Terminate all workers gracefully
        """
        for worker_process in self._worker_processes:
            worker_process.terminate()

import asyncio
import logging

from copy import copy

from .worker_process import WorkerProcess
from .timings import WORKER_PROCESS_TERMINATE_TIME, WORKER_PROCESS_SPAWN_TIME

log = logging.getLogger('server')


class WorkerPool:
    def __init__(self, worker_base_process: WorkerProcess, workers_count: int, start_port: int):

        self._current_port = start_port - 1  # get_port function do increment
        self._workers_count = workers_count
        self._worker_base_process = worker_base_process

        # list of workers
        self._worker_processes = self._create_workers(
            worker_base_process, workers_count
        )

        # list of asyncio tasks for each worker process
        self._worker_async_tasks = [None]*self._workers_count

        # set of free indexes
        self._free_workers_indexes = set([i for i in range(workers_count)])

        # dictionary with node job uuid for every worker
        self._current_worker_jobs = {i: None for i in range(workers_count)}

        # dictionary to store worker index for node job
        self._node_job_worker_index = dict()

        # set with canceled node job uuids
        self.canceled_node_job_uuid = set()

    def _reserve_worker_for_job(self, job_uuid):
        """
        Returns free worker process instance for job and denotes it as bysy
        """
        free_worker_index = self._free_workers_indexes.pop()
        self._current_worker_jobs[free_worker_index] = job_uuid
        self._node_job_worker_index[job_uuid] = free_worker_index
        return self._worker_processes[free_worker_index]

    def _release_worker(self, job_uuid):
        """
        Denotes worker as free worker
        """
        worker_index = self._node_job_worker_index[job_uuid]
        self._free_workers_indexes.add(worker_index)
        self._current_worker_jobs[worker_index] = None
        del self._node_job_worker_index[job_uuid]

    def _get_worker_for_job(self, job_uuid):
        return self._node_job_worker_index[job_uuid]

    @staticmethod
    def _create_workers(
            worker_base_process, workers_count
    ):
        worker_processes = []
        for _ in range(workers_count):
            worker_proc = copy(worker_base_process)
            worker_processes.append(worker_proc)
        return worker_processes

    def _get_port_for_new_worker(self):
        self._current_port += 1
        return self._current_port

    async def run_worker_process_forever(self, worker_process):
        """
        Spawn worker process
        """
        try:
            while True:
                # change port before start
                worker_process.change_port(self._get_port_for_new_worker())

                returned_code, stderr = await worker_process.spawn()
                log.info(f'Process exited with code {returned_code}\n {stderr}')

        except asyncio.CancelledError:
            await worker_process.terminate()
            log.info(f'worker terminated')

    def run_worker_processes_forever(self):
        for i in range(self._workers_count):
            self._worker_async_tasks[i] = asyncio.create_task(
                self.run_worker_process_forever(self._worker_processes[i])
            )

    async def make_job(self, node_job: dict):
        """
        Chose a worker and send job to it
        awaits result and return it
        """
        worker_process = self._reserve_worker_for_job(node_job['uuid'])
        resp = await worker_process.send_job(node_job)
        self._release_worker(node_job['uuid'])

        # if node job was canceled ignore fail status

        if resp['status'] == 'FAILED' and (node_job['uuid'] in self.canceled_node_job_uuid):
            resp['status'] = 'CANCELED'
            resp['status_text'] = 'Node job was canceled successfully'
            self.canceled_node_job_uuid.discard(node_job['uuid'])

        return resp['status'], resp['status_text']

    async def cancel_job(self, node_job: dict):
        """
        Terminates worker process running node job
        """
        log.info(f'Cancel job {node_job["uuid"]}')
        self.canceled_node_job_uuid.add(node_job["uuid"])

        worker_index = self._node_job_worker_index[node_job["uuid"]]

        # cancel task with worker
        self._worker_async_tasks[worker_index].cancel()

        await asyncio.sleep(WORKER_PROCESS_TERMINATE_TIME)
        log.info(f'Worker with index {worker_index} stopped')

        # and start a new one
        self._worker_async_tasks[worker_index] = asyncio.create_task(
            self.run_worker_process_forever(self._worker_processes[worker_index])
        )
        await asyncio.sleep(WORKER_PROCESS_SPAWN_TIME)
        log.info(f'Worker with index {worker_index} started')

        self._release_worker(node_job['uuid'])

    async def get_command_syntax(self):
        return await self._worker_processes[0].get_command_syntax()

    async def _send_node_node_job_to_worker(self, node_job, worker_port):
        pass

    def get_free_workers_count(self):
        """
        Returns number of free workers
        """
        return len(self._free_workers_indexes)

    def get_used_workers_count(self):
        return self._workers_count - len(self._free_workers_indexes)

    def get_workers_count(self):
        """
        Returns total workers count
        """
        return self._workers_count

    async def terminate(self):
        """
        Terminate all workers gracefully
        """
        for worker_process in self._worker_processes:
            await worker_process.terminate()

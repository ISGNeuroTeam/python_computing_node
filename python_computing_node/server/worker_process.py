import asyncio

from pathlib import Path

BASE_SOURCE_DIR = Path(__file__).resolve().parent.parent
worker_DIR = BASE_SOURCE_DIR / 'worker'


class WorkerProcess:
    def __init__(self, spawn_method, port, proc_num_limit, memory_limit, inter_proc_storage, shared_storage, local_storage):
        """
        :param spawn_method: ulimit, docker, or podman
        :param proc_num_limit: max number of processes in worker
        :param memory_limit: max memory usage in worker
        """
        self.spawn_method = spawn_method
        self.port = port
        self.proc_num_limit = proc_num_limit
        self.memory_limit = memory_limit
        self.inter_proc_storage = inter_proc_storage
        self.shared_storage = shared_storage
        self.local_storage = local_storage

        self.command = self.create_launch_command()
        self.proc = None

    def create_launch_command(self):

        if self.spawn_method == 'ulimit':
            ulimit_memory_limit = memory_limit = self.memory_limit * 1024 * 1024
            command = f'bash -c "export PYTHONPATH={str(BASE_SOURCE_DIR)} && ulimit -SH -u {self.proc_num_limit} -d {ulimit_memory_limit} && python -m worker {self.port} {self.inter_proc_storage} {self.shared_storage} {self.local_storage}" '

        elif self.spawn_method == 'docker':
            command = f'docker run -m {self.memory_limit}m --pids-limit {self.proc_num_limit + 1} -v {str(worker_DIR)}:/worker/worker -v {self.local_storage}:/worker/local_storage -v {self.shared_storage}:/worker/shared_storage -p {self.port}:{self.port} worker python -m worker {self.port} {self.inter_proc_storage} {self.shared_storage} {self.local_storage}'

        else:
            raise ValueError('Unknown spawn method')

        return command

    async def spawn(self):
        """
        Launch worker process and await ending
        Returns code and stderr output
        """
        print(self.command)
        self.proc = await asyncio.create_subprocess_shell(
            self.command, stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE
        )
        await self.proc.wait()
        return self.proc.returncode, self.proc.stderr

    def change_port(self, new_port):
        self.port = new_port
        self.command = self.create_launch_command()

    def terminate(self):
        if self.proc is not None and self.proc.returncode:
            self.proc.terminate()

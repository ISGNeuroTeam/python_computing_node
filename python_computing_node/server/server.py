import asyncio


class Server:
    def __init__(self, worker_pool):
        self._worker_pool = worker_pool

    async def run(self):
        await self._worker_pool.run_worker_processes_forever()
        await asyncio.sleep(10000)





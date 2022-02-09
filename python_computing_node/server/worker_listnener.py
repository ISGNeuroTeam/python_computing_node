from aiohttp import web
from pathlib import Path


BASE_SOURCE_DIR = Path(__file__).resolve().parent.parent
RUN_DIR = BASE_SOURCE_DIR.parent / 'run'


class WorkerListener:
    """
    Simple aiohttp server for listening worker requests
    """
    def __init__(self, socket_type, port, run_dir, job_status_handler):
        """
        :param socket_type: 'unix' or 'inet' string
        :param port: port for web server
        :param job_status_handler: coroutine with arguments node_job_uuid, status, message
        :param run_dir: directory with socket and pid files
        """
        self.socket_type = socket_type
        self.port = port
        self.job_status_handler = job_status_handler
        self.run_dir = run_dir

        self.app = self._create_aiohttp_app()
        self.app_runner = None

    def _create_aiohttp_app(self):
        app = web.Application()
        app.add_routes(
            [web.post('/job_status', self._job_status_endpoint)]
        )
        return app

    async def _job_status_endpoint(self, request):
        data = await request.json()
        await self.job_status_handler(data['uuid'], data['status'], data['message'])
        return web.json_response({'status': 'ok'})

    async def start(self):
        """
        Start aiohttp server
        """
        app_runner = web.AppRunner(self.app)
        await app_runner.setup()
        if self.socket_type == 'unix':
            site = web.UnixSite(app_runner, path=str(Path(self.run_dir) / f'server{self.port}.socket'))
        elif self.socket_type == 'inet':
            site = web.TCPSite(app_runner, port=self.port)
        else:
            raise ValueError()

        await site.start()

    async def stop(self):
        await self.app_runner.cleanup()

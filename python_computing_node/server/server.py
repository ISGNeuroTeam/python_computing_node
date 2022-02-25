import json
import asyncio

from aiokafka import AIOKafkaProducer as Producer, AIOKafkaConsumer as Consumer

from .worker_listnener import WorkerListener
from .timings import WORKER_POOL_SPAWN_TIME, KAFKA_WAIT_TIME

COMPUTING_NODE_CONTROL_TOPIC = 'computing_node_control'


class Server:
    def __init__(
            self, kafka_config, server_config, computing_node_config, worker_pool, 
    ):
        """
        :param kafka_config: config dictionary for kafka
        :param server_config: config dictionary (socket type and port) for communicating with workers
        :param computing_node_config: computing node server configuration
        :param worker_pool: worker pool object for making job
        """
        self._worker_pool = worker_pool
        self._kafka_config = kafka_config
        self._worker_listener = WorkerListener(
            server_config['socket_type'],
            server_config['port'],
            server_config['run_dir'],
            self._job_status_handler
        )
        self._computing_node_config = computing_node_config

        # tasks will be defined in start method
        self._consuming_task = None
        self._worker_listener_task = None
        self._worker_processes_task = None

        self._job_topic = f"{self._computing_node_config['uuid']}_job"
        self._producer = Producer(
            bootstrap_servers=kafka_config['producer']['bootstrap_servers']
        )

    async def _get_command_syntax(self):
        """
        Request commands syntax from worker pool
        """
        return await self._worker_pool.get_command_syntax()

    async def _register(self):
        commands_syntax = await self._get_command_syntax()

        register_command = {
            'computing_node_type': self._computing_node_config['type'],
            'host_id': self._computing_node_config['host_id'],
            'otl_command_syntax': commands_syntax,
            'resources': {
                'workers': self._worker_pool.get_workers_count()
            }
        }

        control_command = {
            'computing_node_uuid': self._computing_node_config['uuid'],
            'command_name': 'REGISTER_COMPUTING_NODE',
            'command': register_command,
        }
        await self._producer.send(COMPUTING_NODE_CONTROL_TOPIC, json.dumps(control_command).encode())

    async def _unregister(self):
        unregister_command = {}
        control_command = {
            'computing_node_uuid': self._computing_node_config['uuid'],
            'command_name': 'UNREGISTER_COMPUTING_NODE',
            'command': unregister_command,
        }
        await self._producer.send(COMPUTING_NODE_CONTROL_TOPIC, json.dumps(control_command).encode())

    async def _start_job_consuming(self):
        job_consumer = Consumer(
            self._job_topic,
            bootstrap_servers=self._kafka_config['consumer']['bootstrap_servers'],
            group_id=self._kafka_config['consumer']['group_id'],
            value_deserializer=json.loads
        )
        await job_consumer.start()
        try:
            async for job_message in job_consumer:
                asyncio.create_task(self._run_job(job_message.value))
        finally:
            await job_consumer.stop()

    async def _run_job(self, job):
        """
        Async task for running new node job
        """
        if job['status'] == 'CANCELED':
            await self._worker_pool.cancel_job(job)
            return

        if self._worker_pool.get_free_workers_count() == 0:
            await self._send_node_job_status(
                job['uuid'],
                'DECLINED_BY_COMPUTING_NODE',
                f"Node job was declined, all workers are busy",
            )
            return

        await self._send_node_job_status(
            job['uuid'],
            'RUNNING',
            f"job with uuid {job['uuid']} is being sent to worker pool",
        )
        status, message = await self._worker_pool.make_job(job)

        # report about resource is free
        await self._send_resources()

        await self._send_node_job_status(
            job['uuid'],
            status,
            message,
        )

    async def _send_node_job_status(
        self, node_job_uuid, status, status_text=None
    ):
        message = {
            'uuid': node_job_uuid,
            'status': status,
            'status_text': status_text,
        }
        await self._producer.send('nodejob_status', json.dumps(message).encode())

    async def _send_resources(self):
        cur_resource_usage = {
            'workers': self._worker_pool.get_used_workers_count()
        }
        resource_command = {
            'resources': cur_resource_usage
        }

        control_command = {
            'computing_node_uuid': self._computing_node_config['uuid'],
            'command_name': 'RESOURCE_STATUS',
            'command': resource_command,
        }
        await self._producer.send(COMPUTING_NODE_CONTROL_TOPIC, json.dumps(control_command).encode())

    async def _send_resources_task(self):
        while True:
            await asyncio.sleep(int(self._computing_node_config['health_check_interval']))
            await self._send_resources()

    async def _job_status_handler(self, uuid, status, message):
        """
        Callback for worker job status message
        """
        await self._send_node_job_status(uuid, status, message)

    async def start(self):
        await self._producer.start()

        # start listener for job status
        self._worker_listener_task = asyncio.create_task(self._worker_listener.start())

        # launch workers
        self._worker_pool.run_worker_processes_forever()

        # wait for worker pool
        await asyncio.sleep(WORKER_POOL_SPAWN_TIME)

        # send register message to message queue
        await self._register()

        # periodically send resources to dispatcher
        asyncio.create_task(self._send_resources_task())

        # main task for job consuming
        self._consuming_task = asyncio.create_task(self._start_job_consuming())

        # waiting for kafka topic auto creation
        await asyncio.sleep(KAFKA_WAIT_TIME)

        await asyncio.gather(self._consuming_task, self._worker_listener_task)

    async def stop(self):
        await self._unregister()
        await self._producer.stop()
        await self._worker_listener.stop()

    async def run(self):
        await self.start()






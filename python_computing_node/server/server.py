import json
import importlib

import asyncio

from aiokafka import AIOKafkaProducer as Producer, AIOKafkaConsumer as Consumer


class Server:
    def __init__(
            self, computing_node_config, worker_pool, execution_environment_package,
            command_executor_config, kafka_config,
    ):
        """
        :computing_node_config: computing node server configuration
        :param worker_pool: worker pool object for making job
        :execution_environment_package: package containing CommandExecutor class
        :command_executor_config: config dictionary for comand executor
        :kafka_config: config dictionary for kafka
        """
        self._worker_pool = worker_pool
        self._kafka_config = kafka_config
        self._computing_node_config = computing_node_config
        self._config = computing_node_config

        self._command_execuor_config = command_executor_config
        self.consuming_task = None

        self._commands_syntax = self._get_commands_syntax(execution_environment_package)

        self._job_topic = f"{self._config['uuid']}_job"
        self._producer = Producer(
            bootstrap_servers=kafka_config['producer']['bootstrap_servers']
        )

        asyncio.create_task(self._send_resources_task())

    def _get_commands_syntax(self, execution_environment_package):
        """
        Load command executor from execution environment and returns commands syntax dictionary
        """
        # import command executor class from execution_environment and initialize it
        import sys
        print(sys.path)
        command_executor_module = importlib.import_module(execution_environment_package)
        command_executor_class = command_executor_module.CommandExecutor
        command_executor = command_executor_class(*self._command_execuor_config)
        return command_executor.get_commands_syntax()

    async def _register(self):
        register_command = {
            'computing_node_type': self._config['type'],
            'host_id': self._config['host_id'],
            'otl_command_syntax': self._commands_syntax,
            'resources': {
                'workers': self._worker_pool.get_workers_count()
            }
        }

        control_command = {
            'computing_node_uuid': self._config['uuid'],
            'command_name': 'REGISTER_COMPUTING_NODE',
            'command': register_command,
        }
        await self._producer.send('computing_node_control', json.dumps(control_command).encode())

    async def _unregister(self):
        unregister_command = {}
        control_command = {
            'computing_node_uuid': self._config['uuid'],
            'command_name': 'UNREGISTER_COMPUTING_NODE',
            'command': unregister_command,
        }
        await self._producer.send('computing_node_control', json.dumps(control_command).encode())

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
                print(job_message.value)
                asyncio.create_task(self._run_job(job_message.value))
        finally:
            await job_consumer.stop()

    async def _run_job(self, job):
        """
        Async task for running new node job
        """
        if self._worker_pool.get_free_workers_count() == 0:
            await self._send_node_job_status(
                job['uuid'],
                'DECLINED_BY_COMPUTING_NODE',
                f"Node job was declined, all workers are busy",
            )

        await self._send_node_job_status(
            job['uuid'],
            'RUNNING',
            f"job with uuid {job['uuid']} is being sent to worker pool",
        )
        status, message = await self._worker_pool.make_job(job)
        if status == 'FINISHED':
            # send status job done
            await self._send_node_job_status(
                job['uuid'],
                'FINISHED',
                f"Node job {job['uuid']} successfully finished. {message}",

            )
        else:
            # send job fail
            await self._send_node_job_status(
                job['uuid'],
                'FAILED',
                f"Node job {job['uuid']} failed. {message}",
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
            'workers': self._worker_pool.get_free_workers_count()
        }
        resource_command = {
            'resources': cur_resource_usage
        }

        control_command = {
            'computing_node_uuid': self._config['uuid'],
            'command_name': 'RESOURCE_STATUS',
            'command': resource_command,
        }
        await self._producer.send('computing_node_control', json.dumps(control_command).encode())

    async def _send_resources_task(self):
        while True:
            await self._send_resources()
            await asyncio.sleep(int(self._computing_node_config['health_check_interval']))

    async def start(self):
        await self._producer.start()
        await self._register()
        self.consuming_task = asyncio.create_task(self._start_job_consuming())
        await self.consuming_task

    async def stop(self):
        await self._unregister()
        await self._producer.stop()

    async def run(self):
        asyncio.create_task(self._worker_pool.run_worker_processes_forever())
        await self.start()





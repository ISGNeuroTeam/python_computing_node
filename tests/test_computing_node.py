import unittest
import json
import time

from config import ini_config
from server.timings import WORKER_PROCESS_RESTART_TIME

from kafka import KafkaConsumer, KafkaProducer


class TestComputingNode(unittest.TestCase):

    def setUp(self) -> None:
        self.computing_node_control_consumer = KafkaConsumer(
            'computing_node_control',
            auto_offset_reset='earliest',
            bootstrap_servers=ini_config['kafka_consumer']['bootstrap_servers'],
            group_id=ini_config['kafka_consumer']['group_id']
        )

        self.node_job_status_consumer = KafkaConsumer(
            'nodejob_status',
            auto_offset_reset='earliest',
            bootstrap_servers=ini_config['kafka_consumer']['bootstrap_servers'],
            group_id=ini_config['kafka_consumer']['group_id']
        )

        self.producer = KafkaProducer(
            bootstrap_servers=ini_config['kafka_consumer']['bootstrap_servers']
        )

    def _send_job(self, commands, job_uuid):
        test_node_job_topic = '99999999999999999999999999999999_job'

        message = {
            "uuid": job_uuid,
            "computing_node_type": "SPARK",
            "status": "READY_TO_EXECUTE",
            "commands": commands
        }

        value = json.dumps(message).encode()
        self.producer.send(test_node_job_topic, value=value)

    def _cancel_job(self, job_uuid):
        test_node_job_topic = '99999999999999999999999999999999_job'

        message = {
            "uuid": job_uuid,
            "status": "CANCELED",
        }

        value = json.dumps(message).encode()
        self.producer.send(test_node_job_topic, value=value)

    def tearDown(self) -> None:
        self.computing_node_control_consumer.close()
        self.node_job_status_consumer.close()
        self.producer.close()

    def test1_register(self):
        consumer = self.computing_node_control_consumer

        msg = next(consumer)
        msg = json.loads(msg.value)

        # first message is register command
        self.assertEqual(msg['command_name'], 'REGISTER_COMPUTING_NODE')
        command = msg['command']
        self.assertEqual(command['host_id'], 'test_host_id')
        syntax = command['otl_command_syntax']
        commands_name_set_from_response = set(syntax.keys())
        commands_name_set = {'normal_command', 'error_command', 'subsearch_command', 'command_with_threads'}
        self.assertSetEqual(commands_name_set_from_response, commands_name_set)
        # second message is resource message
        msg = next(consumer)
        msg = json.loads(msg.value)
        self.assertEqual(msg['command_name'], 'RESOURCE_STATUS')

    def test2_execution(self):
        # send node job with two normal command
        commands = [{"name": "normal_command", "arguments": {"stages": [{"value": 3, "key": "stages", "type": "integer", "named_as": "", "group_by": [], "arg_type": "arg"}], "stage_time": [{"value": 1, "key": "stage_time", "type": "integer", "named_as": "", "group_by": [], "arg_type": "arg"}]}}, {"name": "normal_command", "arguments": {"stages": [{"value": 2, "key": "stages", "type": "integer", "named_as": "", "group_by": [], "arg_type": "arg"}], "stage_time": [{"value": 1, "key": "stage_time", "type": "integer", "named_as": "", "group_by": [], "arg_type": "arg"}]}}]

        self._send_job(commands, "00000000000000000000000000000001")

        consumer = self.node_job_status_consumer

        # check that first 10 message is job status message with status RUNNING
        for _ in range(10):
            msg = next(consumer)
            msg_dict = json.loads(msg.value)
            print(msg_dict)
            self.assertEqual(msg_dict['status'], 'RUNNING')

        # the last one is FINISHED
        msg = next(consumer)
        msg_dict = json.loads(msg.value)
        print(msg_dict)
        self.assertEqual(msg_dict['status'], 'FINISHED')

    def test3_error_command(self):
        job_uuid = "000000000000000000000000000error"
        commands = [{"name": "error_command", "arguments": {}}]
        self._send_job(commands, job_uuid)

        # first message with running status
        msg = next(self.node_job_status_consumer)
        msg_dict = json.loads(msg.value)
        print(msg_dict)
        self.assertEqual(msg_dict['status'], 'RUNNING')

        # second message with fail
        # first message with running status
        msg = next(self.node_job_status_consumer)
        msg_dict = json.loads(msg.value)
        print(msg_dict)
        self.assertEqual(msg_dict['status'], 'FAILED')

    def test4_decline_status(self):
        # very long command
        commands = [{"name": "normal_command", "arguments": {"stages": [{"value": 1, "key": "stages", "type": "integer", "named_as": "", "group_by": [], "arg_type": "arg"}], "stage_time": [{"value": 100000, "key": "stage_time", "type": "integer", "named_as": "", "group_by": [], "arg_type": "arg"}]}}]

        # make 4 jobs which takes all workers
        self._send_job(commands, "00000000000000000000000000000011")
        self._send_job(commands, "00000000000000000000000000000012")
        self._send_job(commands, "00000000000000000000000000000013")
        self._send_job(commands, "00000000000000000000000000000014")

        # the last one is declined
        self._send_job(commands, "00000000000000000000000000000015")

        for i in range(9):
            msg = next(self.node_job_status_consumer)
            msg_dict = json.loads(msg.value)
            print(msg_dict)
            if msg_dict['uuid'] == "00000000000000000000000000000015":
                self.assertEqual(msg_dict['status'], 'DECLINED_BY_COMPUTING_NODE')

        self._cancel_job("00000000000000000000000000000011")

        # waiting for cancel and restarting process
        time.sleep(WORKER_PROCESS_RESTART_TIME)

        msg = next(self.node_job_status_consumer)
        msg_dict = json.loads(msg.value)
        print(msg_dict)
        self.assertEqual(msg_dict['uuid'], "00000000000000000000000000000011")
        self.assertEqual(msg_dict['status'], 'CANCELED')

        # now must not be declined
        self._send_job(commands, "00000000000000000000000000000016")

        for i in range(2):
            msg = next(self.node_job_status_consumer)
            msg_dict = json.loads(msg.value)
            print(msg_dict)
            self.assertEqual(msg_dict['uuid'], "00000000000000000000000000000016")
            self.assertEqual(msg_dict['status'], 'RUNNING')


if __name__ == '__main__':
    unittest.main()

import unittest
import json

from config import ini_config

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

    def tearDown(self) -> None:
        self.computing_node_control_consumer.close()
        self.node_job_status_consumer.close()

    def test_register(self):
        consumer = self.computing_node_control_consumer

        msg = next(consumer)
        msg = json.loads(msg.value)

        # first message is register command
        self.assertEqual(msg['command_name'], 'REGISTER_COMPUTING_NODE')
        command = msg['command']
        self.assertEqual(command['host_id'], 'test_host_id')
        syntax = command['otl_command_syntax']
        commands_name_set_from_response = set(syntax.keys())
        commands_name_set = {'normal_command', 'error_command', 'subsearch_command'}
        self.assertSetEqual(commands_name_set_from_response, commands_name_set)
        # second message is resource message
        msg = next(consumer)
        msg = json.loads(msg.value)
        self.assertEqual(msg['command_name'], 'RESOURCE_STATUS')

    def test_execution(self):
        producer = KafkaProducer(
            bootstrap_servers=ini_config['kafka_consumer']['bootstrap_servers']
        )
        test_node_job_topic = '99999999999999999999999999999999_job'

        # send node job with two normal command
        commands = [{"name": "normal_command", "arguments": {"stages": [{"value": 3, "key": "stages", "type": "integer", "named_as": "", "group_by": [], "arg_type": "arg"}], "stage_time": [{"value": 1, "key": "stage_time", "type": "integer", "named_as": "", "group_by": [], "arg_type": "arg"}]}}, {"name": "normal_command", "arguments": {"stages": [{"value": 2, "key": "stages", "type": "integer", "named_as": "", "group_by": [], "arg_type": "arg"}], "stage_time": [{"value": 1, "key": "stage_time", "type": "integer", "named_as": "", "group_by": [], "arg_type": "arg"}]}}]
        message = {
            "uuid": "a7dcc379f3594323b6cd11f3f235e082",
            "computing_node_type": "SPARK",
            "status": "READY_TO_EXECUTE",
            "commands": commands
        }

        value = json.dumps(message).encode()
        producer.send(test_node_job_topic, value=value)

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


if __name__ == '__main__':
    unittest.main()

import unittest
import json

from config import ini_config

from kafka import KafkaConsumer


class TestComputingNode(unittest.TestCase):

    def test_register(self):
        consumer = KafkaConsumer(
            'computing_node_control',
            auto_offset_reset='earliest',
            bootstrap_servers=ini_config['kafka_consumer']['bootstrap_servers'],
            group_id=ini_config['kafka_consumer']['group_id']
        )

        msg = next(consumer)
        msg = json.loads(msg.value)

        # first message is register command
        self.assertEqual(msg['command_name'], 'REGISTER_COMPUTING_NODE')
        command = msg['command']
        self.assertEqual(command['host_id'], 'test_host_id')

        # second message is resource message
        msg = next(consumer)
        msg = json.loads(msg.value)
        self.assertEqual(msg['command_name'], 'RESOURCE_STATUS')


if __name__ == '__main__':
    unittest.main()

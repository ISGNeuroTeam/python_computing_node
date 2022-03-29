#!/bin/bash

# Start zookeeper
/kafka/kafka_2.13-3.0.0/bin/zookeeper-server-start.sh /kafka/kafka_2.13-3.0.0/config/zookeeper.properties &

# Start kafka
/kafka/kafka_2.13-3.0.0/bin/kafka-server-start.sh /kafka/kafka_2.13-3.0.0/config/server.properties & _pid=$! &&
wait 5

/kafka/kafka_2.13-3.0.0/bin/kafka-topics.sh --create --topic nodejob_status --bootstrap-server localhost:9092
/kafka/kafka_2.13-3.0.0/bin/kafka-topics.sh --create --topic computing_node_control --bootstrap-server localhost:9092
/kafka/kafka_2.13-3.0.0/bin/



# Wait for kafka process to exit
wait $_pid

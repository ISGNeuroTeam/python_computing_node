FROM openjdk:11
RUN mkdir /kafka
WORKDIR /kafka

RUN curl https://downloads.apache.org/kafka/3.0.0/kafka_2.13-3.0.0.tgz --output kafka.tar.gz
RUN tar -xzf kafka.tar.gz
RUN rm -f kafka.tar.gz
COPY start_kafka.sh /kafka/start_kafka.sh
CMD ["./start_kafka.sh"]
EXPOSE 9092
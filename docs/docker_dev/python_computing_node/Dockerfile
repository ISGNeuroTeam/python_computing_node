FROM python:3.9.7
ENV PYTHONUNBUFFERED=1

ENV COMPUTING_NODE_CONF=/python_computing_node/docs/docker_dev/python_computing_node/computing_node.conf
ENV PYTHONPATH=/python_computing_node/python_computing_node
RUN mkdir /python_computing_node
RUN mkdir /execution_environment

RUN mkdir -p /storages/shared_storage
RUN mkdir -p  = /storages/local_storage
RUN mkdir -p  = /storages/inter_proc_storage

WORKDIR /python_computing_node
COPY requirements.txt /python_computing_node/
RUN pip install --no-cache-dir  -r requirements.txt

RUN pip install --no-cache-dir  -r requirements.txt

COPY . .
ENTRYPOINT ["/python_computing_node/docs/docker_dev/python_computing_node/entrypoint.sh"]
CMD ["/python_computing_node/docs/docker_dev/python_computing_node/start.sh"]

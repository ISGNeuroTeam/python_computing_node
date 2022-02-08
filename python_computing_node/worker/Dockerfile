FROM python:3.9.7
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/worker

RUN mkdir -p /worker/worker
RUN mkdir -p /worker/storages
RUN mkdir -p /worker/execution_environment

WORKDIR /worker/worker
COPY requirements.txt /worker/worker/
RUN pip install --no-cache-dir  -r requirements.txt
COPY . .
CMD ["python", '-m', 'worker', '8090']

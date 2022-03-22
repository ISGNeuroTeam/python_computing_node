#!/bin/bash

cd `dirname "${BASH_SOURCE[0]}"`

echo 'Trying activate ./venv virtual environment'
source  ./venv/bin/activate

if [ $? -eq 0 ]; then
    echo Virtual environment activated
else
    echo 'Trying activate ../venv virtual environment'
    source  ../venv/bin/activate
fi


mkdir -p ./logs
mkdir -p ./run

echo 'Running python computing node server...'
python ./python_computing_node/main.py & echo $! > ./run/server.pid

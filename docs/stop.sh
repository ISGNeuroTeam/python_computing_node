#!/bin/bash

cd `dirname "${BASH_SOURCE[0]}"`

PID_FILE=./run/server.pid
if [ -f "$PID_FILE" ]; then
    echo "Stopping python computing node server"
    kill -15 `cat $PID_FILE`
    rm $PID_FILE
fi

for workerpid in ./run/worker*.pid
do
	echo "Stopping worker $workerpid"
	kill -15 `cat $workerpid`
done

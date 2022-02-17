#.SILENT:
SHELL = /bin/bash

.PHONY: clean clean_build clean_venv.tar.gz clean_pack clean_kafka clean_unit test docker_test clean_docker_test

all:
	echo -e "Sections:\n\
 build - build project into build directory, with configuration file and environment\n\
 clean - clean all addition file, build directory and output archive file\n\
 test - run all tests\n\
 pack - make output archive, file name format \"python_computing_node_vX.Y.Z_BRANCHNAME.tar.gz\"\n\
 dev - deploy for developing \n\
"



test: docker_test clean_docker_test

run:
	mkdir run

docker_test: run
	@echo "Testing..."
	CURRENT_UID=$(id -u):$(id -g) docker-compose -f docker-compose-dev.yml up -d --build
	sleep 15
	CURRENT_UID=$(id -u):$(id -g) docker-compose -f docker-compose-dev.yml exec  python_computing_node  python -m unittest discover -s tests

clean_docker_test:
	@echo "Clean tests"
	docker-compose -f docker-compose-dev.yml stop
	if [[ $$(docker ps -aq -f name=python_computing_node) ]]; then docker rm $$(docker ps -aq -f name=python_computing_node);  fi;
	rm -rf ./run

clean: clean_docker_test


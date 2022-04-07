#.SILENT:
SHELL = /bin/bash

.PHONY: clean clean_build clean_venv.tar.gz clean_pack clean_kafka clean_unit test docker_test clean_docker_test clean_test_computing_node_env

all:
	echo -e "Sections:\n\
 build - build project into build directory, with configuration file and environment\n\
 clean - clean all addition file, build directory and output archive file\n\
 test - run all tests\n\
 pack - make output archive, file name format \"python_computing_node_vX.Y.Z_BRANCHNAME.tar.gz\"\n\
 dev - deploy for developing \n\
"

GENERATE_VERSION = $(shell cat setup.py | grep __version__ | head -n 1 | sed -re 's/[^"]+//' | sed -re 's/"//g' )
GENERATE_BRANCH = $(shell git name-rev $$(git rev-parse HEAD) | cut -d\  -f2 | sed -re 's/^(remotes\/)?origin\///' | tr '/' '_')
SET_VERSION = $(eval VERSION=$(GENERATE_VERSION))
SET_BRANCH = $(eval BRANCH=$(GENERATE_BRANCH))

define clean_docker_containers
	@echo "Stopping and removing docker containers"
	docker-compose -f docker-compose-dev.yml stop
	if [[ $$(docker ps -aq -f name=python_computing_node) ]]; then docker rm $$(docker ps -aq -f name=python_computing_node);  fi;
endef

pack: make_build
	$(SET_VERSION)
	$(SET_BRANCH)
	echo Create archive \"python_computing_node-$(VERSION)-$(BRANCH).tar.gz\"
	cd make_build; tar czf ../python_computing_node-$(VERSION)-$(BRANCH).tar.gz python_computing_node

clean_pack:
	rm -f python_computing_node*.tar.gz

make_build: venv.tar.gz
	echo make_build
	mkdir -p make_build/python_computing_node
	cp -R ./python_computing_node make_build/python_computing_node
	mkdir ./make_build/python_computing_node/logs
	mkdir ./make_build/python_computing_node/run
	mkdir ./make_build/python_computing_node/execution_environment
	mv ./make_build/python_computing_node/python_computing_node/computing_node.conf.example ./make_build/python_computing_node/python_computing_node/computing_node.conf
	cp ./docs/start.sh ./make_build/python_computing_node/start.sh
	cp ./docs/stop.sh ./make_build/python_computing_node/stop.sh
	mkdir make_build/python_computing_node/venv
	tar -xzf ./venv.tar.gz -C make_build/python_computing_node/venv

clean_build:
	rm -rf make_build

venv.tar.gz: venv
	conda pack -p ./venv -o ./venv.tar.gz

computing_node.conf:
	cp ./python_computing_node/computing_node.conf.example ./python_computing_node/computing_node.conf

dev: venv computing_node.conf python_computing_node/execution_environment/test_execution_environment/venv

python_computing_node/execution_environment/test_execution_environment/venv:
	conda create --copy -p ./python_computing_node/execution_environment/test_execution_environment/venv -y
	conda install -p ./python_computing_node/execution_environment/test_execution_environment/venv python==3.9.7 -y;
	./python_computing_node/execution_environment/test_execution_environment/venv/bin/pip install --no-input  -r ./python_computing_node/execution_environment/test_execution_environment/requirements.txt

clean_test_computing_node_env:
	rm -rf ./python_computing_node/execution_environment/test_execution_environment/venv

venv:
	conda create --copy -p ./venv -y
	conda install -p ./venv python==3.9.7 -y;
	./venv/bin/pip install --no-input  -r requirements.txt

clean_venv:
	rm -rf venv
	rm -f ./venv.tar.gz

test: docker_test

run:
	mkdir -p run

logs:
	mkdir -p logs

docker_test: python_computing_node/execution_environment/test_execution_environment/venv run logs
	$(call clean_docker_containers)
	@echo "Testing..."
	CURRENT_UID=$$(id -u):$$(id -g) docker-compose -f docker-compose-dev.yml up -d --build
	sleep 15
	CURRENT_UID=$$(id -u):$$(id -g) docker-compose -f docker-compose-dev.yml exec -T python_computing_node python -m unittest discover -s tests
	$(call clean_docker_containers)

clean_docker_test:
	$(call clean_docker_containers)
	rm -rf ./run
	rm -rf ./logs

clean: clean_docker_test clean_build clean_venv clean_pack clean_test_computing_node_env


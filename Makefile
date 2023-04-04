#.SILENT:
SHELL = /bin/bash

.PHONY: clean clean_build clean_venv.tar.gz clean_pack clean_kafka clean_unit test docker_test clean_docker_test clean_test_computing_node_env install_conda install_conda_pack

all:
	echo -e "Sections:\n\
 build - build project into build directory, with configuration file and environment\n\
 clean - clean all addition file, build directory and output archive file\n\
 test - run all tests\n\
 pack - make output archive, file name format \"python_computing_node_vX.Y.Z_BRANCHNAME.tar.gz\"\n\
 dev - deploy for developing \n\
Addition section:\n\
 venv\n\
 install_conda - install miniconda in local directory \n\
 install_conda_pack - install conda pack in local directory\n\
"

VERSION := $(shell cat setup.py | grep __version__ | head -n 1 | sed -re "s/[^\"']+//" | sed -re "s/[\"',]//g")
BRANCH := $(shell git name-rev $$(git rev-parse HEAD) | cut -d\  -f2 | sed -re 's/^(remotes\/)?origin\///' | tr '/' '_')

CONDA = conda/miniconda/bin/conda
ENV_PYTHON = venv/bin/python3.9


conda/miniconda.sh:
	echo Download Miniconda
	mkdir -p conda
	wget https://repo.anaconda.com/miniconda/Miniconda3-py39_4.12.0-Linux-x86_64.sh -O conda/miniconda.sh; \

conda/miniconda: conda/miniconda.sh
	bash conda/miniconda.sh -b -p conda/miniconda; \

install_conda: conda/miniconda

conda/miniconda/bin/conda-pack: conda/miniconda
	conda/miniconda/bin/conda install conda-pack -c conda-forge  -y

install_conda_pack: conda/miniconda/bin/conda-pack

clean_conda:
	rm -rf ./conda

define clean_docker_containers
	@echo "Stopping and removing docker containers"
	python_computing_node_containers=$$(docker ps -aq -f name=python_computing_node);\
	if [[ $$python_computing_node_containers ]]; then\
		docker stop $$python_computing_node_containers;\
		docker rm $$python_computing_node_containers;\
	fi;
	rm -rf ./run
	rm -rf ./logs
endef

pack: make_build
	echo Create archive \"python_computing_node-$(VERSION)-$(BRANCH).tar.gz\"
	cd make_build; tar czf ../python_computing_node-$(VERSION)-$(BRANCH).tar.gz python_computing_node

clean_pack:
	rm -f python_computing_node*.tar.gz

make_build: venv.tar.gz
	echo make_build
	mkdir -p make_build/python_computing_node
	cp -R ./python_computing_node make_build/python_computing_node
	cp setup.py make_build/python_computing_node/
	cp *.md make_build/python_computing_node/
	mkdir ./make_build/python_computing_node/logs
	mkdir ./make_build/python_computing_node/run
	mkdir ./make_build/python_computing_node/execution_environment
	cp ./docs/start.sh ./make_build/python_computing_node/start.sh
	cp ./docs/stop.sh ./make_build/python_computing_node/stop.sh
	mkdir make_build/python_computing_node/venv
	tar -xzf ./venv.tar.gz -C make_build/python_computing_node/venv

clean_build:
	rm -rf make_build

venv.tar.gz: venv conda/miniconda/bin/conda-pack
	$(CONDA) pack -p ./venv -o ./venv.tar.gz

computing_node.conf:
	cp ./python_computing_node/computing_node.conf.example ./python_computing_node/computing_node.conf

dev: venv computing_node.conf python_computing_node/execution_environment/test_execution_environment/venv

python_computing_node/execution_environment/test_execution_environment/venv: conda/miniconda
	$(CONDA) create --copy -p ./python_computing_node/execution_environment/test_execution_environment/venv -y
	$(CONDA) install -p ./python_computing_node/execution_environment/test_execution_environment/venv python==3.9.7 -y;
	./python_computing_node/execution_environment/test_execution_environment/venv/bin/python3 ./python_computing_node/execution_environment/test_execution_environment/venv/bin/pip3 install --no-input  -r ./python_computing_node/execution_environment/test_execution_environment/requirements.txt

clean_test_computing_node_env:
	rm -rf ./python_computing_node/execution_environment/test_execution_environment/venv

venv: conda/miniconda
	$(CONDA) create --copy -p ./venv -y
	$(CONDA) install -p ./venv python==3.9.7 -y;
	$(ENV_PYTHON) -m pip  install --no-input  -r requirements.txt

clean_venv:
	rm -rf venv
	rm -f ./venv.tar.gz

test: docker_test


docker_test: python_computing_node/execution_environment/test_execution_environment/venv
	-$(call clean_docker_containers)
	mkdir -p run
	mkdir -p logs
	@echo "Testing..."
	CURRENT_UID=$$(id -u):$$(id -g) docker-compose -f docker-compose-test.yml up -d --build
	sleep 15
	CURRENT_UID=$$(id -u):$$(id -g) docker-compose -f docker-compose-test.yml exec -T python_computing_node python -m unittest discover -s tests
	-$(call clean_docker_containers)

clean_docker_test:
	$(call clean_docker_containers)

clean: clean_docker_test clean_build clean_venv clean_pack clean_test_computing_node_env clean_conda


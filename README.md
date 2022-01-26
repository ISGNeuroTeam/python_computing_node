# Python computing node

Python computing node for otl_interpreter

## Getting Started

### Deploy on host machine
####  Prerequisites
You need:
* python 3.9.7

#### Deploy
1. Install virtual environment from requirements.txt:
```bash
python3 -m venv ./venv
source ./venv/bin/activate
pip install -r ./requirements.txt
```
2. Configure rest.conf:
```bash
cp ./python_computing_node/rest.conf.example ./python_computing_node/rest.conf
```
### Deploy with conda
####  Prerequisites
1. [Miniconda](https://docs.conda.io/en/latest/miniconda.html)
2. [Conda-Pack](https://conda.github.io/conda-pack)
#### Deploy
1. Create virtual environment for project:
```bash
make dev
```
2. To activate virtual environment:
```bash
source ./venv/bin/activate
```
3. Launch services:
```bash
./start.sh
```

### Deploy with docker
#### Prerequisites
1. [Docker](https://docs.docker.com/engine/install/).
[Manage Docker as a non-root user](https://docs.docker.com/engine/install/linux-postinstall/)
2. [Docker compose](https://docs.docker.com/compose/install/)
#### Deploy
```bash
docker-compose -f "docker-compose-dev.yml" up -d --build
```

## Deployment
1. Unpack tar archive to destination directory
2. Run `start.sh`

## Built With
- Conda
- python 3.9.7  
    And python packages:  
- 


## Versioning

We use [SemVer](http://semver.org/) for versioning. For the versions available, see the [tags on this repository](https://github.com/your/project/tags).

## License

See the [LICENSE.md](LICENSE.md) file for details
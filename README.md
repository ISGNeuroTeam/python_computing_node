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
2. Configure computing_node.conf:
```bash
cp ./python_computing_node/rest.conf.example ./python_computing_node/rest.conf
```
3. Launch python computing node server:
```bash
python ./python_computing_node/main.py
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
2. Configure computing_node.conf.

3. To activate virtual environment:
```bash
conda activate ./venv
```


4. Launch python computing node server:
```bash
python ./python_computing_node/main.py
```

## Deployment
1. Unpack tar archive to destination directory
2. Run `start.sh`

## Built With
- Conda
- python 3.9.7  
    And python packages:  
  - aiokafka==0.7.2
  - kafka-python==2.0.2
  - aiohttp==3.8.1
  - gunicorn==20.1.0
  - bottle==0.12.19


## Versioning

We use [SemVer](http://semver.org/) for versioning. For the versions available, see the [tags on this repository](https://github.com/your/project/tags).

## License

See the [LICENSE.md](LICENSE.md) file for details
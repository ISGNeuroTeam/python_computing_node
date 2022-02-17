import os
import copy
import configparser
import uuid
from pathlib import Path


defaults = {
    'storages': {
        'interproc_storage': '../inter_proc_storage',
    },
    'execution_environment': {
        'package': 'test_execution_environment',
        'execution_environment_dir': '../execution_environment',
        'commands_dir': '../execution_environment/test_execution_environment/commands'
    },
    'worker': {
        'spawn_method': 'ulimit',
        'memory_limit': 250,
        'proc_num_limit': 4,
        'workers': 4,
        'start_port': 8091,
    },
    'computing_node':  {
            'host_id': os.popen("hostid").read().strip(),
            'type': 'test',
            'health_check_interval': 3
        },
    'kafka_producer': {
        'bootstrap_servers': 'localhost',
        'acks': 'all',
    },

    'server': {
        'port': 8090,
        'socket_type': 'unix',
        'run_dir': '../run'
    },

    'kafka_consumer': {
        'bootstrap_servers': 'localhost:9092',
        'group_id': 'complex_rest',
    },
    'logging': {
        'active': 'True',
        'log_dir': '../logs',
        'level': 'INFO',
        'rotate': 'True',
        'rotation_size': 10,
        'keep_files': 10,
    }
}


def merge_ini_config_with_defaults(config, default_config):
    """
    Merge ini config with default config
    :param config: config dictionary
    :param default_config: dict with default config
    :return:
    Merged dictionary config
    """
    result_config = merge_dicts(config, default_config)
    return result_config


def merge_dicts(first_dict, second_dict):
    """
    Merges two dicts. Returns new dictionary. Fist dict in priority
    """
    result_dict = copy.deepcopy(second_dict)
    for key, value in first_dict.items():
        if isinstance(value, dict):
            # get node or create one
            node = result_dict.setdefault(key, {})
            result_dict[key] = merge_dicts(value, node)
        else:
            result_dict[key] = value

    return result_dict


def make_abs_paths(config_dict, dict_keys_list, base_dir):
    """
    Replace relative paths in config to absolute paths and create directories if they doesn't exist
    :param config_dict: dict config
    :param dict_keys_list: list of keys in dictionary where relative path located
    Example if dict keys list is ['key1', 'key2' ] then config_dict['key1']['key2'] will become absolute path
    if only one key in list then absolute path will be generated for all kets in config_dict['key1'] dictionary
    :param base_dir: base directory to calculate relative paths
    :return:
    """
    for dict_keys in dict_keys_list:
        section = dict_keys[0]

        if len(dict_keys) == 1:
            options = config_dict[section].keys()
        else:
            options = [dict_keys[1], ]

        for option in options:
            # replace relative paths to absolute
            p = Path(config_dict[section][option])
            if not p.is_absolute():
                dir_path = (base_dir / p).resolve()
            else:
                dir_path = p
            # create directory
            if not dir_path.exists():
                dir_path.mkdir(exist_ok=True)

            config_dict[section][option] = str(dir_path)


def auto_generate_uuids_for_first_launch(config_path, dict_keys_list):
    """
    :config_path: full path to ini config
    :param dict_keys_list: list of keys in dictionary where find uuid
    """
    config = configparser.RawConfigParser()

    config.read(config_path)

    for section, option in dict_keys_list:
        if section not in config:
            config.add_section(section)
        if not (option in config[section] and config[section][option]):
            config[section][option] = uuid.uuid4().hex

    with open(config_path, 'w') as f:
        config.write(f)


def get_ini_config():
    """
    Read config passed in REST_CONF environment variable
    or rest.conf in base directory
    :return:
    config dictionary merged with defaults
    """

    node_source_dir = Path(__file__).resolve().parent
    # try to read path to config from environment
    conf_path_env = os.environ.get('COMPUTING_NODE_CONF', None)

    if conf_path_env is None:
        conf_path = node_source_dir / 'computing_node.conf'
    else:
        conf_path = Path(conf_path_env).resolve()

    auto_generate_uuids_for_first_launch(
        str(conf_path),
        [
            ['computing_node', 'uuid']
        ]
    )

    config = configparser.ConfigParser()

    config.read(conf_path)

    # convert to dictionary
    config = {s: dict(config.items(s)) for s in config.sections()}
    merged_with_defaults = merge_ini_config_with_defaults(
        config, defaults
    )
    make_abs_paths(
        merged_with_defaults,
        [
            ['storages', ],
            ['execution_environment', 'execution_environment_dir'],
            ['execution_environment', 'commands_dir'],
            ['server', 'run_dir'],
            ['logging', 'log_dir']
        ],
        node_source_dir
    )
    return merged_with_defaults


ini_config = get_ini_config()





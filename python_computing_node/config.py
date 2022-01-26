import os
import copy
import configparser
from pathlib import Path


defaults = {
    'mounts': {
        'shared_storage': '../shared_storage',
        'local_storage': '../local_storage',
        'inter_proc_storage': '../inter_proc_storage',
    },
    'worker': {
        'spawn_method': 'ulimit',
        'memory_limit': 250,
        'proc_num_limit': 4,
        'workers': 4,
        'start_port': 8091,
    },
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
    :param base_dir: base directory to calculate relative paths
    :return:
    """
    for section, option in dict_keys_list:
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
            ['mounts', 'shared_storage'],
            ['mounts', 'local_storage'],
        ],
        node_source_dir
    )
    return merged_with_defaults


ini_config = get_ini_config()





import time
import logging
import threading

from pathlib import Path

from .random_dataframe import random_data_frame


log = logging.getLogger('test_execution_environment')

syntax = {
        'normal_command': {
            "rules":
            [
                {
                    "name": "stages",
                    "type": "kwarg",
                    "key": "stages",
                    "required": True,
                },
                {
                    "name": "stage_time",
                    "type": "kwarg",
                    "key": "stage_time",
                    "required": True,
                },
            ]},
        'error_command': {
            "rules":
            [
                {
                    "name": "stages",
                    "type": "kwarg",
                    "key": "stages",
                    "required": False,
                },
                {
                    "name": "stage_time",
                    "type": "kwarg",
                    "key": "stage_time",
                    "required": False,
                },
                {
                    "name": "error_stage",
                    "type": "kwarg",
                    "key": "error_stage",
                    "required": False,
                },
            ]},
            'subsearch_command': {
                'rules':
                    [
                        {
                            'name': 'subsearch',
                            "type": "subsearch",
                            "required": True,
                        },
                    ]
            },
            'command_with_threads': {
                "rules":
                [
                    {
                        "name": "count",
                        "type": "kwarg",
                        "key": "count",
                        "required": True,
                    },
                ]
            }
}


def do_sys_command(command_dict,  command_progress_message):
    command_progress_message(f'Start system_command {command_dict["name"]} command')
    command_progress_message(f'Finish system_command {command_dict["name"]} command')


def do_normal_command(command_dict,  command_progress_message):
    log.info('Starting normal command')
    command_progress_message('Start normal command')
    stages = int(command_dict['arguments']['stages'][0]['value'])
    stage_time = int(command_dict['arguments']['stage_time'][0]['value'])

    for i in range(1, stages+1):
        time.sleep(stage_time)
        command_progress_message(f'Stage  {i} completed', stage=i, total_stages=stages)
    command_progress_message('Normal command finished')
    log.info('Normal command finished')


def do_error_command(command_dict, command_progress_message):
    log.info('Error command starting')
    stage_time = 1
    error_stage = 1

    if 'stages' in command_dict['arguments']:
        stages = int(command_dict['arguments']['stages'][0]['value'])

        if 'stage_time' in command_dict['arguments']:
            stage_time = int(command_dict['arguments']['stage_time'][0]['value'])

        if 'error_stage' in command_dict['arguments']:
            error_stage = int(command_dict['arguments']['error_stage'][0]['value'])

    else:
        stages = None

    if stages:
        for i in range(1, stages+1):
            if i == error_stage:
                command_progress_message(f'Test error occured', total_stages=stages, stage=i)
                raise Exception('Test error')

            time.sleep(stage_time)
            command_progress_message(f'Stage  {i} completed', stage=1, total_stages=stages)
    else:
        raise Exception('Test exception')


def do_subsearch_command(command_dict, command_progress_message, execute):
    log.info('Subsearch command starting')
    command_progress_message('Making subsearch')
    execute(command_dict['arguments']['subsearch'][0]['value'])


def sys_write_result(command_dict, command_progress_message, storages_dict):
    log.info('Sys write command starting')
    command_progress_message(f'Start system_command {command_dict["name"]} command')
    storage_type = command_dict['arguments']['storage_type'][0]['value']
    result_path = command_dict['arguments']['path'][0]['value']

    write_random_df(Path(storages_dict[storage_type]) / result_path)
    command_progress_message(f'Finish system_command {command_dict["name"]} command')


def target_for_thread():
    for _ in range(10):
        time.sleep(5)

def do_command_with_threads(command_dict, command_progress_message):
    log.info('command with threads starting')
    command_progress_message(f'Creating threads')
    number_of_threads = command_dict['arguments']['count'][0]['value']
    for _ in range(number_of_threads):
        new_thread = threading.Thread(target=target_for_thread)
        new_thread.start()
    command_progress_message('Threads are created')
    new_thread.join()
    command_progress_message('All threads are completed')


def write_random_df(dir_path):
    df, schema = random_data_frame()
    result_path = dir_path / 'jsonl'
    result_path.mkdir(parents=True, exist_ok=True)
    # write schema
    with open(result_path / '_SCHEMA', 'w') as file:
        file.write(schema)

    # write data
    df.to_json(result_path / 'data', lines=True, orient="records")

import time


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
            }
}


def do_normal_command(command_dict,  command_progress_message):
    command_progress_message('Start normal command')
    stages = int(command_dict['arguments']['stages'][0]['value'])
    stage_time = int(command_dict['arguments']['stage_time'][0]['value'])

    for i in range(1, stages+1):
        time.sleep(stage_time)
        command_progress_message(f'Stage  {i} completed', stage=i, total_stages=stages)
    command_progress_message('Normal command finished')


def do_error_command(command_dict, command_progress_message):
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


def do_subsearch_command(command_dict, command_progress_message, execute):
    command_progress_message('Making subsearch')
    execute(command_dict['arguments']['subsearch'][0]['value'])
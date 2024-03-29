from functools import partial

from .test_commands import (
    syntax, do_error_command, do_normal_command, do_subsearch_command, do_sys_command, sys_write_result
)


class CommandExecutor:
    def __init__(self, storages: dict, commands_dir, progress_message):
        self.progress_message = progress_message
        self.storages = storages
        self.commands_dir = commands_dir
        self.depth=0

    @staticmethod
    def get_command_syntax():
        return syntax

    def execute(self, dict_commands, platform_envs=None):
        if platform_envs is None:
            platform_envs={'user_guid': 'test_user_guid'}

        for command_index, command in enumerate(dict_commands):
            command_progress_message = partial(
                self.progress_message,
                command_name=command['name'],
                command_index_in_pipeline=command_index+1,
                total_commands_in_pipeline=len(dict_commands),
                depth=self.depth
            )
            if command['name'] == 'normal_command':
                do_normal_command(command, command_progress_message)
            elif command['name'] == 'error_command':
                do_error_command(command, command_progress_message)
            elif command['name'] == 'subsearch_command':
                self.depth += 1
                do_subsearch_command(command, command_progress_message, self.execute)
                self.depth -= 1
            elif command['name'] == 'sys_write_result':
                sys_write_result(command, command_progress_message, self.storages)
            elif command['name'].startswith('sys_'):
                do_sys_command(command, command_progress_message)
            else:
                raise Exception(f'Unsupported command {command["name"] }')

        return {}

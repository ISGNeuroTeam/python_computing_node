class CommandExecutor:
    def __init__(self, storages: dict, commands_dir, progress_message):
        self.progress_message = progress_message
        pass

    def get_commands_syntax(self):
        return {'test_syntax': 'syntax'}

    def execute_commands(self, dict_commands):
        return []

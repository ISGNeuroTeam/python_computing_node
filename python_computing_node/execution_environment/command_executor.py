from .sys_commands import SysWriteResultCommand, SysWriteInterProcCommand, SysReadInterProcCommand


class GetArg:
    def __init__(self, command_executor, arguments):
        """
        arguments - list of arguments
        command_executor - instance of command_executor for calculate subsearches
        """
        self.arguments = arguments
        self.command_executor = command_executor

    def __call__(self, name, index=0):
        # if type subsearch
            # get commands
            # return self.command_executor(commands)
        # else
            # return argument
        pass


class CommandExecutor:
    def __init__(self, shared_storage, local_storage, inter_proc_storage, commands_directory):
        """
        shared_storage - mount point for shared post processing storage
        local_storage - mount point for local post processing storage
        inter_proc_storage - mount point for inter_proc_storage
        commands_directory - users commands directory which inherit from BaseCommand
        """

        self.shared_storage = shared_storage
        self.local_storage = local_storage
        self.inter_proc_storage = inter_proc_storage

        self.commands_directory = commands_directory

        # dictionary with command classes
        self.command_classes = {}

        self._import_sys_commands()
        self._import_user_commands()

    def _import_sys_commands(self):
        SysWriteResultCommand.shared_storage = self.shared_storage
        SysWriteResultCommand.local_storage = self.local_storage
        SysWriteResultCommand.inter_proc_storage = self.inter_proc_storage

        SysReadInterProcCommand.inter_proc_storage = self.inter_proc_storage
        SysWriteInterProcCommand.inter_proc_storage = self.inter_proc_storage

        self.command_classes['sys_read_interproc'] = SysReadInterProcCommand
        self.command_classes['sys_write_interproc'] = SysWriteInterProcCommand

        self.command_classes['sys_write_result'] = SysWriteResultCommand

    def _import_user_commands(self):
        # using self.commands_directory and importlib module
        pass

    def execute(self, dict_commands: dict):
        df = None
        for dict_command in dict_commands:
            arguments = dict_command['arguments']
            command_name = dict_command['name']
            command_cls = self.command_classes[command_name]
            get_arg = GetArg(arguments, self)
            # А вот тут инициализируем уже реальную пользовательскую команду
            command = command_cls(get_arg)
            df = command.transform_df(df)
        return df

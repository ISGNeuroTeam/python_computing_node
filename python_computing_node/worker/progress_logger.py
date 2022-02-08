class ProgressLog:
    def __init__(self, server_client):
        self.server_client = server_client
        pass

    def enter_subsearch(self, command, arg_name=None, index=0):
        """
        :param command: command name
        :param arg_name: argument rule name
        :param index: argument index in rule
        """
        print('enter_subsearch')

    def exit_subsearch(self):
        print('exit_subsearch')

    def log(self, message, command=None, index=None):
        """
        Send status message to dispatcher
        :param message:
        :param command: command name
        :param
        """
        print(message)
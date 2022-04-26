from .server_client import ServerClient


class ProgressNotifier:
    def __init__(self, server_client: ServerClient):
        self._server_client = server_client
        # current job uuid
        self._job_uuid = None

    def set_cur_job_uuid(self, uuid):
        self._job_uuid = uuid

    def message(
            self, message,
            command_name, command_index_in_pipeline,
            total_commands_in_pipeline, stage=None, total_stages=None, depth=0
    ):

        message_for_sending = self._format_message(
            message,
            command_name, command_index_in_pipeline,
            total_commands_in_pipeline, stage, total_stages, depth
        )
        self._server_client.send_job_status(self._job_uuid, 'RUNNING', message_for_sending)

    @staticmethod
    def _format_message(
            message,
            command_name, command_index_in_pipeline,
            total_commands_in_pipeline, stage=None, total_stages=None, depth=0

    ):
        command_message = '\t'*depth + f'{command_index_in_pipeline} out of {total_commands_in_pipeline} command.' \
                                      f' Command {command_name}.'
        if stage is None:
            stage_message = ''
        else:
            stage_message = f'Stage {stage}/{total_stages}'
        result_message = command_message + ' ' + stage_message + ' ' + message
        return result_message

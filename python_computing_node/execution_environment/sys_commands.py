from .base_command import BaseCommand


class SysWriteInterProcCommand(BaseCommand):
    # class attribute must be defined after class import
    inter_proc_storage = None

    def transform(self, df):
        assert self.inter_proc_storage is not None
        pass


class SysReadInterProcCommand(BaseCommand):
    # class attribute must be defined after class import
    inter_proc_storage = None

    def transform(self, df):
        assert self.inter_proc_storage is not None
        pass


class SysWriteResultCommand:
    # class attributes must be defined after class import
    local_storage = None
    shared_storage = None
    inter_proc_storage = None

    def transform(self, df):
        assert self.local_storage is not None
        assert self.shared_storage is not None
        assert self.inter_proc_storage is not None
        pass
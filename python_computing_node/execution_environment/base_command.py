class BaseCommand:
    def __init__(self, get_arg):
        """
        get_arg - callable object for retrieving arguments
        arg = get_arg(name=<arg rule name from command syntax>, index=0)
        """
        self.get_arg = get_arg

    def transform(self, df):
        raise NotImplementedError

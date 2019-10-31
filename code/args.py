import argparse
from . import Logs

class Args:
    __shared_state = {'init':False}

    def __init__(self):
        self.__dict__ = self.__shared_state
        if not self.init:
            self.init = True


            parser = argparse.ArgumentParser(description='Process Images')
            parser.add_argument('--rowid', metavar='N', type=int,
                               help='row id to start processing at, defaults to all rows')
            parser.add_argument('--threshold', metavar='N', type=int, default=5,
                                help='All values must be <= to this value to trigger a match (Defaults to 5)')

            self.args = parser.parse_args()
            self.logger = Logs()
            self.logger.info(self.args)


    def __getitem__(self, key):
        return self.args.__getattribute__(key)


    def __getattr__(self, name):
        if name in self.__dict__:
            return self.__dict__[name]
        return self.args.__getattribute__(name)

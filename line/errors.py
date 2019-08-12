
import sys

# TODO MID error management

class LineParseError(Exception):

    def __init__(self, message):
        self.message = message
        super().__init__()

    def __str__(self):
        return self.message


class LineProcessError(Exception):

    def __init__(self, message):
        self.message = message
        super().__init__()

    def __str__(self):
        return self.message


def warn(message):
    print('WARNING: ', message, file=sys.stderr)

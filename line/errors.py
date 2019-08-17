
import sys
import os.path
import traceback


class LineParseError(Exception):

    def __init__(self, message, context=''):
        self.message = message
        self.context = context
        super().__init__()

    def __str__(self):
        return self.message


class LineProcessError(Exception):

    def __init__(self, message, context=''):
        self.message = message
        self.context = context
        super().__init__()

    def __str__(self):
        return self.message


def warn(message):
    print('WARNING:', message, file=sys.stderr)


def print_sys_error(e):
    """ General formatting of system error
    """
    exc_type = type(e)
    tb_frame = traceback.extract_tb(e.__traceback__)[-1]

    file_name = os.path.basename(tb_frame.filename)
    func_name = tb_frame.name
    line_no = tb_frame.lineno

    print('[%s:%d %s()] %s: %s' % (file_name, line_no, func_name, exc_type.__name__, e), file=sys.stderr)

def print_as_warning(e):
    warn(sys.exc_info()[1])

def print_line_error(e):
    if isinstance(e, LineParseError):
        print('Parsing Error: %s' % e, file=sys.stderr)
    elif isinstance(e, LineProcessError):
        print('Runtime Error: %s' % e, file=sys.stderr)

def print_error(e:Exception):

    if isinstance(e, (LineParseError, LineProcessError)):
        print_line_error(e)

    else:
        print_sys_error(e)

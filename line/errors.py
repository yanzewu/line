
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


#def format_error(e):
#    return sys.exc_info()[1]

def format_sys_error(e):
    """ General formatting of system error
    """
    exc_type = type(e)
    tb_frame = traceback.extract_tb(e.__traceback__)[-1]

    file_name = os.path.basename(tb_frame.filename)
    func_name = tb_frame.name
    line_no = tb_frame.lineno

    return '[%s:%d %s()] %s: %s' % (file_name, line_no, func_name, exc_type.__name__, e)

def format_line_error(e):
    if isinstance(e, LineParseError):
        return 'Parsing Error: %s' % e
    elif isinstance(e, LineProcessError):
        return 'Runtime Error: %s' % e

def format_error(e):

    if isinstance(e, (LineParseError, LineProcessError)):
        return format_line_error(e)
    elif isinstance(e, Warning):
        return str(e)
    else:
        return format_sys_error(e)

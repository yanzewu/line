
import logging
import warnings
import sys
from prompt_toolkit import print_formatted_text as _print_formatted_text
from prompt_toolkit.formatted_text import FormattedText

from .. import session
from ..vm import LineDebugInfo
from ..errors import format_error
        
showwarning_default = warnings.showwarning

def print_formatted_text_default(text, file=sys.stdout):
    if isinstance(text, FormattedText):
        print(str(text))
    else:
        print(text)

print_formatted_text = _print_formatted_text

def set_jupyter():
    # Redirect error to normal print: print_formatted_text does not work here.
    global print_formatted_text, print_formatted_text_default

    print_formatted_text = print_formatted_text_default


def showwarning(message:Warning, category, filename, lineno, file=None, line=None):
    
    if category == UserWarning:
        if session.has_instance():
            ldi, tokens = session.get_vm().pc
            print_error_formatted(
                message, LineDebugInfo(ldi.filename, ldi.lineid, ldi.token_pos[max(-len(tokens)-1, -len(ldi.token_pos))]), None, 
                print_source=not session.is_interactive(),
                print_indicator=session.is_interactive(),   #  TODO use shell_interactive instead.
                extra_indent=6 if session.is_interactive() else 0,
                )
        else:
            print_formatted_text(FormattedText([
                ('magenta', 'Warning: '),
                ('', str(message))
            ]))
    else:
        return showwarning_default(message, category, filename, lineno, file, line)


def init_logger():
    logger = logging.getLogger('line')
    logger.setLevel(logging.WARNING)
    sh = logging.StreamHandler()
    sh.setFormatter(logging.Formatter('[%(filename)s: %(funcName)s()] %(message)s'))
    logger.addHandler(sh)
    

def print_error_string(text:str):
    """ print a string using red
    """
    print_formatted_text(FormattedText(
        [('red', text)]
    ), file=sys.stderr)


def print_error_formatted(error, dbg_info:LineDebugInfo, code_line=None, print_error=True, print_source=False, print_indicator=False, extra_indent=0):
    """ Display formatted error string.
    Args:
        error: will be formatted by errors.format_error()
        dbg_info: LineDebugInfo instance.
        code_line: str/None. If None, will not print the code line.
        print_error: Print the error name.
        print_source: Print row and column position.
        print_indicator: Print a small indicator below the code_line (if given), or above error string (otherwise).
    """
    if isinstance(dbg_info.token_pos, tuple):
        dbg_info = LineDebugInfo(dbg_info.filename, dbg_info.token_pos[0], dbg_info.token_pos[1])

    if code_line is None and print_indicator: # just display the line
        print_formatted_text(FormattedText([
            ('white', ' ' * (extra_indent + dbg_info.token_pos)),
            ('green', '^')]), file=sys.stderr)
    
    error_str = format_error(error)
    if isinstance(error, Warning):
        error_str_f = [('magenta', 'Warning: '), ('', error_str)]
    elif not error_str.startswith('['):
        _colonpos = error_str.find(':')
        error_str_f = [('red', error_str[:_colonpos+1]), ('', error_str[_colonpos+1:])]
    else:
        error_str_f = [('red', 'Error: '), ('', error_str)]

    if not print_error:
        pass
    elif not print_source:
        print_formatted_text(FormattedText(error_str_f), file=sys.stderr)
    else:
        print_formatted_text(FormattedText([
            ('white', '%sline %d, col %d: ' % (
                        ('"%s", ' % dbg_info.filename if dbg_info.filename else ''),
                        dbg_info.lineid + 1,
                        dbg_info.token_pos + 1,)),
        ] + error_str_f), file=sys.stderr)

    if code_line is not None:
        print_formatted_text('    ' + code_line, file=sys.stderr)
        if print_indicator:
            print_formatted_text(FormattedText([
                ('white', ' ' * (dbg_info.token_pos + 4)),
                ('green', '^')]), file=sys.stderr)

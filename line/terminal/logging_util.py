
import logging
import warnings
import sys
from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import FormattedText

from .. import session
from ..vm import LineDebugInfo
from ..errors import format_error
        
showwarning_default = warnings.showwarning

def showwarning(message:Warning, category, filename, lineno, file=None, line=None):
    
    if category == UserWarning:
        if session.has_instance():
            ldi, tokens = session.get_vm().pc
            print_error_formatted(
                message, LineDebugInfo(ldi.filename, ldi.lineid, ldi.token_pos[max(-len(tokens)-1, -len(ldi.token_pos))]), 
                    session.is_interactive(), extra_indent=6 if session.is_interactive() else 0)
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


def print_error_formatted(error, dbg_info:LineDebugInfo, is_interactive:bool, code_line=None, extra_indent=0):
    """ Display formatted error string.
    If `is_interactive': Will show column position instead of display column index;
    """
    if isinstance(dbg_info.token_pos, tuple):
        dbg_info = LineDebugInfo(dbg_info.filename, dbg_info.token_pos[0], dbg_info.token_pos[1])

    if is_interactive and not code_line: # just display the line
        display_code = False
        print_formatted_text(FormattedText([
            ('white', ' ' * (extra_indent + dbg_info.token_pos)),
            ('green', '^')]), file=sys.stderr)
    else:
        display_code = True
    
    error_str = format_error(error)
    if isinstance(error, Warning):
        error_str_f = [('magenta', 'Warning: '), ('', error_str)]
    elif not error_str.startswith('['):
        _colonpos = error_str.find(':')
        error_str_f = [('red', error_str[:_colonpos+1]), ('', error_str[_colonpos+1:])]
    else:
        error_str_f = [('red', 'Error: '), ('', error_str)]

    if not display_code:
        print_formatted_text(FormattedText(error_str_f), file=sys.stderr)
    else:
        print_formatted_text(FormattedText([
            ('white', '%sline %d, col %d: ' % (
                        ('"%s", ' % dbg_info.filename if dbg_info.filename and not is_interactive else ''),
                        dbg_info.lineid + 1,
                        dbg_info.token_pos + 1,)),
        ] + error_str_f), file=sys.stderr)

    if display_code and code_line:
        print_formatted_text('    ' + code_line, file=sys.stderr)
        print_formatted_text(FormattedText([
            ('white', ' ' * (dbg_info.token_pos + 4)),
            ('green', '^')]), file=sys.stderr)

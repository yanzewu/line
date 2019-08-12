
import sys
import logging

from . import cmd_handle
from .parse import translate_option_val


if __name__ == '__main__':
    
    help_str = '''
line: Visualizing sequential data smartly.
Available options are:
-e, --eval: Entering evaluation mode, where args will be treated as commands;
-p, --plot: Entering plotting mode, where args will be treated as arguments of command `plot`;
-h, --help: Display this help.
By default, reads script files from args.
Additional options can be shown by `line -e 'show option'`'''

    cmd_handler = cmd_handle.CMDHandler()

    mode = 'script'
    args = []

    for arg in sys.argv[1:]:
        if arg in ('-e', '--eval'):
            mode = 'eval'
        elif arg in ('-p', '--plot'):
            mode = 'plot'
        elif arg in ('-h', '--help'):
            print(help_str)
            exit(0)
        elif arg in ('-d', '--debug'):
            logging.getLogger('line').setLevel(logging.DEBUG)
        elif arg.startswith('--'):
            opt, val = arg[2:].split('=')
            cmd_handler.m_state.options[opt] = translate_option_val(opt, val)
        else:
            args.append(arg)
    
    if len(args) == 0:
        cmd_handler.init_input()
        cmd_handler.input_loop()
    elif mode == 'script':
        for filename in args:
            cmd_handler.proc_file(filename)
    elif mode == 'eval':
        cmd_handler.proc_lines([' '.join(args)])
    elif mode == 'plot':
        cmd_handler.proc_lines(['plot ' + ' '.join(args)])

        
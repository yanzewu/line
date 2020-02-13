
import sys
import logging
import warnings

from . import defaults
from . import cmd_handle
from .process import process_display

def main():

    help_str = '''
line: Visualizing sequential data smartly.
Available options are:
-e, --eval: Entering evaluation mode, where args will be treated as commands;
-p, --plot: Entering plotting mode, where args will be treated as arguments of command `plot`;
-h, --help: Display this help.
By default, reads script files from args.
Additional options can be shown by `line -e 'show option'`'''

    mode = 'script'
    args = []
    kwargs = []

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
            cmd_handle.CMDHandler._debug = True
        elif arg.startswith('--'):
            kwargs.append(arg[2:].split('='))
        else:
            args.append(arg)
    
    defaults.default_options.update(defaults.parse_default_options(kwargs, 
        option_range=defaults.default_options.keys(), raise_error=True))

    if not cmd_handle.CMDHandler._debug:
        warnings.filterwarnings('ignore')

    cmd_handler = cmd_handle.CMDHandler(preload_input=(len(args) == 0) and
        defaults.default_options['delayed-init'])

    if len(args) == 0:
        cmd_handler.read_source()
        cmd_handler.m_state.is_interactive = True
        cmd_handler.input_loop()
    elif mode == 'script':
        cmd_handler.read_source()
        for filename in args:
            cmd_handler.proc_file(filename)
    elif mode == 'eval':
        cmd_handler.read_source()
        cmd_handler.proc_lines([' '.join(args)])
    elif mode == 'plot':
        cmd_handler.m_state.options['display-when-quit'] = True
        cmd_handler.read_source()
        line0 = 'plot ' + ' '.join(args)
        line0 = line0.replace('\\', '/')
        cmd_handler.proc_lines([line0])
        process_display(cmd_handler.m_state)


if __name__ == '__main__':
    
    main()
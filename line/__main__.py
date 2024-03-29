
import sys
import logging
import warnings

from . import defaults
from . import terminal
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
            terminal.CMDHandler._debug = True
        elif arg.startswith('--'):
            kwargs.append(arg[2:].split('='))
        else:
            args.append(arg)
    
    if len(args) == 0:
        if sys.stdin.isatty():
            mode = 'interactive'
        else:
            mode = 'stdin'

    defaults.default_options.update(defaults.parse_default_options(kwargs, 
        option_range=defaults.default_options.keys(), raise_error=True))

    if not terminal.CMDHandler._debug:
        warnings.filterwarnings(action='ignore', category=DeprecationWarning)
    warnings.simplefilter('always', UserWarning)

    cmd_handler = terminal.CMDHandler(preload_input=(mode == 'interactive') and
        defaults.default_options['delayed-init'])
    if len(args) == 0:
        cmd_handler.m_state._vmhost.push_args(['[stdin]'])
    else:
        cmd_handler.m_state._vmhost.push_args(args)

    ret_code = 0
    cmd_handler.read_source()
    logging.getLogger('line').debug('Entering %s mode' % mode)
    if mode == 'interactive':
        cmd_handler.m_state.is_interactive = True
        ret_code = cmd_handler.input_loop()
    elif mode == 'stdin':
        ret_code = cmd_handler.proc_stdin()
    elif mode == 'script':
        ret_code = cmd_handler.proc_file(args[0])
    elif mode == 'eval':
        cmd_handler._filename = '<command>'
        ret_code = cmd_handler.proc_lines([' '.join(args)])
    elif mode == 'plot':
        cmd_handler.m_state.options['display-when-quit'] = True
        line0 = ('plot ' + args[0]).replace('\\', '/')
        ret_code = cmd_handler.proc_lines([line0])


    if ret_code == 0 and cmd_handler.m_state.options['display-when-quit']:
        process_display(cmd_handler.m_state)


if __name__ == '__main__':
    
    main()

import re
import sys
import logging

try:
    import readline
except ImportError:
    import pyreadline.rlmain
    import readline

from . import state
from . import parse
from . import process
from .errors import LineParseError
from . import defaults
from . import plot


logger = logging.getLogger('line')
sh = logging.StreamHandler()
sh.setFormatter(logging.Formatter('[%(filename)s: %(funcName)s()] %(message)s'))
logger.addHandler(sh)


# TODO LOW FEATURE include other file


class CMDHandler:

    PS1 = 'line> '
    PS2 = '> '
    HISTORY_NAME = None
    TOKEN_MATCHER = re.compile(r"(?P<a>([\"\'])(?:\\\2|(?:(?!\2)).)*(\2)?)|(?P<b>[^,:=;#\\\"\'\s]+)|(?P<c>[,:=;#\\])")
    
    # generally there are only 5 global-wise chracters: , : = # \

    RET_EXIT = 1
    RET_CONTINUE = 2
    RET_INTERACTIVE = 3

    _debug = False

    def __init__(self):
        self.m_state = state.GlobalState()
        defaults.init_global_state(self.m_state)

        self.token_buffer = []
        self.completion_buffer = []

    def init_input(self):
        if self.HISTORY_NAME:
            try:
                readline.read_history_file(history_name)
            except IOError:
                pass 
        #readline.parse_and_bind('tab: complete')
        #readline.set_completer(self.complete)
        #readline.set_completer_delims('')

    def proc_file(self, filename):
        with open(filename, 'r') as f:
            self.m_state.is_interactive = False
            self.proc_lines(f.readlines())

    def proc_lines(self, lines):
        plot.initialize(self.m_state)
        for line in lines:
            try:
                ret = self.handle_line(line, self.token_buffer, True)
            except Exception as e:
                if self._debug:
                    raise
                else:
                    print(e)
                    return
            else:
                if ret == 0:
                    self.token_buffer.clear()
                elif ret == self.RET_EXIT:
                    break
                elif ret == self.RET_CONTINUE:
                    continue
            
            if self.m_state.is_interactive:
                self.input_loop()
                self.m_state.is_interactive = False
                # TODO MID FIX handle initialize and finalize and other 
                # interfaces when switching plotting mode
        plot.finalize(self.m_state)

    def proc_input(self, ps=PS1):
        self.m_state.is_interactive = True
        line = input(ps)
        # if 'readline' in sys.modules and self.HISTORY_NAME:
        #     readline.write_history_file(self.HISTORY_NAME)

        try:
            ret = self.handle_line(line, self.token_buffer, True)
        except Exception as e:
            self.token_buffer.clear()
            raise
            # TODO MID FIX error line number and token position
        else:
            if ret == 0:
                self.token_buffer.clear()
                return 0
            elif ret == self.RET_EXIT:
                return 1
            elif ret == self.RET_CONTINUE:
                self.proc_input(self.PS2)

    def input_loop(self):
        plot.initialize(self.m_state)
        ret = 0
        while ret == 0:
            ret = self.proc_input()
        plot.finalize(self.m_state)

    def handle_line(self, line, token_buffer, execute=True):
        """ Preprocessing and execute
        """
        logger.debug('Handle input line: %s' % line)
        token_iter = self.TOKEN_MATCHER.finditer(line)
        
        while True:
            cur_token = next(token_iter, None)
            if cur_token is None:
                break

            if cur_token.group('a'):    # string
                string = cur_token.group('a')
                if string[-1] != string[0]:
                    raise LineParseError("Quote not match")
                token_buffer.append(string[1:-1])

            elif cur_token.group('b'):  # variable or others
                token_buffer.append(cur_token.group('b'))

            elif cur_token.group('c'):  # special characters
                char = cur_token.group('c')
                if char in ',:=':
                    token_buffer.append(char)
                elif char == '#':
                    break
                elif char == '\\':
                    cur_token = next(token_iter, None)
                    if cur_token is None or cur_token.group('c') == '#':
                        return self.RET_CONTINUE # ask for next line
                    else:
                        raise LineParseError('There should not be any characters after "\\"')
                elif char == ';':
                    if execute:
                        ret = process.parse_and_process_command(self.token_buffer, self.m_state)
                        if ret != 0:
                            return ret
                        else:
                            self.token_buffer.clear()

        if execute:
            return process.parse_and_process_command(self.token_buffer, self.m_state)

    def complete(self, text, state):
        """ Complete function
        """

        if state == 0:
            tokens = self.token_buffer.copy()
            try:
                ret = self.handle_line(text, tokens, execute=False)
            except LineParseError:
                self.completion_buffer = []
            else:
                if ret == 0:
                    self.completion_buffer = process.get_completions(tokens)
                else:
                    self.completion_buffer = []
        
        else:
            self.completion_buffer = [c for c in self.completion_buffer if c.startswith(text)]

        return self.completion_buffer[state] if state < len(self.completion_buffer) else None

        

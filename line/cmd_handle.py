
import re
import sys
import logging
import os.path
from collections import deque
import rlcompleter
import readline

from . import state
from . import parse
from . import process
from . import completion
from .errors import LineParseError, print_error
from . import defaults
from . import plot

logger = logging.getLogger('line')
sh = logging.StreamHandler()
sh.setFormatter(logging.Formatter('[%(filename)s: %(funcName)s()] %(message)s'))
logger.addHandler(sh)


class CMDHandler:

    PS1 = 'line> '
    PS2 = '> '
    HISTORY_NAME = os.path.join(os.path.expanduser('~'), '.line_history')
    SOURCE_NAME = os.path.join(os.path.expanduser('~'), '.linerc')
    TOKEN_MATCHER = re.compile(r"(?P<a>([\"\'])(?:\\\2|(?:(?!\2)).)*(\2)?)|(?P<b>[^,:=;#\\\"\'\s]+)|(?P<c>[,:=;#\\])")
    
    # generally there are only 5 global-wise chracters: , : = # \

    RET_EXIT = 1
    RET_CONTINUE = 2

    _debug = False

    def __init__(self, m_state=None):

        self.token_buffer = deque()
        self.token_begin_pos = []
        self.completion_buffer = []

        if m_state is None:
            self.m_state = state.GlobalState()
            defaults.init_global_state(self.m_state)

        else:
            self.m_state = m_state

        self._filename = None

    def init_input(self):
        if self.HISTORY_NAME:
            try:
                readline.read_history_file(self.HISTORY_NAME)
            except IOError:
                pass 
        readline.parse_and_bind('tab: complete')
        readline.parse_and_bind('\\c-u: unix-line-discard')
        readline.parse_and_bind('\\c-a: beginning-of-line')
        readline.parse_and_bind('\\c-e: end-of-line')
        readline.parse_and_bind('\\c-f: forward-char')
        readline.parse_and_bind('\\c-b: backward-char')
        readline.parse_and_bind('\\m-f: forward-word')
        readline.parse_and_bind('\\m-b: backward-word')
        readline.set_completer(self.complete)
        readline.set_completer_delims(' ,;:=')

    def finalize_input(self):
        if self.HISTORY_NAME:
            readline.write_history_file(self.HISTORY_NAME)

    def read_source(self):
        try:
            self.proc_file(self.SOURCE_NAME)
        except IOError:
            pass

    def proc_file(self, filename, do_interactive=False):
        with open(filename, 'r') as f:
            self.m_state.is_interactive = do_interactive
            self._filename = filename
            self.proc_lines(f.readlines())

    def proc_lines(self, lines):
        plot.initialize(self.m_state)
        for line in lines:
            try:
                ret = self.handle_line(line, self.token_buffer, self.token_begin_pos, True)
            except Exception as e:
                if self._debug:
                    raise
                else:
                    if self.token_begin_pos:
                        token_pos = self.token_begin_pos[-len(self.token_buffer)-1 if len(self.token_buffer) < len(self.token_begin_pos) else 0]
                    else:
                        token_pos = 0
                    if self._filename:
                        print('"%s", line %d, col %d (near "%s"):' % (self._filename, lines.index(line), token_pos, line[token_pos:token_pos+5].strip('\n')),
                            file=sys.stderr)
                    else:
                        print('line %d, col %d (near "%s"):' % (lines.index(line), token_pos, line[token_pos:token_pos+5].strip('\n')), file=sys.stderr)

                    print_error(e)
                    self.token_buffer.clear()
                    self.token_begin_pos.clear()
                    return
            else:
                if ret == 0:
                    self.token_buffer.clear()
                    self.token_begin_pos.clear()
                elif ret == self.RET_EXIT:
                    break
                elif ret == self.RET_CONTINUE:
                    continue
            
            if self.m_state.is_interactive:
                self.input_loop()
                self.m_state.is_interactive = False

        plot.finalize(self.m_state)

    def proc_input(self, ps=PS1):
        self.m_state.is_interactive = True
        try:
            line = input(ps)
        except KeyboardInterrupt:
            return 1

        try:
            ret = self.handle_line(line, self.token_buffer, self.token_begin_pos, True)
        except Exception as e:
            
            if self._debug:
                raise
            else:
                if self.token_begin_pos:
                    token_pos = self.token_begin_pos[-len(self.token_buffer)-1 if len(self.token_buffer) < len(self.token_begin_pos) else 0]
                else:
                    token_pos = 0
                print(' ' * (len(ps) + token_pos) + '^')
                print_error(e)
                self.token_buffer.clear()
                self.token_begin_pos.clear()
                return 0            
        else:
            if ret == 0:
                self.token_buffer.clear()
                self.token_begin_pos.clear()
                return 0
            elif ret == self.RET_EXIT:
                return 1
            elif ret == self.RET_CONTINUE:
                return self.proc_input(self.PS2)

    def input_loop(self):
        self.init_input()
        plot.initialize(self.m_state)
        ret = 0
        while ret == 0:
            ret = self.proc_input()
        plot.finalize(self.m_state)
        self.finalize_input()

    def handle_line(self, line, token_buffer, token_begin_pos, execute=True):
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
                token_buffer.append(string)
                token_begin_pos.append(cur_token.start())

            elif cur_token.group('b'):  # variable or others
                token_buffer.append(cur_token.group('b'))
                token_begin_pos.append(cur_token.start())

            elif cur_token.group('c'):  # special characters
                char = cur_token.group('c')
                if char in ',:=':
                    token_buffer.append(char)
                    token_begin_pos.append(cur_token.start())
                elif char == '#':
                    break
                elif char == '\\':
                    cur_token = next(token_iter, None)
                    if cur_token is None or cur_token.group('c') == '#':
                        return self.RET_CONTINUE # ask for next line
                    else:
                        raise LineParseError('Character after "\\"')
                elif char == ';':
                    if execute:
                        ret = process.parse_and_process_command(self.token_buffer, self.m_state)
                        if ret != 0:
                            return ret
                        else:
                            token_buffer.clear()
                            token_begin_pos.clear()
                    else:
                        token_buffer.clear()
                        token_begin_pos.clear()

            else:
                raise RuntimeError()

        if execute:
            return process.parse_and_process_command(self.token_buffer, self.m_state)
        else:
            return 0

    def complete(self, text, state):
        """ Complete function
        """

        if state == 0:
            self.completion_buffer = completion.get_keywords() + completion.get_filelist(text)
            # tokens = self.token_buffer.copy()
            # try:
            #     ret = self.handle_line(text, tokens, execute=False)
            # except LineParseError:
            #     logger.debug('Failed to parse line')
            #     self.completion_buffer = []
            # else:
            #     if ret == 0:
            #         logger.debug('Tokens are: %s' % tokens)
            #         if text and tokens and re.match(r'\w', text[-1]):   # this is not riguous, but completion is only a choice anyway
            #             tokens.pop()
            #         self.completion_buffer = completion.get_completions(self.m_state, tokens)
            #     else:
            #         self.completion_buffer = []
        
        # else:
        #     self.completion_buffer = [c for c in self.completion_buffer if c.startswith(text)]

        _ret = [c for c in self.completion_buffer if c.startswith(text)] 
        return _ret[state] if state < len(_ret) else None

        # return self.completion_buffer[state] if state < len(self.completion_buffer) else None

        

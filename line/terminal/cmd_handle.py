
import re
import sys
import logging
import warnings
import os.path
from collections import deque
import readline
import threading

from .. import defaults
from .. import state
from .. import process
from .. import vm
from ..errors import LineParseError, format_error
from .. import backend
from .. import session
from . import completion_util

logger = logging.getLogger('line')
sh = logging.StreamHandler()
sh.setFormatter(logging.Formatter('[%(filename)s: %(funcName)s()] %(message)s'))
logger.addHandler(sh)


class CMDHandler:
    """ The shell for backward compatibility (without using prompt-toolkit)
    """

    PS1 = 'line> '
    PS2 = '> '
    HISTORY_NAME = os.path.join(os.path.expanduser('~'), '.line_history')
    SOURCE_NAME = os.path.join(os.path.expanduser('~'), '.linerc')
    TOKEN_MATCHER = re.compile(r"(?P<a>([\"\'])(?:\\\2|(?:(?!\2)).)*(\2)?)|(?P<b>[^,:=;#\\\"\'\s]+)|(?P<c>[,:=;#\\])")
    
    # generally there are only 5 global-wise chracters: , : = # \

    RET_EXIT = 1
    RET_CONTINUE = 2
    RET_USERERROR = 3
    RET_SYSERROR = 4    # only used here

    _debug = False
    _input_inited = False

    def __init__(self, m_state=None, preload_input=False):

        self.token_buffer = deque()
        self.token_begin_pos = []
        self.completion_buffer = []
        self._filename = None
        self._unpaired_quote = None

        if preload_input:
            th = threading.Thread(target=self.get_input_cache)
            th.start()
        else:
            self._input_cache = None
            th = None

        if m_state is None:
            self.m_state = session.get_instance(debug=self._debug, enable_history=True).state
            defaults.init_global_state(self.m_state)
            process.initialize()
        else:
            self.m_state = m_state

        if th is not None:
            try:
                th.join()
            except KeyboardInterrupt:
                exit()

    def init_input(self):
        if self._input_inited:
            return

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
        self._input_inited = True

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
            return self.proc_lines(f.readlines())

    def proc_stdin(self):
        self._filename = '<stdin>'
        return self.proc_lines(sys.stdin.readlines())

    def proc_lines(self, lines):
        backend.initialize(self.m_state)
        for j, line in enumerate(lines):
            try:
                ret = self.handle_line(line, self.token_buffer, self.token_begin_pos, True, j)
            except Exception as e:
                ret = self.RET_SYSERROR
                if self._debug:
                    raise
                else:
                    print_error(e)
                    break
            else:
                if ret == 0:
                    pass
                elif ret == self.RET_EXIT:
                    break
                elif ret == self.RET_CONTINUE:
                    continue
                elif isinstance(ret, tuple) and ret[0] == self.RET_USERERROR:
                    dbg_info = ret[1]
                    print('%sline %d, col %d (near "%s")' % (
                        ('"%s", ' % dbg_info.filename if dbg_info.filename else ''),
                        dbg_info.lineid + 1,
                        dbg_info.token_pos + 1,
                        lines[dbg_info.lineid][dbg_info.token_pos:dbg_info.token_pos+5].strip('\n')
                    ), file=sys.stderr)
                    # FIXME here lineid is constant; cannot handle the case of multiple \\
                    print_error(ret[2])
                    break
                else:
                    print('Undefined return:', ret)

                self.token_buffer.clear()
                self.token_begin_pos.clear()
            
            if self.m_state.is_interactive:
                self.input_loop()
                self.m_state.is_interactive = False

        backend.finalize(self.m_state)
        return ret if ret != self.RET_EXIT else 0

    def proc_input(self, ps=PS1):
        self.m_state.is_interactive = True
        if self._input_cache is not None:
            line = self._input_cache
            self._input_cache = None
        else:
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
                print_error(e)
                self.token_buffer.clear()
                self.token_begin_pos.clear()
                return 0            
        else:
            if ret == 0:
                pass
            elif ret == self.RET_EXIT:
                return 1
            elif ret == self.RET_CONTINUE:
                return self.proc_input(self.PS2)
            elif isinstance(ret, tuple) and ret[0] == self.RET_USERERROR:
                dbg_info = ret[1]
                if dbg_info.lineid == 0:
                    print(' ' * (len(ps) + dbg_info.token_pos) + '^')
                else:
                    print('%sline %d, col %d' % (
                        ('"%s", ' % dbg_info.filename if dbg_info.filename else ''),
                        dbg_info.lineid + 1,
                        dbg_info.token_pos + 1,
                    ), file=sys.stderr)
                print_error(ret[2])
            else:
                print('Undefined return:', ret)

            self.token_buffer.clear()
            self.token_begin_pos.clear()
            return 0

    def get_input_cache(self):
        self.init_input()
        try:
            self._input_cache = input(self.PS1)
        except KeyboardInterrupt:
            import os
            os._exit(1)
        

    def input_loop(self):
        self.init_input()
        self._filename = '<interactive>'
        backend.initialize(self.m_state, silent=session.get_state().options['remote'])
        ret = 0
        while ret == 0:
            ret = self.proc_input()
        backend.finalize(self.m_state)
        self.finalize_input()
        return 0

    def handle_line(self, line, token_buffer, token_begin_pos, execute=True, lineid=0):
        """ Preprocessing and execute
        """
        logger.debug('Handle input line: %s' % line)
        if self._unpaired_quote is not None:
            j = line.find(self._unpaired_quote)
            if j != -1:
                self.token_buffer[-1] += line[:j+1] # TODO check if '\n' is necessary
                line = line[j+1:]
                self._unpaired_quote = None
            else:
                self.token_buffer[-1] += line.strip('\n')
                return self.RET_CONTINUE

        token_iter = self.TOKEN_MATCHER.finditer(line)
        
        while True:
            cur_token = next(token_iter, None)
            if cur_token is None:
                break

            if cur_token.group('a'):    # string
                string = cur_token.group('a')
                token_buffer.append(string)
                token_begin_pos.append(cur_token.start())
                if string[-1] != string[0]:
                    self._unpaired_quote = string[0]
                    # raise LineParseError("Quote not match")
                    return self.RET_CONTINUE

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
                    return self.RET_CONTINUE
                elif char == ';':
                    if execute:
                        ret = self.m_state._vmhost.process(self.m_state, self.token_buffer, 
                            vm.LineDebugInfo(self._filename, lineid, self.token_begin_pos.copy()))
                        #ret = process.parse_and_process_command(self.token_buffer, self.m_state)
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
            return self.m_state._vmhost.process(self.m_state, self.token_buffer, 
                vm.LineDebugInfo(self._filename, lineid, self.token_begin_pos.copy()))
            # return process.parse_and_process_command(self.token_buffer, self.m_state)
        else:
            return 0

    def complete(self, text, state):
        """ Complete function
        """

        if state == 0:
            self.completion_buffer = completion_util.get_keywords() + completion_util.get_filelist(text)
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

        
def query_cond(question, cond, default, set_true=True):
    """ If cond is True, ask question and get answer, otherwise use default.
    if `set_ture`, automatically convert positive answer to True, and other False.
    """
    if cond:
        answer = input(question)
        if set_true:
            answer = answer in ('y', 'Y', 'yes', 'Yes')
        return answer
    else:
        return default


def print_error(e):
    print(format_error(e), file=sys.stderr)


def show_warning(message, *args):
    if isinstance(message, UserWarning):
        print(message)
    else:
        return warnings.showwarning(message, *args)

warnings.showwarning = show_warning

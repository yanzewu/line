
import re
import sys
import logging
import os.path
from collections import deque
import prompt_toolkit as pt
import threading
import asyncio
import warnings
pt_inputhooks = None

from .. import defaults
from ..errors import LineParseError, format_error
from .. import state
from .. import session
from .. import process
from .. import backend
from ..vm import LineDebugInfo

from . import completion
from . import logging_util


# init the output devices

warnings.showwarning = logging_util.showwarning
logging_util.init_logger()
logger = logging.getLogger('line')


class CMDHandler:

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
    _input_session = None

    def __init__(self, m_state=None, preload_input=False):
        """ Starting the shell and GUI engine. There may be multiple CMDHandler, but only a single instance of shell.
        Args:
            m_state: If `None', will create one. Otherwise will use the given one.
            preload_input: Asynchronously load the input string.
        """
        self.token_buffer = deque()
        self.token_begin_pos = []
        self._filename = None
        self._unpaired_quote = None

        if preload_input:
            th = threading.Thread(target=self.get_input_cache)
            th.start()
        else:
            self._input_cache = None
            th = None

        if m_state is None:
            self.init_backend()
        self.m_state = session.get_state()

        if th is not None:
            try:
                th.join()
            except KeyboardInterrupt:
                exit()
            
        # should talk with backend here.
        _, hook = pt_inputhooks.get_inputhook_name_and_func('qt')
        asyncio.set_event_loop(pt.eventloop.new_eventloop_with_inputhook(hook))

    def init_backend(self):
        """ Initialize states and backends.
        Including all performance affecting steps (import of mpl and ipython).
        """
        sess = session.get_instance(debug=CMDHandler._debug)
        self.m_state = sess.state
        process.initialize()

        global pt_inputhooks
        from IPython.terminal import pt_inputhooks as pt_inputhooks_1
        pt_inputhooks = pt_inputhooks_1

    def init_input(self):
        """ Executed when start/switch to the interactive mode.
        """
        if CMDHandler._input_session:
            return
        else:
            CMDHandler._input_session = pt.PromptSession(
                history=ReadlineHistory(self.HISTORY_NAME),
                enable_history_search=True,
            )

    def finalize_input(self):
        """ Executed when leave interactive mode.
        """
        pass

    def get_input_cache(self):
        """ Asynchronic version for input. Main thread is loading modules.
        """
        self.init_input()
        try:
            self._input_cache = CMDHandler._input_session.prompt(self.PS1, completer=completion.Completer())
        except KeyboardInterrupt:
            import os
            os._exit(1)
 

    def read_source(self):
        """ Read the ~/.linerc file.
        """
        try:
            return self.proc_file(self.SOURCE_NAME)
        except IOError:
            pass


    def input_loop(self):
        """ The shell loop. Will always return 0 after finalization.
        """
        self.init_input()
        self.m_state.is_interactive = True
        backend.initialize(self.m_state)
        ps = self.PS1
        while True:
            if self._input_cache is not None:
                line = self._input_cache
                self._input_cache = None
            else:
                try:
                    line = CMDHandler._input_session.prompt(ps, completer=completion.Completer())
                except KeyboardInterrupt:
                    break

            ret = self.proc_line_interactive(line, ps)
            if ret != self.RET_CONTINUE:
                self.lexer_cleanup()
                ps = self.PS1
            else:
                ps = self.PS2

            if ret == self.RET_EXIT:
                break
            elif ret == self.RET_USERERROR:
                self.print_error(None, len(ps))
            
        backend.finalize(self.m_state)
        self.finalize_input()
        return 0

    def proc_file(self, filename, do_interactive=False):
        with open(filename, 'r') as f:
            self.m_state.is_interactive = do_interactive
            self._filename = filename
            return self.proc_lines(f.readlines())

    def proc_stdin(self):
        self._filename = '<stdin>'
        return self.proc_lines(sys.stdin.readlines())

    def proc_lines(self, lines):
        """ Process a list of lines.
        Returns 0 if process ended up normally without error; Otherwise return RET_USERERROR or RET_SYSERROR
        """
        backend.initialize(self.m_state)
        for j, line in enumerate(lines):
            ret = self.proc_line_noniteractive(line, j)
            if ret != self.RET_CONTINUE:
                self.lexer_cleanup()
            if ret == self.RET_USERERROR:
                self.print_error(lines, 0)
                break
            elif ret == self.RET_EXIT or ret == self.RET_SYSERROR:
                break

        backend.finalize(self.m_state)
        return ret if ret != self.RET_EXIT else 0

    def proc_line_noniteractive(self, line, lineid:int):
        """ Process one line in noninteractive mode.
        Returns the return code.
        """
        try:
            ret = self.handle_line(line, self.token_buffer, self.token_begin_pos, True, lineid)
        except Exception as e:
            if CMDHandler._debug:
                raise
            else:
                logging_util.print_error_string(format_error(e))
                return self.RET_SYSERROR
        else:
            if ret == 0:
                if self.m_state.is_interactive:     # initiate an input_loop, when switch to input mode
                    self.input_loop()
                    self.m_state.is_interactive = False
                return 0
            elif ret == self.RET_EXIT or ret == self.RET_CONTINUE:  # FIXME here lineid is constant; cannot handle the case of multiple
                return ret
            elif isinstance(ret, tuple) and ret[0] == self.RET_USERERROR:
                return self.RET_USERERROR
            else:
                logging_util.print_error_string('Undefined return: %r' % ret)
                return self.RET_SYSERROR

    def proc_line_interactive(self, line, ps):
        """ Process one line in interactive mode.
        Returns the return code.
        """
        
        try:
            ret = self.handle_line(line, self.token_buffer, self.token_begin_pos, True)
        except Exception as e:
            if CMDHandler._debug:
                raise
            else:   # This should only be VM errors
                logging_util.print_error_string(format_error(e))
                return self.RET_SYSERROR
        else:
            if ret == 0 or ret == self.RET_EXIT or ret == self.RET_CONTINUE:
                return ret
            elif isinstance(ret, tuple) and ret[0] == self.RET_USERERROR:
                return self.RET_USERERROR
            else:
                logging_util.print_error_string('Undefined return: %r' % ret)
                return self.RET_SYSERROR

    def print_error(self, lines, extra_indent=0):
        backtrace = session.get_vm().backtrace
        error = session.get_vm().error

        line = lines[backtrace.lineid].strip('\n') if lines else None
        logging_util.print_error_formatted(error, backtrace, session.is_interactive(), line, extra_indent)

    # === LEXER ===

    def lexer_cleanup(self):
        self.token_buffer.clear()
        self.token_begin_pos.clear()

    def handle_line(self, line:str, token_buffer:deque, token_begin_pos:int, execute=True, lineid=0):
        """ Tokenize and execute.
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
                            LineDebugInfo(self._filename, lineid, self.token_begin_pos.copy()))
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
                LineDebugInfo(self._filename, lineid, self.token_begin_pos.copy()))
        else:
            return 0

        
class ReadlineHistory(pt.history.FileHistory):

    def load_history_strings(self):
        try:
            with open(self.filename, 'r') as f:
                lines = f.readlines()
                for line in reversed(lines):
                    yield line.rstrip('\n')
        except IOError:
            return

    def store_string(self, s):
        with open(self.filename, 'a') as f:
            print(s, file=f)


def query_cond(question, cond, default, set_true=True):
    """ If cond is True, ask question and get answer, otherwise use default.
    if `set_ture`, automatically convert positive answer to True, and other False.
    """
    if cond:
        answer = pt.prompt(pt.formatted_text.FormattedText([('white', question)]))
        if set_true:
            answer = answer in ('y', 'Y', 'yes', 'Yes')
        return answer
    else:
        return default


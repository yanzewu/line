
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
from . import lexer

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

    def proc_input(self):
        """ The shell loop. Will always return 0 after finalization.
        """
        self.init_input()
        self.m_state.is_interactive = True
        self.ps = CMDHandler.PS1

        def fetch_next_line(forced):
            if self._input_cache is not None:
                line = self._input_cache
                self._input_cache = None
                return line
            else:
                self.ps = CMDHandler.PS1 if not forced else CMDHandler.PS2
                try:
                    return CMDHandler._input_session.prompt(self.ps, completer=completion.Completer())
                except KeyboardInterrupt:
                    return None

        def fetch_previous_line(offset):
            return CMDHandler._input_session.history.get_strings()[offset-1] if offset < 0 else None

        self.proc_(fetch_next_line, fetch_previous_line, False, True)
        self.finalize_input()
        return 0

    input_loop = proc_input

    def proc_file(self, filename, do_interactive=False):
        with open(filename, 'r') as f:
            self.m_state.is_interactive = do_interactive
            self._filename = filename
            return self.proc_lines(f.readlines())

    def proc_stdin(self):
        self._filename = '<stdin>'
        return self.proc_lines(sys.stdin.readlines())

    def proc_lines(self, lines):
        j = [-1]
        def fetch_next_line(forced):
            j[0] += 1
            return lines[j[0]].strip('\n') if j[0] < len(lines) else None

        def fetch_previous_line(offset):
            return lines[j[0]+offset].strip('\n')

        return self.proc_(fetch_next_line, fetch_previous_line, True, False)

    def proc_(self, fetch_next_line, fetch_previous_line, exit_on_error=True, is_interactive=False):
        """ The REPL loop.
        fetch_next_line(forced:bool)->str: Should return the next line without break ('\n'); 
            If continuing last line, `forced` will be true.
        fetch_previous_line(offset:int)->str: Should return current lineid + offset (if 0 then current line).
        exit_on_error: Break when an error occurs (even if it is handled);
            Otherwise only returns when ret == RET_EXIT or RET_SYSERROR.
        is_interactive: Being able to respond command `input`.
        """

        l = lexer.Lexer()
        backend.initialize(session.get_state())
        ret = 0
        emittor = l.run(fetch_next_line)

        while True:
            try:
                tokens, tp = next(emittor)
            except LineParseError as e: # TODO clean lexer or initiate a new one
                if self._debug:
                    raise
                else:
                    logging_util.print_error_formatted(e, 
                        LineDebugInfo(self._filename, 0, (l.lineid, l.head)), 
                        session.get_state().is_interactive,
                        fetch_previous_line(0),
                        len(self.ps) if is_interactive else 0)

                    emittor = l.run(fetch_next_line)
                    ret = self.RET_USERERROR
            except StopIteration:
                ret = self.RET_EXIT
            except KeyboardInterrupt:
                ret = self.RET_EXIT
            else:
                if not tokens:
                    continue
                logger.debug("Tokens are: %s" % list(tokens))
                ret = session.get_vm().process(session.get_state(), tokens, LineDebugInfo(self._filename, 0, tp))
                if ret == 0:
                    if not is_interactive and self.m_state.is_interactive:     # initiate an input_loop, when switch to input mode
                        self.proc_input()
                        self.m_state.is_interactive = False
                elif ret == self.RET_EXIT:
                    pass
                elif isinstance(ret, tuple) and ret[0] == self.RET_USERERROR:
                    m_vm = session.get_vm()
                    logging_util.print_error_formatted(m_vm.error, 
                        m_vm.backtrace, 
                        session.get_state().is_interactive,
                        fetch_previous_line(m_vm.backtrace.token_pos[0] - l.lineid),
                        len(self.ps) if is_interactive else 0)
                    ret = ret[0]
                else:
                    logging_util.print_error_string('Undefined return: %r' % ret)
                    ret = self.RET_SYSERROR

            if not (ret == self.RET_USERERROR and not exit_on_error or ret == 0):
                break
                
        backend.finalize(session.get_state())
        return 0 if ret == self.RET_EXIT else ret

        
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


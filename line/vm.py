
from collections import namedtuple

from . import process
from . import parse_util
from . import option_util
from . import errors
from . import keywords

class CodeBlock:

    def __init__(self):
        self.loop_var = None
        self.loop_range = None
        self.cond = None
        self.stmts = []

LineDebugInfo = namedtuple('LineDebugInfo', ['filename', 'lineid', 'token_pos'])

class Frame:

    def __init__(self, argv:list, caller:tuple, block_level:int):
        self.argv = argv
        self.caller_pc = caller
        self.option_cache = None
        self.block_level = block_level

    def get_arg(self, index:int):
        return self.argv[index] if index < len(self.argv) else ''

    def argc(self):
        return len(self.argv)

    def get_option(self, name):
        if self.option_cache is None:
            self.option_cache = option_util.get_options(self.argv[1:], option_util.parse_token)
        return self.option_cache.get(name, None)

class VMHost:

    MODE_EXEC = 0
    MODE_RECORD = 1
    MODE_RECORD_IF = 2
    MODE_RECORD_LOOP = 3
    MODE_ERROR = 7

    def __init__(self, debug=False):
        self.mode = VMHost.MODE_EXEC
        self.debug = debug
        self.records = {}
        self.cur_record_name = None

        self.stack = []
        self.block_level = 0    # control block stack height
        self.pc = None
        self.backtrace = []     # list of (error, ldi)

        import numpy as np
        
        self.variables = {
            '__varx': np.arange(-5, 5, 1), 
            '__varpi': np.pi,
            '__vartrue': True,
            '__varfalse': False,
            'arg': lambda x: self.stack[-1].get_arg(int(x)),
            'argc': lambda: self.stack[-1].argc(),
            'option': lambda x=None: self.stack[-1].get_option(x),
            'cond': lambda x,a,b: a if x else b,
            'set':self.set_variable,
            'exist': self.exist_variable,
            }
        

    def process(self, state, tokens, line_debug_info:LineDebugInfo):
        try:
            self.pc = (line_debug_info, tokens)     # point to LDI, tokens
            self.backtrace.clear()
            return self.process_unsafe(state, tokens, line_debug_info)
        except Exception as e:
            if self.debug:
                raise
            else:
                self.mode = VMHost.MODE_ERROR
                self.backtrace.append((e, self._assemble_backtrace(self.pc)))
                return 3

    def process_unsafe(self, state, tokens, line_debug_info):
        
        if self.mode == VMHost.MODE_EXEC:
            self.variables['state'] = lambda: state
            return self.exec_special(state, tokens, line_debug_info)
            
        elif self.mode in (VMHost.MODE_RECORD, VMHost.MODE_RECORD_LOOP, VMHost.MODE_RECORD_IF):
            if parse_util.lookup(tokens) in ('done', 'end'):
                self.block_level -= 1
                if self.block_level == 0:
                    return self.exec_done(state)
                else:
                    return self.record(tokens, line_debug_info)
            elif self.mode == VMHost.MODE_RECORD_IF and parse_util.lookup(tokens) == 'else':
                if self.records['else'] is None:   # else is greedy matched
                    parse_util.get_token(tokens)
                    self._push_record('else', CodeBlock())
                    return self.record(tokens, line_debug_info)
                else:
                    return self.record(tokens, line_debug_info)
            else:
                if parse_util.lookup(tokens) in ('if', 'for') or (
                    parse_util.lookup(tokens) == 'let' and parse_util.lookup(tokens, 3) == 'do'):
                    self.block_level += 1
                return self.record(tokens, line_debug_info)
        elif self.mode == VMHost.MODE_ERROR:
            return 3
        else:
            raise ValueError(self.mode)

    def exec_special(self, state, tokens, line_debug_info):

        if parse_util.test_token_inc(tokens, 'for'):
            block = CodeBlock()
            block.loop_var = parse_util.get_token(tokens)
            parse_util.assert_token(parse_util.get_token(tokens), '=')
            expr = parse_util.parse_expr(tokens)
            parse_util.assert_token(parse_util.get_token(tokens), 'do')
            ret = process.process_expr(state, expr)
            if isinstance(ret, str):
                ret = ret.split()
            block.loop_range = ret
            self._push_record('for', block)
            self.block_level += 1
            self.record(tokens, line_debug_info)
            self.mode = VMHost.MODE_RECORD_LOOP

        elif parse_util.test_token_inc(tokens, 'if'):
            cond = process.parse_and_process_if(state, tokens)

            if parse_util.test_token_inc(tokens, "then"):
                block = CodeBlock()
                block.cond = cond
                self._push_record('if', block)
                self.block_level += 1
                self.record(tokens, line_debug_info)
                self.mode = VMHost.MODE_RECORD_IF
                self.records['else'] = None     # clear else part, prevent misexecution
            elif parse_util.lookup(tokens) == 'call':
                if cond:
                    return self.exec_special(state, tokens, line_debug_info)
            else:
                raise errors.LineParseError('"then" or "call" required')

        elif parse_util.test_token_inc(tokens, 'let'):
            fname = parse_util.get_token(tokens)
            parse_util.assert_token(parse_util.get_token(tokens), '=')
            if parse_util.test_token_inc(tokens, 'do'):
                self._push_record(fname, CodeBlock())
                self.block_level += 1
                self.record(tokens, line_debug_info)
                self.mode = VMHost.MODE_RECORD
            else:
                expr = parse_util.parse_expr(tokens)
                parse_util.assert_no_token(tokens)
                ret = process.process_expr(state, expr)
                self.set_variable(fname, ret)

        elif parse_util.test_token_inc(tokens, 'call'):
            return self.exec_invoke(state, tokens)
        else:
            return process.parse_and_process_command(tokens, state)

        return 0

    def exec_invoke(self, state, tokens):
        function = parse_util.get_token(tokens)
        if keywords.command_alias.get(function, function) in keywords.control_keywords:
            raise errors.LineParseError("Cannot use %s as function name" % function)
        block = self.records.get(function, None)
        if not block:
            raise errors.LineProcessError("Undefined function: %s" % function)
        new_args = [function]
        while len(tokens) > 0:
            if parse_util.lookup_raw(tokens).startswith('$'):
                new_args.append(process.process_expr(state, parse_util.parse_expr(tokens)))
            else:
                new_args.append(parse_util.get_token(tokens))
        self.push_args(new_args)
        r = self.exec_block(state, block)
        self.pop_args()
        return r

    def exec_done(self, state):
        if self.mode == VMHost.MODE_RECORD_LOOP: # for-loop: will execute it right away
            block = self.records.get(self.cur_record_name, None)
            self.mode = VMHost.MODE_EXEC
            return self.exec_block(state, block)
        elif self.mode == VMHost.MODE_RECORD:
            self.mode = VMHost.MODE_EXEC
        elif self.mode == VMHost.MODE_RECORD_IF:
            blockif = self.records.get('if', None)
            blockelse = self.records.get('else', None)
            self.mode = VMHost.MODE_EXEC
            if blockif.cond:
                return self.exec_block(state, blockif)
            elif blockelse:
                return self.exec_block(state, blockelse)
        
        return 0

    def exec_block(self, state, block):
        if block.loop_var:
            for x in block.loop_range:
                self.set_variable(block.loop_var, x)
                for stmt, info in block.stmts:
                    r = self.process(state, stmt.copy(), info)
                    if r != 0:
                        return r
        else:
            for stmt, info in block.stmts:
                r = self.process(state, stmt.copy(), info)
                if r != 0:
                    return r
        return 0

    def record(self, tokens, line_debug_info:LineDebugInfo):
        self._cur_record().stmts.append((tokens.copy(), line_debug_info))
        return 0

    def get_variable(self, name:str):
        return self.variables[process.expr_proc.ExprEvaler.convert_varname(name)]

    def set_variable(self, name:str, value):
        self.variables[process.expr_proc.ExprEvaler.convert_varname(name)] = value

    def exist_variable(self, name:str):
        return process.expr_proc.ExprEvaler.convert_varname(name) in self.variables

    def push_args(self, args:list):
        if len(self.stack) > 512:
            raise errors.LineProcessError("Maximum recursion (512) reached.")
        self.stack.append(Frame(args, self.pc, self.block_level))
        self.set_variable('argv', self.stack[-1].argv)
        self.block_level = 0

    def pop_args(self, discard_incomplete_control=False):
        lastframe = self.stack.pop()
        self.block_level = lastframe.block_level
        if len(self.stack) > 0:
            self.set_variable('argv', self.stack[-1].argv)
        if self.mode in (VMHost.MODE_RECORD, VMHost.MODE_RECORD_LOOP, VMHost.MODE_RECORD_IF):
            if not discard_incomplete_control:
                self.mode = VMHost.MODE_ERROR
                raise errors.LineParseError("Missing 'end' of control block in file \"%s\"" % (self.pc[0].filename))
            else:
                self.mode = VMHost.MODE_EXEC
        elif self.mode == VMHost.MODE_ERROR:
            context = self.stack[-1].argv[0] if self.stack and self.stack[-1].argv else ''
            self.backtrace.append((errors.LineBacktrace(context), self._assemble_backtrace(lastframe.caller_pc)))

    def set_error(self):
        self.mode = VMHost.MODE_ERROR

    def deset_error(self):
        self.mode = VMHost.MODE_EXEC
        self.backtrace.clear()

    def _assemble_backtrace(self, pc):
        line_debug_info, tokens = pc
        p = -len(tokens)-1
        if p <= -len(line_debug_info.token_pos):
            p = 0
        return LineDebugInfo(line_debug_info.filename, 
            line_debug_info.lineid,
            line_debug_info.token_pos[p])

    def _cur_record(self):
        return self.records.get(self.cur_record_name, None)

    def _push_record(self, name, block):
        self.records[name] = block
        self.cur_record_name = name


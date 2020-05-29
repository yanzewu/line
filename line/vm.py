
from collections import namedtuple

from . import process
from . import parse_util
from . import errors


class CodeBlock:

    def __init__(self):
        self.loop_var = None
        self.loop_range = None
        self.stmts = []

LineDebugInfo = namedtuple('LineDebugInfo', ['filename', 'lineid', 'token_pos'])

class VMHost:

    def __init__(self, debug=False):
        self.mode = 'exec'
        self.debug = debug
        self.records = {}
        self.cur_record_name = None

        self.arg_stack = []

        import numpy as np
        
        self.variables = {'__varx': np.arange(-5, 5, 1), 'arg':lambda x:self.arg_stack[-1][x], 'set':self.set_variable}
        

    def process(self, state, tokens, line_debug_info):
        try:
            return self.process_unsafe(state, tokens, line_debug_info)
        except Exception as e:
            if self.debug:
                raise
            else:
                p = -len(tokens)-1
                if p <= -len(line_debug_info.token_pos):
                    p = 0
                return 3,  LineDebugInfo(line_debug_info.filename, 
                    line_debug_info.lineid, 
                    line_debug_info.token_pos[p]), e

    def process_unsafe(self, state, tokens, line_debug_info):
        
        if self.mode == 'exec':
            self.variables['state'] = lambda: state
            return self.exec_special(state, tokens, line_debug_info)
            
        elif self.mode == 'record' or self.mode == 'recorddo':
            if parse_util.test_token_inc(tokens, 'done'):
                return self.exec_done(state)
            else:
                self.record(tokens, line_debug_info)
                return 0
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
            self.record(tokens, line_debug_info)
            self.mode = 'recorddo'

        elif parse_util.test_token_inc(tokens, 'let'):
            fname = parse_util.get_token(tokens)
            parse_util.assert_token(parse_util.get_token(tokens), '=')
            if parse_util.test_token_inc(tokens, 'do'):
                self._push_record(fname, CodeBlock())
                self.mode = 'record'
            else:
                expr = parse_util.parse_expr(tokens)
                parse_util.assert_no_token(tokens)
                ret = process.process_expr(state, expr)
                self.set_variable(fname, ret)

        elif parse_util.test_token_inc(tokens, 'call'):
            function = parse_util.get_token(tokens)
            block = self.records.get(function, None)
            if not block:
                raise errors.LineProcessError("Undefined function: %s" % function)
            new_args = [function]
            while len(tokens) > 0:
                new_args.append(process.process_expr(state, parse_util.parse_expr(tokens)))
            self.arg_stack.append(new_args)
            r = self.exec_block(state, block)
            self.arg_stack.pop()
            if r != 0:
                return r
        else:
            return process.parse_and_process_command(tokens, state)

        return 0

    def exec_done(self, state):
        if self.mode == 'recorddo':
            block = self.records.get(self.cur_record_name, None)
            self.mode = 'exec'
            return self.exec_block(state, block)
        elif self.mode == 'record':
            self.mode = 'exec'
        
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

    def record(self, tokens, line_debug_info):
        self._cur_record().stmts.append((tokens.copy(), line_debug_info))

    def get_variable(self, name):
        return self.variables[process.expr_proc.ExprEvaler.convert_varname(name)]

    def set_variable(self, name, value):
        self.variables[process.expr_proc.ExprEvaler.convert_varname(name)] = value

    def push_args(self, args):
        self.arg_stack.append(args)

    def pop_args(self):
        self.arg_stack.pop()

    def _cur_record(self):
        return self.records.get(self.cur_record_name, None)

    def _push_record(self, name, block):
        self.records[name] = block
        self.cur_record_name = name


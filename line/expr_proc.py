
import re
import logging
import numpy as np
import pandas as pd
import warnings

from . import stat_util
from . import model
from . import io_util
from .graphing import scale
from .errors import LineParseError, LineProcessError

_VAR_EXPR = re.compile(r'\$[_0-9a-zA-Z\*\?\.]+\b')
_TOKEN_EXPR = re.compile(r'\b[_a-zA-Z]([0-9a-zA-Z][_0-9a-zA-Z\.]*)?(?!\()\b')
_INNSTR_EXPR = re.compile(r'\b__str\d+\b')
_INNVAR_EXPR = re.compile(r'\b__var[_0-9a-zA-Z]+\b')
_SPECIAL_BRACKET = re.compile(r'\$\!?\(')
_SPECIAL_BRACKET_MAPPER = {'$(': '(', '$!(': 'python('}

logger = logging.getLogger('line')

def _get_ufunc_list(name_list):
    
    return dict([(l, getattr(np, l)) if isinstance(l, str) else (l[0], getattr(np, l[1])) for l in name_list])


class ExprEvaler:

    FUNCTIONS = {
            **_get_ufunc_list([
                'mod', 'fmod', 'abs', 'rint', 'sign', 'heaviside', ('rem', 'remainder'), 
                'conj', 'exp', 'exp2', 'log', 'log2', 'log10', 'sqrt', 'square',
                'sin', 'cos', 'tan', 'sinh', 'cosh', 'tanh',
                ('asin', 'arcsin'), ('acos', 'arccos'), ('atan', 'arctan'), ('atan2', 'arctan2'),
                ('asinh', 'arcsinh'), ('acosh', 'arccosh'), ('atanh', 'arctanh'),
                ('mand', 'logical_and'), ('mor', 'logical_or'), ('mnot', 'logical_not'),
                ('max', 'maximum'), ('min', 'minimum'), 'floor', 'ceil',
                'sum', 'cumsum', ('tp', 'transpose'), 'linspace', 'array', ('range', 'arange'),
            ]),
            'all':all, 'any':any, 'ascii':ascii, 'bool':bool, 'chr':chr, 'dict':dict, 'float':float, 
            'format':format, 'int':int, 'len':len, 'list':list, 'max':max, 'min':min,
            'ord':ord, 'pow':pow, 'reversed':reversed, 'round':round, 'sorted':sorted,
            'str':str, 'sum':sum,
            'split':str.split,
            'startswith':str.startswith,
            'ismember': lambda x, a: x in a,
            'hist': stat_util.histogram,
            'load': model.load_file,
            'save': model.save_file,
            'stack': model.util.stack,
            'expand': io_util.expand,
            'load_stdin': model.load_stdin,
            'save_stdout': model.save_stdout,
            'makerange': scale.make_range,
            'col':None,
            'cols': None,
            'hint':None,
        }

    def __init__(self, m_globals:dict, m_file_caches:dict):
        self.m_globals = m_globals          # predefined variables
        self.m_file_caches = m_file_caches  # file cache, transparent for outside
        self.m_locals = {}                  # runtime evaluated variables
        self.m_globals['python'] = self.evaluate_system # the single special command requires call to self
        self.m_globals['system'] = self.evaluate_shell

    def load(self, expr:str, omit_dollar=False, variable_prefix='__var'):
        self.expr = canonicalize(expr, omit_dollar, variable_prefix=variable_prefix)
        logger.debug(self.expr)

    def load_singlevar(self, expr:str):
        self.expr = ExprEvaler.convert_varname(expr)
        logger.debug(self.expr)
    
    @staticmethod
    def convert_varname(expr:str):
        if expr.startswith('\'') or expr.endswith('"'):
            return '__var' + expr[1:-1]
        elif expr.startswith('$'):
            return '__var' + expr[1:]
        else:
            return '__var' + expr

    def evaluate_system(self, expr:str):
        if not isinstance(expr, str):
            raise LineProcessError('string required')
        
        safety = self.m_globals['state']().options['safety']
        if safety != 0:
            warnings.warn('Executing native python code which may not be safe.')

        evaler = ExprEvaler(self.m_globals, self.m_file_caches)
        evaler.load(expr, omit_dollar=True, variable_prefix='')
        return evaler._eval(False)

    def evaluate_shell(self, expr:str):
        if not isinstance(expr, str):
            raise LineProcessError('string required')
        
        safety = self.m_globals['state']().options['safety']
        if safety != 0:
            warnings.warn('Executing shell code which may not be safe.')
        
        import os
        return os.system(expr)

    def evaluate(self):
        """ Evaluate expression; Return an array-like object.
        """
        for v in _INNVAR_EXPR.findall(self.expr):
            if v not in self.m_globals and v not in self.m_file_caches:
                try:
                    self.m_file_caches[v] = model.load_file(self.strip_var(v))
                except IOError:
                    raise LineProcessError('Undefined variable: "%s"' % self.strip_var(v))
        return self._eval()

    def evaluate_singlevar(self):
        v = self.expr
        if v in self.m_globals:
            return self.m_globals[v]
        elif v in self.m_file_caches:
            return self.m_file_caches[v]
        else:
            try:
                self.m_file_caches[v] = model.load_file(self.strip_var(v))
                return self.m_file_caches[v]
            except IOError:
                raise LineProcessError('Undefined variable: "%s"' % self.strip_var(v))

    def evaluate_with_hintvar(self, hintvar=None):
        """ Evaluate expression, try interpret undefined variable as column
        label of hintvar.
        """
        self.hintvalue = hintvar

        self.m_locals['col'] = lambda x: model.util.loc_col_str(self.hintvalue, str(x))
        self.m_locals['cols'] = lambda x: model.util.loc_col_wildcard(self.hintvalue, str(x))
        self.m_locals['hint'] = lambda: self.hintvalue
      
        for v in _INNVAR_EXPR.findall(self.expr):
            if v not in self.m_globals and v not in self.m_file_caches:
                try:
                    self.m_file_caches[v] = model.load_file(self.strip_var(v))
                except IOError:
                    try:
                        self.m_locals[v] = model.util.loc_col_str(self.hintvalue, self.strip_var(v))
                    except IndexError:
                        if self.strip_var(v).isdigit():
                            raise LineProcessError('Index out of bounds: %s' % self.strip_var(v))
                        else:
                            raise LineProcessError('Undefined variable: "%s"' % self.strip_var(v))
        return self._eval()

    def _eval(self, supress_builtins=True):
        _m_globals = self.FUNCTIONS.copy()
        _m_globals.update(self.m_file_caches)
        _m_globals.update(self.m_globals)
        if supress_builtins:
            _m_globals.update({'__builtins__': None})
        return eval(self.expr, _m_globals, self.m_locals)

    def strip_var(self, varname:str):
        return varname[5:]
        
        
def canonicalize(expr:str, omit_dollar:bool=False, variable_prefix:str='__var') -> str:
    """ Check expression quote, bracket and doing the following variable replacement:
    $foo => __varfoo
    if `omit_dollar' is set, also try to replace foo => __varfoo
    """

    expr = expr.strip()

    # check string and bracket
    m_bracket = []
    m_quote = None
    m_quotebegin = None

    strlist = []

    i = 0
    while i < len(expr):

        if expr[i] in '\'\"':
            if m_quote is None:
                m_quote = expr[i]
                m_quotebegin = i

            elif expr[i-1] != '\\' and m_quote == expr[i]:
                strlist.append(expr[m_quotebegin:i+1])
                expr = expr[:m_quotebegin] + '__str%d' % (len(strlist)-1) + expr[i+1:]
                i = m_quotebegin-1
                m_quote = None

        elif m_quote is None:
            if expr[i] in '([{':
                m_bracket.append(expr[i])
            elif expr[i] in ')]}':
                if len(m_bracket) > 0 and ((
                    expr[i] == ')' and m_bracket[-1] == '(') or expr[i] == ']' and m_bracket[-1] == '[' or expr[i] == '}' and m_bracket[-1] == '{'):
                    m_bracket.pop()
                else:
                    raise LineParseError('Bracket not match near "%s"' % expr[i-3:i+3])
        i += 1
            
    if len(m_bracket) > 0:
        raise LineParseError('Bracket not match near "%s"' % expr[i-5:])
    elif m_quote is not None:
        raise LineParseError('Quote not match')

    expr = _VAR_EXPR.sub(lambda x: variable_prefix + x.group()[1:], expr)
    expr = _SPECIAL_BRACKET.sub(lambda x: _SPECIAL_BRACKET_MAPPER[x.group()], expr)

    if omit_dollar:
        expr = _TOKEN_EXPR.sub(lambda x: variable_prefix + x.group(), expr)

    else:
        varwithoutdollar = _TOKEN_EXPR.search(expr)
        if varwithoutdollar:
            raise LineParseError('Unrecognized token: "%s"' % varwithoutdollar.group())

    return _INNSTR_EXPR.sub(lambda x:strlist[int(x.group()[5:])], expr)


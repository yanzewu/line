
import re
import logging
import numpy as np
import pandas as pd

from . import sheet_util
from .errors import LineParseError, LineProcessError, print_error

_VAR_EXPR = re.compile(r'\$[_0-9a-zA-Z\*\?\.]+\b')
_TOKEN_EXPR = re.compile(r'\b[_a-zA-Z]([0-9a-zA-Z][_0-9a-zA-Z\.]*)?(?!\()\b')
_INNSTR_EXPR = re.compile(r'\b__str\d+\b')
_INNVAR_EXPR = re.compile(r'\b__var[_0-9a-zA-Z]+\b')


logger = logging.getLogger('line')

class ExprEvaler:

    FUNCTIONS = {
            'sin':np.sin,
            'cos':np.cos,
            'tan':np.tan,
            'cumsum':np.cumsum,
            'exp':np.exp,
            'log':np.log,
            'sinh':np.sinh,
            'cosh':np.cosh,
            'tanh':np.tanh,
            'sqrt':np.sqrt,
            'abs':np.abs,
            'min':np.minimum,
            'max':np.maximum,
            'tp': np.transpose,
            'range':np.arange,
            'linspace':np.linspace,
            'hist': sheet_util.histogram,
            'load': sheet_util.load_file,
            'save': sheet_util.save_file,
            'col':None,
            'hint':None
        }

    def __init__(self, m_globals:dict, m_file_caches:dict):
        self.m_globals = m_globals          # predefined variables
        self.m_file_caches = m_file_caches  # file cache, transparent for outside
        self.m_locals = {}                  # runtime evaluated variables

    def load(self, expr, omit_dollar=False):
        self.expr = canonicalize(expr, omit_dollar)
        logger.debug(self.expr)

    def load_singlevar(self, expr):
        if expr.startswith('\'') or expr.endswith('"'):
            self.expr = '__var' + expr[1:-1]
        elif expr.startswith('$'):
            self.expr = '__var' + expr[1:]
        else:
            self.expr = '__var' + expr
        logger.debug(self.expr)

    def evaluate(self):
        """ Evaluate expression; Return an array-like object.
        """
        for v in _INNVAR_EXPR.findall(self.expr):
            if v not in self.m_globals and v not in self.m_file_caches:
                try:
                    self.m_file_caches[v] = sheet_util.load_file(self.strip_var(v))
                except IOError:
                    raise LineProcessError('Undefined variable: "%s"' % v)
        return self._eval()

    def evaluate_singlevar(self):
        v = self.expr
        if v in self.m_globals:
            return self.m_globals[v]
        elif v in self.m_file_caches:
            return self.m_file_caches[v]
        else:
            try:
                self.m_file_caches[v] = sheet_util.load_file(self.strip_var(v))
                return self.m_file_caches[v]
            except IOError:
                raise LineProcessError('Undefined variable: "%s"' % self.strip_var(v))

    def evaluate_with_hintvar(self, hintvar=None):
        """ Evaluate expression, try interpret undefined variable as column
        label of hintvar.
        """
        if hintvar is not None:
            evaler = ExprEvaler(self.m_globals, self.m_file_caches)
            evaler.load_singlevar(hintvar)
            self.hintvalue = evaler.evaluate_singlevar()
        else:
            self.hintvalue = None

        self.m_locals['col'] = lambda x: sheet_util.loc_col_str(self.hintvalue, x) if isinstance(x, str) \
            else sheet_util.loc_col(self.hintvalue, x)
        self.m_locals['hint'] = lambda: self.hintvalue
      
        for v in _INNVAR_EXPR.findall(self.expr):
            if v not in self.m_globals and v not in self.m_file_caches:
                try:
                    self.m_file_caches[v] = sheet_util.load_file(self.strip_var(v))
                except IOError:
                    try:
                        self.m_locals[v] = sheet_util.loc_col_str(self.hintvalue, self.strip_var(v))
                    except IndexError:
                        if self.strip_var(v).isdigit():
                            raise LineProcessError('Index out of bounds: %s' % self.strip_var(v))
                        else:
                            raise LineProcessError('Undefined variable: "%s"' % self.strip_var(v))
        return self._eval()

    def _eval(self):
        _m_globals = self.FUNCTIONS.copy()
        _m_globals.update(self.m_file_caches)
        _m_globals.update(self.m_globals)
        return eval(self.expr, _m_globals, self.m_locals)

    def strip_var(self, varname):
        return varname[5:]
        
        
def canonicalize(expr:str, omit_dollar=False):
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
            if expr[i] in '([':
                m_bracket.append(expr[i])
            elif expr[i] in ')]':
                if len(m_bracket) > 0 and ((expr[i] == ')' and m_bracket[-1] == '(') or expr[i] == ']' and m_bracket[-1] == '['):
                    m_bracket.pop()
                else:
                    raise LineParseError('Bracket not match near "%s"' % expr[i-3:i+3])
        i += 1
            
    if len(m_bracket) > 0:
        raise LineParseError('Bracket not match near "%s"' % expr[i-5:])
    elif m_quote is not None:
        raise LineParseError('Quote not match')

    expr = _VAR_EXPR.sub(lambda x:'__var' + x.group()[1:], expr)

    if omit_dollar:
        expr = _TOKEN_EXPR.sub(lambda x: '__var' + x.group(), expr)

    else:
        varwithoutdollar = _TOKEN_EXPR.search(expr)
        if varwithoutdollar:
            raise LineParseError('Unrecognized token: "%s"' % varwithoutdollar.group())

    return _INNSTR_EXPR.sub(lambda x:strlist[int(x.group()[5:])], expr)


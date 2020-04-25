""" Util functions for parsing.
"""

import logging
logger = logging.getLogger('line')

from .errors import LineParseError

STOB = {'true':True, 'false':False, 'none':None}

def get_token(m_tokens):
    try:
        x = m_tokens.popleft()
    except IndexError:
        raise LineParseError("Incomplete command")
    else:
        return strip_quote(x)

def get_token_raw(m_tokens):
    try:
        return m_tokens.popleft()
    except IndexError:
        raise LineParseError("Incomplete command")

def strip_quote(token):
    return token[1:-1] if token[0] in '\'\"' else token

def assert_no_token(m_tokens):
    if len(m_tokens) != 0:
        raise LineParseError('Extra tokens: "%s"' % m_tokens[0])

def assert_token(token, expected):
    if token != expected:
        raise LineParseError('"%s" expected' % expected)

def make_assert_token(expected):
    return (lambda x: assert_token(x, expected))

def lookup(m_tokens, idx=0, ret_string=False):
    """ Exception-free look up the next token in advance.
    idx: number of token ahead;
    ret_string: Return empty string if out of bound; By default returns None.
    """
    return strip_quote(m_tokens[idx]) if len(m_tokens) > idx else ('' if ret_string else None)

def lookup_raw(m_tokens, idx=0, ret_string=False):

    return m_tokens[idx] if len(m_tokens) > idx else ('' if ret_string else None)

def test_token_inc(m_tokens, expr):

    do_inc = False
    if len(m_tokens) > 0:
        if callable(expr):
            do_inc = expr(lookup(m_tokens))
        elif isinstance(expr, tuple) or isinstance(expr, list):
            do_inc = lookup(m_tokens) in expr
        else:
            do_inc = (lookup(m_tokens) == expr)
    if do_inc:
        m_tokens.popleft()
    return do_inc
    

def skip_tokens(m_tokens, termflag):
    """ Skip tokens until the end or termflag is meet (included)
    """
    while len(m_tokens) > 0:
        if get_token(m_tokens) == termflag:
            break

def zipeval(functions, m_tokens):
    """ [f(t) for f, t in zip(functions, m_tokens)]
    raise error if len(m_tokens) < len(functions)
    tokens will be poped by len(functions)
    """
    r = []
    for f in functions:
        r.append(f(get_token(m_tokens)))
    return r


def stod(token):

    try:
        return int(token)
    except ValueError:
        raise LineParseError('Integer required')

def stof(token):

    try:
        return float(token)
    except ValueError:
        raise LineParseError('Number required')

def stob(token):
    try:
        return STOB[token]
    except KeyError:
        raise LineParseError("true/false required")

def parse_token_with_comma(m_tokens):
    """ Parse consecutive tokens separated by ",", return the list.
    """
    tokenlist = []
    while len(m_tokens) > 0:
        tokenlist.append(get_token(m_tokens))
        if lookup(m_tokens) == ',':
            get_token(m_tokens)
        else:
            break
    return tokenlist


def parse_column(m_tokens):
    """ Return a string containing column descriptor
    """
    if '(' in m_tokens[0]:
        column_expr = ''
        m_bracket = 0
        while True:
            new_token = get_token_raw(m_tokens)
            for i in range(len(new_token)):
                if new_token[i] == '(':
                    m_bracket += 1
                elif new_token[i] == ')':
                    m_bracket -= 1
                    if m_bracket == 0:
                        column_expr += new_token[:i+1]
                        if i != len(new_token)-1:
                            m_tokens.appendleft(new_token[i+1:])
                        break
            if m_bracket == 0:
                break
            else:
                column_expr += new_token
            
    elif m_tokens[0][0] == '$':
        column_expr = get_token_raw(m_tokens)
        if lookup(m_tokens) in ('+', '-', '*', '/', '^', '==', '!=', '&', '|', '**'):
            column_expr += get_token_raw(m_tokens) + parse_column(m_tokens)

    else:
        column_expr = get_token_raw(m_tokens)

    logger.debug('Column string parsed: %s' % column_expr)
    return column_expr

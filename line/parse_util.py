""" Util functions for parsing.
"""

from .errors import LineParseError

STOB = {'true':True, 'false':False, 'none':None}

def get_token(m_tokens):
    try:
        return m_tokens.popleft()
    except IndexError:
        raise LineParseError("Incomplete command")


def assert_no_token(m_tokens):
    if len(m_tokens) != 0:
        raise LineParseError('Extra tokens: "%s"' % m_tokens[0])

def assert_token(token, expected):
    if token != expected:
        raise LineParseError('"%s" expected' % expected)

def lookup(m_tokens, idx=0):

    return m_tokens[idx] if len(m_tokens) > idx else None

def lookup_rev(m_tokens, idx=0):
    return m_tokens[idx] if len(m_tokens) > idx else ''


def skip_tokens(m_tokens, termflag):
    """ Skip tokens until the end or termflag is meet (included)
    """
    while len(m_tokens) > 0:
        if get_token(m_tokens) == termflag:
            break

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

def is_num(token):
    try:
        float(token)
        return True
    except ValueError:
        return False

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


def parse_range(token):
    """ Parse the range start:step:stop / start:stop into tuple (start, stop, step)
    """
    ssplit = token.split(':')
    start = stof(ssplit[0]) if ssplit[0] else None
    if len(ssplit) == 3:
        step = stof(ssplit[1]) if ssplit[1] else 1
    else:
        step = 1
    stop = stof(ssplit[-1]) if ssplit[-1] else None

    return start, stop, step

def parse_general(token:str):
    """ Parse general token into python objects.
    """
    if ',' in token:
        return [parse_general(t) for t in token.split(',')]
    elif ':' in token:
        return parse_range(token)

    else:
        try:
            return STOB[token]
        except KeyError:
            pass
        
        if '.' in token or 'e' in token:
            try:
                return float(token)
            except ValueError:
                return token
        try:
            return int(token)
        except ValueError:
            return token


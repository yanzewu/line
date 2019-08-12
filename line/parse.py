""" Additional parsing functions
"""

import logging

from . import style
from . import keywords

from .errors import LineParseError, LineProcessError, warn
from .parse_util import *

logger = logging.getLogger('line')


def parse_column(m_tokens):
    """ Return a string containing column descriptor
    """
    if m_tokens[0][0] == '(':
        column_expr = get_token(m_tokens)
        while column_expr[-1] != ')':
            new_token = get_token(m_tokens)
            if new_token in ':,=\"\'':
                raise LineParseError('Bracket not match')
            column_expr += new_token
            
    elif m_tokens[0][0] == '$':
        column_expr = get_token(m_tokens)
        while (len(m_tokens) > 0 and m_tokens[0] not in ':,\"\'') and \
            (len(m_tokens) < 2 or m_tokens[1] != '='):
            
            column_expr += get_token(m_tokens)

    else:
        column_expr = get_token(m_tokens)

    logger.debug('Column string parsed: %s' % column_expr)
    return column_expr


def parse_style(m_tokens, termflag='', require_equal=False, recog_comma=True, recog_colon=True):
    """ Parse style tokens.
    Args:
        termflag: Terminate parsing by flag.
    Returns:
        m_styles: dict of stylename:stylevalue
    """
    m_styles = {}

    while len(m_tokens) > 0 and m_tokens[0] not in termflag:
        style_name, style_val_real = parse_single_style(m_tokens, require_equal, recog_comma, recog_colon)
        if not style_name:
            continue
        m_styles[style_name] = style_val_real

    logger.debug('Style parsed: %s' % m_styles)
    return m_styles


def parse_single_style(m_tokens, require_equal=False, recog_comma=True, recog_colon=True):
    """ Parse consecutive style descriptor 'style=val'
    Args:
        require_equal: If '=' must be present.
        recog_comma: Treat a,b,c as multivalued style parameter when possible.
        recog_colon: Treat a:b:c as multivalued style parameter when possible.
    """

    style_name = get_token(m_tokens)
    style_val = get_token(m_tokens)
    if style_val == '=':
        style_val = get_token(m_tokens)
    elif require_equal:
        raise LineParseError('\"=\" required')

    while len(m_tokens) > 0:
        if m_tokens[0] == ',' and recog_comma:
            style_val += get_token(m_tokens)
            style_val += get_token(m_tokens)
        elif m_tokens[0] == ':' and recog_colon:
            style_val += get_token(m_tokens)
            style_val += get_token(m_tokens)
        else:
            break
    
    # validity of style
    style_name = keywords.style_alias.get(style_name, style_name)
    if style_name not in keywords.style_keywords:
        warn('Skipping invalid style: %s' % style_name)
        return None, None

    try:
        style_val_real = translate_style_val(style_name, style_val)
    except (LineParseError, KeyError, ValueError):
        warn('Skipping invalid style parameter for %s: %s' % (style_name, style_val))
        return None, None
    else:
        return style_name, style_val_real


def parse_group(group:str):

    order = _text_order(group.replace('...', ''))

    if '...' in group:
        prefix, suffix = group.split('...')
        i = len(prefix)-1
        repeator = prefix[i]
        while i > len(prefix)//2:
            if prefix[2*i - len(prefix):i] == prefix[i:]:
                repeator = prefix[i:]
            i -= 1
        prefix = prefix[:len(prefix)-len(repeator)]

        return ([order[t] for t in prefix], [order[t] for t in repeator], [order[t] for t in suffix])

    else:
        return ([order[t] for t in group], None, [])        


def _text_order(text):
    order = {}
    for i, t in enumerate(text):
        order.setdefault(t, i)
    return order


def translate_style_val(style_name:str, style_val:str):
    """ Parse style value depends on name
    """
    # Already agreed with document.

    if style_name.endswith('color'):
        return style.str2color(style_val)
    
    elif style_name == 'linetype':
        try:
            return style.LineType(style.LineTypeStr.index(style_val))
        except ValueError:
            return style.LineType[style_val.upper()]
        
    elif style_name == 'pointtype':
        try:
            return style.PointType(style.PointTypeStr.index(style_val))
        except ValueError:
            return style.PointType[style_val.upper()]

    elif style_name == 'font':
        fontname, fontsize = style_val.split(',')
        return fontname, stod(fontsize)

    elif style_name == 'orient':
        if style_val not in ('in', 'out'):
            raise LineParseError('Invalid orient style: %s' % style_val)
        return style_val

    elif style_name == 'pos':
        try:
            return style.Str2Pos[style_name]
        except KeyError:
            v1, v2 = style_val.split(',')
            return stof(v1), stof(v2)    

    elif style_name == 'size':
        v1, v2 = style_val.split(',')
        return stod(v1), stod(v2)

    # require multiple num value
    elif style_name in ('rsize', 'rpos', 'spacing'):
        v1, v2 = style_val.split(',')
        return stof(v1), stof(v2)

    elif style_name in ('margin', 'padding'):
        vs = style_val.split(',')
        return [stof(vs[i]) for i in range(4)]

    # range
    elif style_name.endswith('range'):
        return parse_range(style_val)

    # bool
    elif style_name == 'visible':
        return STOB[style_name]

    # int
    elif style_name in ('fontsize', 'skippoint', 'zindex', 'dpi'):
        return stod(style_val)

    # float
    elif style_name in ('hspacing', 'vspacing', 'pointsize', 'linewidth', 'alpha') or \
        style_name.startswith('margin-') or style_name.startswith('padding-'):
        return stof(style_val)

    # require str only
    elif style_name in ('text', 'title', 'label', 'xlabel', 'ylabel', 'format', 
        'tick', 'xtick', 'ytick', 'fontfamily', 'palette', 'coord'):
        return style_val

    # general    
    else:
        return parse_general(style_val)


def translate_option_val(option:str, value:str):
    
    if option == 'data-delimiter':
        return value
    elif option == 'data-title':
        if value == 'auto':
            return value

    try:
        return STOB[value]
    except KeyError:
        raise errors.LineParseError('true/false requried for option %s, got %s' % (option, value))


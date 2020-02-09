""" Additional parsing functions
"""

import logging

from . import style
from .style import css, translate_style_val
from . import keywords

from .errors import LineParseError, warn, print_as_warning
from .parse_util import *

logger = logging.getLogger('line')


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
        while lookup(m_tokens) in ('+', '-', '*', '/', '^', '==', '!=', '&', '|', '**'):
            column_expr += get_token_raw(m_tokens) + get_token_raw(m_tokens)

    else:
        column_expr = get_token_raw(m_tokens)

    logger.debug('Column string parsed: %s' % column_expr)
    return column_expr


def parse_style_selector(m_tokens):
    tokenlist = parse_token_with_comma(m_tokens)
    return [parse_single_style_selector(t) for t in tokenlist]
    

def parse_single_style_selector(t):

    if ':' in t:
        typename, attr = t.split(':', 1)
        name, val = attr.split('=')
        return css.TypeStyleSelector(t, name, translate_style_val(name, val))
    elif '=' in t:
        name, val = attr.split('=')
        return css.StyleSelector(name, translate_style_val(name, val))
    elif '.' in t[1:]:
        if t[0] != '.':
            raise LineParseError('Line does not support type-type selection')
        _first, _second = t[1:].split('.', 1)
        if _second in keywords.element_keywords:
            return css.ClassTypeSelector(_first, _second)
        else:
            return css.ClassNameSelector(_first, _second)
    elif t[0] == '.':
        return css.ClassSelector(t[1:])
    else:
        if t in keywords.element_keywords:
            return css.TypeSelector(t)
        else:
            return css.NameSelector(t)
        

def parse_style(m_tokens, termflag='', require_equal=False, recog_comma=True, recog_colon=True, recog_class=False, raise_error=False):
    """ Parse style tokens.
    Args:
        termflag: Terminate parsing by flag.
    Returns:
        m_styles: dict of stylename:stylevalue
        class_add: classname to be added;
        class_remove: classname to be removed;
    """
    m_styles = {}

    class_add = []
    class_remove = []

    while lookup(m_tokens, 0, True) not in termflag:
        if recog_class:
            if m_tokens[0].startswith('+') and m_tokens[0] != '+':
                class_add.append(get_token(m_tokens)[1:])
                continue
            elif m_tokens[0].startswith('-') and m_tokens[0] != '-':
                class_remove.append(get_token(m_tokens)[1:])
                continue
            
        # try parsing style descriptor
        if (lookup_raw(m_tokens).startswith('\'') or not keywords.is_style_keyword(lookup(m_tokens))) and \
            keywords.is_style_desc(lookup(m_tokens)):
            style_desc = get_token(m_tokens)
            try:
                lc, lt, pt = parse_style_descriptor(style_desc)
            except (IndexError, KeyError, ValueError):
                if raise_error:
                    raise LineParseError('Invalid style descriptor: "%s"' % style_desc)
                else:
                    warn('Skip invalid style descriptor "%s"' % style_desc)
            else:
                m_styles.update(build_line_style(lc, lt, pt))
        else:
            style_name, style_val_real = parse_single_style(m_tokens, require_equal, recog_comma, recog_colon, raise_error)
            if style_name:
                m_styles[style_name] = style_val_real

    if recog_class:
        logger.debug('Style parsed: %s; Class parsed: +%s -%s' % (m_styles, class_add, class_remove))
        return m_styles, class_add, class_remove
    else:
        logger.debug('Style parsed: %s' % m_styles)
        return m_styles


def parse_single_style(m_tokens, require_equal=False, recog_comma=True, recog_colon=True, raise_error=False):
    """ Parse consecutive style descriptor 'style=val'
    Args:
        require_equal: If '=' must be present.
        recog_comma: Treat a,b,c as multivalued style parameter when possible.
        recog_colon: Treat a:b:c as multivalued style parameter when possible.
    """

    style_name = get_token(m_tokens)
    if style_name == 'on':
        return 'visible', True
    elif style_name == 'off':
        return 'visible', False

    style_name = keywords.style_alias.get(style_name, style_name)
    is_invalid = style_name not in keywords.style_keywords
    if is_invalid and raise_error:
        raise LineParseError('Invalid style "%s"' % style_name)
        
    style_val = get_token(m_tokens)
    if style_val == '=':
        style_val = get_token(m_tokens)
    elif require_equal:
        raise LineParseError('\"=\" required')

    while len(m_tokens) > 0:
        if lookup(m_tokens) == ',' and recog_comma:
            style_val += get_token(m_tokens) + get_token(m_tokens)
        elif lookup(m_tokens) == ':' and recog_colon:
            style_val += get_token(m_tokens) + get_token(m_tokens)
        else:
            break
    
    # validity of style
    if is_invalid:
        warn('Skip invalid style "%s"' % style_name)
        return None, None

    try:
        style_val_real = translate_style_val(style_name, style_val)
    except (LineParseError, KeyError, ValueError) as e:
        if raise_error:
            raise LineParseError('Invalid style parameter for "%s": %s' % (style_name, style_val))
        else:
            print_as_warning(e)
            warn('Skip invalid style parameter for "%s": %s' % (style_name, style_val))
            return None, None
    else:
        return style_name, style_val_real


def parse_style_descriptor(text:str):
    """ Parse matlab-style descriptor (e.g. "rx-") into
    (color, linestyle, pointstyle) tuple.
    """

    color = None
    linestyle = None
    pointstyle = None

    while len(text) > 0:

        if text[0] in style.ShortColorStr:
            color = style.ShortColorAlias[text[0]]
            text = text[1:]
        elif text[0] in style.PointTypeStr:
            pointstyle = style.PointType(style.PointTypeStr.index(text[0]))
            text = text[1:]
        elif text[0] == '-':
            if lookup(text, 1) in ('-', '.'):
                linestyle = style.LineType(style.LineTypeStr.index(text[0] + text[1]))
                text = text[2:]
            else:
                linestyle = style.LineType(style.LineTypeStr.index(text[0]))
                text = text[1:]
        elif text[0] == ':':
            linestyle = style.LineType(style.LineTypeStr.index(text[0]))
            text = text[1:]
        else:
            raise ValueError(text[0])

    return color, linestyle, pointstyle


def build_line_style(linecolor, linestyle, pointstyle):
    """ Return of parse_style_descriptor => style dict
    """
    ret = {}
    if linecolor is not None:
        ret['linecolor'] = style.str2color(linecolor)
    if linestyle is not None:
        ret['linetype'] = linestyle
        if pointstyle is None:
            ret['pointtype'] = style.PointType.NONE
    if pointstyle is not None:
        ret['pointtype'] = pointstyle
        if linecolor is not None:
            ret['edgecolor'] = style.str2color(linecolor)
            ret['fillcolor'] = style.str2color(style.LighterColor.get(linecolor,linecolor))
        if linestyle is None:
            ret['linetype'] = style.LineType.NONE
        else:
            ret['linewidth'] = 1
    return ret


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

        is_direct_repeat = True
        if len(repeator) == 1:
            i = len(prefix)-1
            r1 = 0
            r2 = 0
            while i > 0:
                if prefix[i-1] == prefix[i]:
                    pass
                elif r1 == 0:
                    r1 = len(prefix) - i
                elif r2 == 0:
                    r2 = len(prefix) - i - r1
                    break
                i -= 1
            if r1 == r2 and r1 > 1:
                is_direct_repeat = False
                repeator = prefix[len(prefix)-r1:]
            print(r1, r2)

        if is_direct_repeat:
            prefix = prefix[:len(prefix)-len(repeator)]

        return ([order[t] for t in prefix], [order[t] for t in repeator], [order[t] for t in suffix], is_direct_repeat)

    else:
        return ([order[t] for t in group], [], [], True)


def _text_order(text):
    order = {'0':0}
    i = 1
    for t in text:
        if t not in order:
            order[t] = i
            i += 1
    return order

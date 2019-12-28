""" Additional parsing functions
"""

import logging

from . import style
from . import style_man
from . import keywords

from .errors import LineParseError, LineProcessError, warn, print_as_warning
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
            column_expr += get_token_raw(m_tokens)
            column_expr += get_token_raw(m_tokens)

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
        return style_man.TypeStyleSelector(t, name, translate_style_val(name, val))
    elif '=' in t:
        name, val = attr.split('=')
        return style_man.StyleSelector(name, translate_style_val(name, val))
    elif '.' in t[1:]:
        if t[0] != '.':
            raise LineParseError('Line does not support type-type selection')
        _first, _second = t[1:].split('.', 1)
        if _second in keywords.element_keywords:
            return style_man.ClassTypeSelector(_first, _second)
        else:
            return style_man.ClassNameSelector(_first, _second)
    elif t[0] == '.':
        return style_man.ClassSelector(t[1:])
    else:
        if t in keywords.element_keywords:
            return style_man.TypeSelector(t)
        else:
            return style_man.NameSelector(t)
        

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
    if style_name not in keywords.style_keywords:
        if raise_error:
            raise LineParseError('Invalid style "%s"' % style_name)
        else:
            is_invalid = True
    else:
        is_invalid = False
        
    style_val = get_token(m_tokens)
    if style_val == '=':
        style_val = get_token(m_tokens)
    elif require_equal:
        raise LineParseError('\"=\" required')

    while len(m_tokens) > 0:
        if lookup(m_tokens) == ',' and recog_comma:
            style_val += get_token(m_tokens)
            style_val += get_token(m_tokens)
        elif lookup(m_tokens) == ':' and recog_colon:
            style_val += get_token(m_tokens)
            style_val += get_token(m_tokens)
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
            raise LineProcessError('Invalid style parameter for "%s": %s' % (style_name, style_val))
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
        prefix = prefix[:len(prefix)-len(repeator)]

        return ([order[t] for t in prefix], [order[t] for t in repeator], [order[t] for t in suffix])

    else:
        return ([order[t] for t in group], [], [])


def _text_order(text):
    order = {'0':0}
    i = 1
    for t in text:
        if t not in order:
            order[t] = i
            i += 1
    return order


def translate_style_val(style_name:str, style_val:str):
    """ Parse style value depends on name
    """
    # Already agreed with document.

    if style_val == 'inherit' and keywords.is_inheritable(style_name):
        return style_man.SpecialStyleValue.INHERIT
    elif style_val == 'default' and keywords.is_copyable(style_name):
        return style_man.SpecialStyleValue.DEFAULT

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
            raise LineParseError('Invalid orient style "%s"' % style_val)
        return style_val

    elif style_name == 'hold':
        if style_val == 'on':
            return True
        elif style_val == 'off':
            return False
        else:
            return stob(style_val)

    elif style_name == 'pos':
        try:
            return style.Str2Pos[style_val]
        except KeyError:
            v1, v2 = style_val.split(',')
            return stof(v1), stof(v2)    

    elif style_name == 'size':
        v1, v2 = style_val.split(',')
        return stod(v1), stod(v2)

    elif style_name == 'dpi':
        if style_val in ('high', 'mid', 'low'):
            return style_val
        else:
            return stod(style_val)

    elif style_name in ('scale', 'xscale', 'yscale'):
        if style_val not in ('linear', 'log'):
            raise LineParseError('Invalid scale "%s"' % style_val)
        return style_val

    # require multiple num value
    elif style_name in ('rsize', 'rpos', 'spacing'):
        v1, v2 = style_val.split(',')
        return stof(v1), stof(v2)

    elif style_name in ('margin', 'padding'):
        vs = style_val.split(',')
        return [stof(vs[i]) for i in range(4)]

    # range
    elif style_name.endswith('range'):
        return style_val if style_val == 'auto' else parse_range(style_val)

    # bool
    elif style_name == 'visible':
        return stob(style_val)

    # int
    elif style_name in ('fontsize', 'skippoint', 'zindex'):
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
        raise LineParseError('true/false requried for option "%s", got "%s"' % (option, value))


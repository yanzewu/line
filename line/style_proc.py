""" Additional parsing functions
"""

import logging

from . import style
from .style import css, translate_style_val
from . import keywords

from .errors import LineParseError, warn, print_as_warning
from .parse_util import *

logger = logging.getLogger('line')


def parse_selection_and_style_with_default(m_tokens, default_selection, **kwargs):
    
    if keywords.is_style_keyword(lookup(m_tokens)) and lookup(m_tokens, 1) != 'clear' and \
        lookup(m_tokens, 1) != ',' and (
        not keywords.is_style_keyword(lookup(m_tokens, 1)) or 
        (lookup(m_tokens, 1) not in ('on', 'off') and len(m_tokens) <= 2)):
        # the nasty cases... either not a style keyword or not enough style parameters
        # that treated as value

        selection = default_selection
    else:
        selection = parse_style_selector(m_tokens)

    if lookup(m_tokens) == 'clear':
        get_token(m_tokens)
        assert_no_token(m_tokens)
        style_list = css.ResetStyle()
        add_class = []
        remove_class = []
    else:
        style_list, add_class, remove_class = parse_style(m_tokens, recog_class=True, **kwargs)

    return selection, style_list, add_class, remove_class
    

def parse_style_selector(m_tokens):

    tokenlist = []
    while len(m_tokens) > 0:
        v1 = get_token(m_tokens)
        if test_token_inc(m_tokens, '='):
            tokenlist.append('%s=%s' % (v1, get_token(m_tokens)))
        elif test_token_inc(m_tokens, ':'):
            v2 = get_token(m_tokens)
            if test_token_inc(m_tokens, '='):
                tokenlist.append('%s:%s=%s' % (v1, v2, get_token(m_tokens)))
        else:
            tokenlist.append(v1)
        
        if not test_token_inc(m_tokens, ','):
            break

    return [parse_single_style_selector(t) for t in tokenlist]
    

def parse_single_style_selector(t):

    if ':' in t:
        typename, attr = t.split(':', 1)
        name, val = attr.split('=')
        name = keywords.style_alias.get(name, name)
        return css.TypeStyleSelector(typename, name, translate_style_val(name, val))
    elif '=' in t:
        name, val = t.split('=')
        name = keywords.style_alias.get(name, name)
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
        

def parse_style(m_tokens, termflag='', require_equal=False, recog_comma=True, recog_colon=True, recog_class=False, recog_expression=False, raise_error=False):
    """ Parse style tokens.
    Args:
        termflag: Terminate parsing by flag.
        require_equal: If '=' must be present.
        recog_comma: Treat a,b,c as multivalued style parameter when possible.
        recog_colon: Treat a:b:c as multivalued style parameter when possible.
        recog_expression: If the style value starts with '$(', return the value without parsing.
        raise_error: Raise error if needed;
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
            style_name, style_val_real = parse_single_style(m_tokens, require_equal, recog_comma, recog_colon, recog_expression, raise_error)
            if style_name:
                m_styles[style_name] = style_val_real

    if recog_class:
        logger.debug('Style parsed: %s; Class parsed: +%s -%s' % (m_styles, class_add, class_remove))
        return m_styles, class_add, class_remove
    else:
        logger.debug('Style parsed: %s' % m_styles)
        return m_styles


def parse_single_style(m_tokens, require_equal=False, recog_comma=True, recog_colon=True, recog_expression=False, raise_error=False):
    """ Parse consecutive style descriptor 'style=val'
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

    if recog_expression and style_val.startswith('$('):
        return style_name, style_val

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


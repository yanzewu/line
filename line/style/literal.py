
from ..keywords import style_keywords, inheritable_styles, clustered_styles
from ..parse_util import *
from ..option_util import parse_general, parse_range

from . import css
from . import style


def is_inheritable_style(token):
    return token in inheritable_styles

def is_copyable_style(token):
    return token in style_keywords

def is_clustered_style(token):
    """ style that is a group of several individual keys (or indices)
    """
    return token in clustered_styles

def translate_style_val(style_name:str, style_val:str):
    """ Parse style value depends on name
    """
    # Already agreed with document.

    if style_val == 'inherit' and is_inheritable_style(style_name):
        return css.SpecialStyleValue.INHERIT
    elif style_val == 'default' and is_copyable_style(style_name):
        return css.SpecialStyleValue.DEFAULT

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

    elif style_name == 'fontprops':
        try:
            return style.FontProperty(*style_val.split(','))
        except ValueError as e:
            raise LineParseError(str(e))

    elif style_name == 'orient':
        if style_val not in ('in', 'out', 'horizontal', 'vertical'):
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
            return style.str2pos(style_val)
        except ValueError as e:
            raise LineParseError(str(e))

    elif style_name == 'side':
        try:
            s = style.str2pos(style_val)
            if not isinstance(s, tuple) or not isinstance(s[0], style.FloatingPos) \
                or not isinstance(s[1], style.FloatingPos):
                raise LineParseError('Invalid side: "%s"' % style_val)
            return s
        except ValueError as e:
            raise LineParseError(str(e))

    elif style_name == 'size':
        v1, v2 = style_val.split(',')
        return [stod(v1), stod(v2)]

    elif style_name == 'dpi':
        if style_val in ('high', 'mid', 'low'):
            return style_val
        else:
            return stod(style_val)

    elif style_name in ('scale', 'xscale', 'yscale'):
        if style_val not in ('linear', 'log'):
            raise LineParseError('Invalid scale "%s"' % style_val)
        return style_val

    elif style_name == 'fillstyle':
        if style_val not in ('none', 'full'):
            raise LineParseError('Invalid fill style "%s"' % style_val)
        return style_val

    # require multiple num value
    elif style_name in ('rsize', 'rpos', 'spacing'):
        v1, v2 = style_val.split(',')
        return [stof(v1), stof(v2)]

    elif style_name in ('margin', 'padding'):
        vs = style_val.split(',')
        return style.Padding(*(stof(vs_) for vs_ in vs))

    # range
    elif style_name.endswith('range'):
        return (None,None,None) if style_val == 'auto' else parse_range(style_val)

    # bool
    elif style_name == 'visible':
        return stob(style_val)

    # int
    elif style_name in ('skippoint', 'zindex'):
        return stod(style_val)

    # float
    elif style_name in ('hspacing', 'vspacing', 'pointsize', 'linewidth', 'alpha') or \
        style_name.startswith('margin-') or style_name.startswith('padding-'):
        return stof(style_val)

    # require str only
    elif style_name in ('text', 'title', 'label', 'xlabel', 'ylabel', 'format', 
        'fontfamily', 'palette', 'coord'):
        return style_val

    # general    
    else:
        return parse_general(style_val)


def merge_cluster_styles(style1, style2):
    """Merge both list/Padding/FontProps: If style2[key] is none, use style1[key]. otherwise use style2[key].
    If merge fails, will return the second one."""

    if isinstance(style1, list) and isinstance(style2, (list, tuple)):
        if len(style1) == len(style2):
            return _merge_list(style1, style2)

    elif isinstance(style1, style.Padding) and isinstance(style2, (style.Padding, list, tuple)):
        return style.Padding(*_merge_list(style1, style2))

    elif isinstance(style1, style.FontProperty) and isinstance(style2, (style.FontProperty, dict)):
        s = style.FontProperty()
        for k in style1:
            s[k] = style1[k] if style2[k] is None else style2[k]
        return s

    return style2


def _merge_list(l1:list, l2:list):
    return [l1_ if l2_ is None else l2_ for l1_, l2_ in zip(l1, l2)]

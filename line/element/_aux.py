
""" Factory style setter/getter
"""
from . import css

def _set_color(m_style, value):
    m_style['linecolor'] = value
    m_style['edgecolor'] = value

def _set_data(target, value):
    target.data = value
    target._update_ext()

_get_computed_style = lambda o, n, d: o.computed_style.get(n, d) if o.computed_style else d

def _merge_2_list(name, key, val, styles, default_len):
    if name in styles and not isinstance(styles[name], css.SpecialStyleValue):
        c = styles[name].copy() # same style groups
          # since sometimes the style might be set in lower priority. Also to prevent inheritance.
    else:
        c = [None] * default_len
    c[key] = val
    return c

def _merge_2_dict(name, key, val, styles, default_keys):
    # NOTE that if two styles are set in the same sheet, and one is 'inherit' it will gets override by the other one.
    # however it is a very rare case since one usually want to inherit all or just one *in the same style sheet*.
    # I will leave this as a feature.
    if name in styles and not isinstance(styles[name], css.SpecialStyleValue):
        c = styles[name].copy() # same style groups
    else:
        c = dict(((k, None) for k in default_keys))
    c[key] = val
    return c

def _gen_fontprops_setter():

    name = 'fontprops'
    default_keys = {'style', 'weight', 'variant', 'stretch', 'size'}
    
    return {
        'fontstyle': lambda s, v: s.update({name:_merge_2_dict(name, 'style', v, s, default_keys)}),
        'fontweight': lambda s, v: s.update({name:_merge_2_dict(name, 'weight', v, s, default_keys)}),
        'fontvariant': lambda s, v: s.update({name:_merge_2_dict(name, 'variant', v, s, default_keys)}),
        'fontstretch': lambda s, v: s.update({name:_merge_2_dict(name, 'stretch', v, s, default_keys)}),
        'fontsize': lambda s, v: s.update({name:_merge_2_dict(name, 'size', v, s, default_keys)}),
    }

def _gen_fontprops_getter(obj):
    return {
        'fontsize': lambda s: _get_computed_style(obj, 'fontprops', None)['size'],
        'fontweight': lambda s: _get_computed_style(obj, 'fontprops', None)['weight'],
        'fontstyle': lambda s: _get_computed_style(obj, 'fontprops', None)['style'],
    }

def _gen_margin_setter():
    name = 'margin'

    return {
        'margin-left': lambda s, v: s.update({name: _merge_2_list(name, 0, v, s, 4)}),
        'margin-bottom': lambda s, v: s.update({name: _merge_2_list(name, 1, v, s, 4)}),
        'margin-right': lambda s, v: s.update({name: _merge_2_list(name, 2, v, s, 4)}),
        'margin-top': lambda s, v: s.update({name: _merge_2_list(name, 3, v, s, 4)}),
    }    
    
def _gen_margin_getter(obj):
    return {
        'margin-left': lambda s: _get_computed_style(obj, 'margin', None)[0],
        'margin-bottom': lambda s: _get_computed_style(obj, 'margin', None)[1],
        'margin-right': lambda s: _get_computed_style(obj, 'margin', None)[2],
        'margin-top': lambda s: _get_computed_style(obj, 'margin', None)[3],
    }

def _gen_padding_setter():
    name = 'padding'

    return {
        'padding-left': lambda s, v: s.update({name: _merge_2_list(name, 0, v, s, 4)}),
        'padding-bottom': lambda s, v: s.update({name: _merge_2_list(name, 1, v, s, 4)}),
        'padding-right': lambda s, v: s.update({name: _merge_2_list(name, 2, v, s, 4)}),
        'padding-top': lambda s, v: s.update({name: _merge_2_list(name, 3, v, s, 4)}),
    }

def _gen_padding_getter(obj):
    return {
        'padding-left': lambda s: _get_computed_style(obj, 'padding', None)[0],
        'padding-bottom': lambda s: _get_computed_style(obj, 'padding', None)[1],
        'padding-right': lambda s: _get_computed_style(obj, 'padding', None)[2],
        'padding-top': lambda s: _get_computed_style(obj, 'padding', None)[3],
    }

def _gen_spacing_setter():
    name = 'spacing'
    return {
        'hspacing': lambda s, v: s.update({name: _merge_2_list(name, 0, v, s, 2)}),
        'vspacing': lambda s, v: s.update({name: _merge_2_list(name, 1, v, s, 2)}),
    }


def _gen_spacing_getter(obj):
    return {
        'hspacing': lambda s: _get_computed_style(obj, 'spacing', None)[0],
        'vspacing': lambda s: _get_computed_style(obj, 'spacing', None)[1],
    }

def _gen_size_setter():
    name = 'size'
    return {
        'width': lambda s, v: lambda s, v: s.update({name: _merge_2_list(name, 0, v, s, 2)}),
        'height': lambda s, v: lambda s, v: s.update({name: _merge_2_list(name, 1, v, s, 2)}),
    }

def _gen_size_getter(obj):
    return {
        'width': lambda s: _get_computed_style(obj, 'size', None)[0],
        'height': lambda s: _get_computed_style(obj, 'size', None)[1],
    }
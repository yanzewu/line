
""" Factory style setter/getter
"""


def _set_color(m_style, value):
    m_style['linecolor'] = value
    m_style['edgecolor'] = value

def _set_data(target, value):
    target.data = value
    target._update_ext()

_get_computed_style = lambda o, n, d: o.computed_style.get(n, d) if o.computed_style else d

def _merge_2(o, d, n, k, v):
    c = _get_computed_style(o, n, d[n]).copy()  # since sometimes the style might be set in lower priority. Also to prevent inheritance.
    c[k] = v
    return c

def _gen_fontprops_setter(obj, default_val):

    name = 'fontprops'
    return {
        'fontstyle': lambda s, v: s.update({name:_merge_2(obj, default_val, name, 'style', v)}),
        'fontweight': lambda s, v: s.update({name:_merge_2(obj, default_val, name, 'weight', v)}),
        'fontvariant': lambda s, v: s.update({name:_merge_2(obj, default_val, name, 'variant', v)}),
        'fontstretch': lambda s, v: s.update({name:_merge_2(obj, default_val, name, 'stretch', v)}),
        'fontsize': lambda s, v: s.update({name:_merge_2(obj, default_val, name, 'size', v)}),
    }

def _gen_fontprops_getter(obj):
    return {
        'fontsize': lambda s: _get_computed_style(obj, 'fontprops', None)['size'],
        'fontweight': lambda s: _get_computed_style(obj, 'fontprops', None)['weight'],
        'fontstyle': lambda s: _get_computed_style(obj, 'fontprops', None)['style'],
    }

def _gen_margin_setter(obj, default_val):
    name = 'margin'

    return {
        'margin-left': lambda s, v: s.update({name:_merge_2(obj, default_val, name, 0, v)}),
        'margin-bottom': lambda s, v: s.update({name:_merge_2(obj, default_val, name, 1, v)}),
        'margin-right': lambda s, v: s.update({name:_merge_2(obj, default_val, name, 2, v)}),
        'margin-top': lambda s, v: s.update({name:_merge_2(obj, default_val, name, 3, v)}),
    }
    
def _gen_margin_getter(obj):
    return {
        'margin-left': lambda s: _get_computed_style(obj, 'margin', None)[0],
        'margin-bottom': lambda s: _get_computed_style(obj, 'margin', None)[1],
        'margin-right': lambda s: _get_computed_style(obj, 'margin', None)[2],
        'margin-top': lambda s: _get_computed_style(obj, 'margin', None)[3],
    }

def _gen_padding_setter(obj, default_val):
    name = 'padding'

    return {
        'padding-left': lambda s, v: s.update({name:_merge_2(obj, default_val, name, 0, v)}),
        'padding-bottom': lambda s, v: s.update({name:_merge_2(obj, default_val, name, 1, v)}),
        'padding-right': lambda s, v: s.update({name:_merge_2(obj, default_val, name, 2, v)}),
        'padding-top': lambda s, v: s.update({name:_merge_2(obj, default_val, name, 3, v)}),
    }

def _gen_padding_getter(obj):
    return {
        'padding-left': lambda s: _get_computed_style(obj, 'padding', None)[0],
        'padding-bottom': lambda s: _get_computed_style(obj, 'padding', None)[1],
        'padding-right': lambda s: _get_computed_style(obj, 'padding', None)[2],
        'padding-top': lambda s: _get_computed_style(obj, 'padding', None)[3],
    }

def _gen_spacing_setter(obj, default_val):
    name = 'spacing'
    return {
        'hspacing': lambda s, v: s.update({name:_merge_2(obj, default_val, name, 0, v)}),
        'vspacing': lambda s, v: s.update({name:_merge_2(obj, default_val, name, 1, v)}),
    }


def _gen_spacing_getter(obj):
    return {
        'hspacing': lambda s: _get_computed_style(obj, 'spacing', None)[0],
        'vspacing': lambda s: _get_computed_style(obj, 'spacing', None)[1],
    }

def _gen_size_setter(obj, default_val):
    name = 'size'
    return {
        'width': lambda s, v: s.update({name:_merge_2(obj, default_val, name, 0, v)}),
        'height': lambda s, v: s.update({name:_merge_2(obj, default_val, name, 1, v)}),
    }

def _gen_size_getter(obj):
    return {
        'width': lambda s: _get_computed_style(obj, 'size', None)[0],
        'height': lambda s: _get_computed_style(obj, 'size', None)[1],
    }
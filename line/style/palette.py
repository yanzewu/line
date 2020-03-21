""" Loading palette and colors.
"""

import numpy as np

from . import style
from . import css


PALETTES = {}


def get_palette(name):
    """ raise KeyError if palette does not exist.
    Returns: palette, a list of (r,g,b) values.
    """
    return PALETTES[name]


def load_palette(fp):
    """ Load palette from json file descriptor. Will override existing 
    items with same name.
    """
    import json
    j = json.load(fp)
    for name in j:
        new_list = []
        for d in j[name]:
            new_list.append(style.str2color(d) if isinstance(d, str) else d)
        j[name] = new_list
        
    PALETTES.update(j)


def load_intrinsic_palette():
    """ Load intrinsic palettes (from matplotlib)
    """
    _load_palette_mpl()
    _load_colors_mpl()


def palette2stylesheet(palette, target=None, target_style='color'):
    """ Return css.StyleSheet object from list of colors.
    """
    ss = css.StyleSheet()
    for idx, color in enumerate(palette):
        if target:
            ss.data[css.TypeStyleSelector(target, 'colorid', idx)] = css.Style(**{target_style: color})
        else:
            ss.data[css.StyleSelector('colorid', idx)] = css.Style(**{target_style: color})
    return ss


def _load_palette_mpl():
    """ Try importing all palettes from Matplotlib.
    """

    from matplotlib import cm

    for name, cmap in cm.cmap_d.items():
        try:
            PALETTES['mpl.' + name] = [(0,0,0)] + list(cmap.colors)
        except AttributeError:
            PALETTES['mpl.' + name] = [(0,0,0)] + [cmap(i) for i in np.arange(0.05, 1.0, 0.15)]


def _load_palette_seaborn():
    """ Try importing all palettes from Seaborn.
    """
    try:
        import seaborn as sns
    except ImportError:
        return

    PALETTES['sns.default'] = [(0,0,0)] + sns.color_palette()
    PALETTES['sns'] = [(0,0,0)] + sns.color_palette()

    for name in ('deep', 'muted', 'bright', 'pastel', 'dark'):
        PALETTES['sns' + name] = [(0,0,0)] + sns.color_palette(name)


def _load_colors_mpl():
    """ Loading color names from Matplotlib.
    """
    from matplotlib import colors
    
    for name, val in colors.TABLEAU_COLORS.items():
        setattr(style.Color, name.replace(':', '-').upper(), colors.to_rgb(val))
    
    for name, val in colors.CSS4_COLORS.items():
        setattr(style.Color, name.upper(), colors.to_rgb(val))

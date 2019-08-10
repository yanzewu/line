""" Loading palatte and colors.
"""

import numpy as np

from . import style

# TODO HIGH Reverse mpl color string

def _load_palette_mpl():
    """ Try importing all palettes from Matplotlib.
    """

    from matplotlib import cm

    for name, cmap in cm.cmap_d.items():
        try:
            style.PALETTES['mpl.' + name] = [(0,0,0)] + list(cmap.colors)
        except AttributeError:
            style.PALETTES['mpl.' + name] = [(0,0,0)] + [cmap(i) for i in np.arange(0.05, 1.0, 0.15)]


def _load_palette_seaborn():
    """ Try importing all palettes from Seaborn.
    """
    try:
        import seaborn as sns
    except ImportError:
        return

    style.PALETTES['sns.default'] = [(0,0,0)] + sns.color_palette()
    style.PALETTES['sns'] = [(0,0,0)] + sns.color_palette()

    for name in ('deep', 'muted', 'bright', 'pastel', 'dark'):
        style.PALETTES['sns' + name] = [(0,0,0)] + sns.color_palette(name)


def _load_palette_line():
    """ Load palettes defined here.
    """
    pass


def _load_colors_mpl():
    """ Loading color names from Matplotlib.
    """
    from matplotlib import colors
    
    for name, val in colors.TABLEAU_COLORS.items():
        setattr(style.Color, name.replace(':', '-').upper(), colors.to_rgb(val))
    
    for name, val in colors.CSS4_COLORS.items():
        setattr(style.Color, name.upper(), colors.to_rgb(val))

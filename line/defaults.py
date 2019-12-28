
""" Initializing default options, styles and palettes.
"""

from . import style_man
from . import palette


default_options = {
    'auto-adjust-range':True,
    'data-title':'auto',
    'data-delimiter':'auto',
    'display-when-quit':False,
    'ignore-data-comment': True,
    'identify-data':False,              # not used now
    'prompt-always':False,
    'prompt-multi-removal':True,
    'prompt-overwrite':True,
    'prompt-save-when-quit':False,
}

default_font = 'CMU Serif'
default_math_font = 'cm'
default_fonts = ['CMU Serif', 'Times New Roman', 'Arial', 'serif']  # font fallback
default_figure_size_inches = [7.2, 4.8]
default_style_entries = {}


def init_global_state(m_state):

    import os.path

    m_state.options = default_options
    style_dir = os.path.join(os.path.dirname(__file__) , 'styles')
    with open(os.path.join(style_dir, 'defaults.css'), 'r') as f:
        m_state.default_stylesheet = style_man.load_css(f)
    with open(os.path.join(style_dir, 'defaults.d.css')) as f:
        m_state.custom_stylesheet = style_man.load_css(f)

    for selector, style in m_state.default_stylesheet.data.items():
        default_style_entries[selector.typename] = set(style)

    with open(os.path.join(style_dir, 'palettes.json')) as f:
        palette.load_palette(f)
        m_state.custom_stylesheet.update(palette.palette2stylesheet(palette.PALETTES['default']))
                

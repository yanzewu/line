
""" Initializing default options, styles and palettes.
"""

from . import style_man
from . import palette


default_options = {
    'auto-adjust-range':True,
    'data-title':'auto',
    'broadcast-style':['linewidth', 'pointsize', 'edgewidth'],
    'data-delimiter':'auto',
    'display-when-quit':False,
    'force-column-selection':False,
    'ignore-data-comment': True,
    'identify-data':False,              # not used now
    'prompt-always':False,
    'prompt-multi-removal':True,
    'prompt-overwrite':True,
    'prompt-save-when-quit':False,
    'remove-element-by-style':False,
    'set-future-line-style':True,
    'set-skip-invalid-selection':True,
}

default_font = 'CMU Serif'
default_math_font = 'cm'
default_fonts = ['CMU Serif', 'Times New Roman', 'Arial', 'serif']  # font fallback

default_style_entries = {}


def init_global_state(m_state):

    import os.path

    m_state.options = default_options
    with open(os.path.join(__file__ , '../styles/defaults.css'), 'r') as f:
        m_state.default_stylesheet = style_man.load_css(f)
    with open(os.path.join(__file__, '../styles/defaults.d.css')) as f:
        m_state.custom_stylesheet = style_man.load_css(f)

    for selector, style in m_state.default_stylesheet.data.items():
        default_style_entries[selector.typename] = set(style)

    with open(os.path.join(__file__, '../styles/palettes.json')) as f:
        palette.load_palette(f)
        m_state.custom_stylesheet.update(palette.palette2stylesheet(palette.PALETTES['default']))
                

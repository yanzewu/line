
""" Initializing default options, styles and palettes.
"""

default_options = {}

default_font = 'CMU Serif'
default_math_font = 'cm'
default_fonts = ['CMU Serif', 'Times New Roman', 'Arial', 'serif']  # font fallback
default_figure_size_inches = [7.2, 4.8]
default_style_entries = {}

def read_default_options(section='DEFAULT'):

    global default_options

    import configparser
    import os.path
    from .parse_util import parse_general

    style_dir = os.path.join(os.path.dirname(__file__) , 'styles')
    config = configparser.ConfigParser()
    config.read(os.path.join(style_dir, 'options.ini'))
    default_options = dict(((k, parse_general(v)) for (k, v) in config[section].items()))
    

def init_global_state(m_state):

    import os.path

    from .style import css
    from .style import palette

    m_state.options = default_options
    style_dir = os.path.join(os.path.dirname(__file__) , 'styles')
    with open(os.path.join(style_dir, 'defaults.css'), 'r') as f:
        m_state.default_stylesheet = css.load_css(f)
    with open(os.path.join(style_dir, 'defaults.d.css')) as f:
        m_state.custom_stylesheet = css.load_css(f)

    for selector, style in m_state.default_stylesheet.data.items():
        default_style_entries[selector.typename] = set(style)

    palette.load_intrinsic_palette()
    with open(os.path.join(style_dir, 'palettes.json')) as f:
        palette.load_palette(f)
        m_state.custom_stylesheet.update(palette.palette2stylesheet(palette.PALETTES['default']))

read_default_options()

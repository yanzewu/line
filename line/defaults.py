
""" Initializing default options, styles and palettes.
"""
import configparser
import os.path

from . import option_util


default_options = {}
default_style_entries = {}
default_style_sheet = None  # we export default CSS here to help elements initialize themselves


def parse_default_options(option_list, option_range=None, raise_error=False):

    return option_util.parse_option_list(option_list, 
        omit_when_valueerror=not raise_error, 
        strict=raise_error,
        option_range=option_range,
        default_handler=option_util.to_bool, 
        custom_handler_dict={
            'data-delimiter': lambda x: x,
            'data-title': lambda x: x if x == 'auto' else option_util.to_bool(x),
            'safety': lambda x: int(x),
        })


def read_default_options():

    global default_options

    style_dir = os.path.join(os.path.dirname(__file__) , 'styles')
    config = configparser.ConfigParser(inline_comment_prefixes='#')
    config.read(os.path.join(style_dir, 'options.ini'))
    default_options = dict(((k, option_util.parse_general(v)) for (k, v) in config['DEFAULT'].items()))
    if 'custom' in config.sections():
        default_options.update(
            parse_default_options(config['custom'].items(), option_range=default_options.keys())
            )
    

def init_global_state(m_state):

    global default_style_sheet

    from .style import css
    from .style import palette

    m_state.options = default_options
    style_dir = os.path.join(os.path.dirname(__file__) , 'styles')
    with open(os.path.join(style_dir, 'defaults.css'), 'r') as f:
        default_style_sheet = css.load_css(f)
        m_state.default_stylesheet = default_style_sheet
    with open(os.path.join(style_dir, 'defaults.d.css')) as f:
        m_state.update_local_stylesheet(css.load_css(f))

    for selector, style in m_state.default_stylesheet.data.items():
        default_style_entries[selector.typename] = set(style)

    palette.load_intrinsic_palette()
    with open(os.path.join(style_dir, 'palettes.json')) as f:
        palette.load_palette(f)
        m_state.custom_stylesheet.update(palette.palette2stylesheet(palette.PALETTES['default']))

read_default_options()

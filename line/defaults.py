
from . import state
from . import errors
from .style import Color, LineType, PointType
from .collection_util import RestrictDict, extract_single
from . import style_man


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

default_figure_style = RestrictDict({
    'size': [0, 0],
    'dpi':200,
    'margin': [0.05, 0.05, 0.05, 0.05],
    'spacing': [0.05, 0.05]
})

default_figure_size_inches = [7.2, 4.8]
default_figure_style['size'] = [
    default_figure_size_inches[0]*default_figure_style['dpi'],
    default_figure_size_inches[1]*default_figure_style['dpi'],
    ]

default_figure_attr = RestrictDict({
    'split': [1,1]
})

default_font = 'CMU Serif'
default_math_font = 'cm'
default_fonts = ['CMU Serif', 'Times New Roman', 'Arial', 'serif']  # font fallback

default_major_axis_style = RestrictDict({
    'linewidth':0.5,
    'linetype':LineType.SOLID,
    'color':Color.BLACK,
    'visible':True,
    'zindex':-1,
    'label':RestrictDict({
        'fontfamily':default_font,
        'fontsize':16,
        'color':Color.BLACK,
        'visible':True,
    }),
    'tick':RestrictDict({
        'fontfamily':default_font,
        'fontsize':14,
        'format':'%.4G',
        'color':Color.BLACK,
        'orient':'in',
        'linewidth':0.5,
        'visible':True
    }),
    'grid':RestrictDict({
        'linewidth': 0.2,
        'linetype':LineType.DOT,
        'linecolor':Color.GREY,
        'visible':False,
        'zindex':-2
    })
})

default_minor_axis_style = RestrictDict({
    'linewidth':0.5,
    'linetype':LineType.SOLID,
    'color':Color.BLACK,
    'visible':True,
    'zindex':-1,
    'label':RestrictDict({
        'fontfamily':default_font,
        'fontsize':16,
        'color':Color.BLACK,
        'visible':False
    }),
    'tick':RestrictDict({
        'fontfamily':default_font,
        'fontsize':14,
        'format':'%.4G',
        'color':Color.BLACK,
        'orient':'in',
        'linewidth':0.5,
        'visible':False
    }),
    'grid':RestrictDict({
        'linewidth': 0.5,
        'linetype':LineType.DASH,
        'linecolor':Color.GREY,
        'visible':False
    })
})

default_axis_attr = RestrictDict({
    'range': (None, None),
    'interval': 0.1
})

default_dataline_style = RestrictDict({
    'linewidth':2,
    'linetype':LineType.SOLID,
    'linecolor':Color.BLACK,    # 'color' sets both line and point
    'pointsize':6,
    'pointtype':PointType.NONE,
    'edgewidth':0.8,
    'edgecolor':Color.BLACK,
    'fillcolor':Color.WHITE,
    'visible':True,
    'zindex':0
})

# Global default drawline style
default_drawline_style = RestrictDict({
    'linewidth':2,
    'linetype':LineType.SOLID,
    'linecolor':Color.BLACK,
    'pointsize':4,
    'pointtype':PointType.NONE,
    'edgewidth':0.8,
    'edgecolor':Color.BLACK,
    'fillcolor':Color.BLACK,
    'visible':True,
    'coord': 'data',
    'zindex':0
})

default_text_style = RestrictDict({
    'fontfamily':default_font,     # 'font' set both family and size
    'fontsize':16,
    'color':Color.BLACK,
    'visible':True,
    'coord': 'axis',
    'zindex':0
})

default_legend_style = RestrictDict({
    'alpha':0,
    'linewidth':0.5,
    'linecolor':Color.BLACK,
    'linetype':LineType.SOLID,
    'fontfamily':default_font,
    'fontsize':16,
    'color':Color.WHITE,
    'visible':True,
    'pos':'best',       # both str and (a,b) is valid
    'zindex':0
})

default_legend_attr = RestrictDict({
    'pos': 'best'
})

default_subfigure_style = RestrictDict({
    'padding': [0.1, 0.1, 0.0, 0.0],
    'palette': 'default',
    'default-dataline': default_dataline_style,
    'default-drawline': default_drawline_style,
    'default-text': default_text_style,
    'title':'',
    'visible':True,
    'xaxis':default_major_axis_style,
    'yaxis':default_major_axis_style,
    'raxis':default_minor_axis_style,
    'taxis':default_minor_axis_style,
    'legend':default_legend_style
})

default_subfigure_attr = RestrictDict({
    'rsize': (1.0, 1.0),
    'rpos': (0.0, 0.0),
    'group': tuple()
})

default_figure_style.data['subfigure0'] = default_subfigure_style


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


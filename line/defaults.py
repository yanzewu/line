
import argparse

from . import state
from . import errors
from .style import Color, LineType, PointType
from .collection_util import RestrictDict

default_options = {
    'force-column-selection':False,
    'ignore-data-comment': True,
    'identify-data':False,              # not used now
    'data-delimiter':'auto',
    'data-title':'auto',
    'prompt-multi-removal':True,
    'remove-element-by-style':False,
    'prompt-overwrite':True,
    'set-allow-empty-selection':False,  # not used now
    'adjust-range':'auto',
    'auto-save':False,
    'broadcast-style':['linewidth', 'linetype', 'pointsize', 'edgewidth']
}

default_figure_style = RestrictDict({
    'size': [0, 0],
    'dpi':200,
    'margin': [0.05, 0.05, 0.05, 0.05],
    'spacing': [0.05, 0.05]
})
# TODO LOW dpi aware of high-resolution 
default_figure_size_inches = [6,4]
default_figure_style['size'] = [
    default_figure_size_inches[0]*default_figure_style['dpi'],
    default_figure_size_inches[1]*default_figure_style['dpi'],
    ]

default_figure_attr = RestrictDict({
    'split': [1,1]
})

default_major_axis_style = RestrictDict({
    'axis':RestrictDict({
        'linewidth':1,
        'linetype':LineType.SOLID,
        'color':Color.BLACK,
        'visible':True,
        'zindex':0
    }),
    'label':RestrictDict({
        'fontfamily':'Times New Roman',
        'fontsize':14,
        'color':Color.BLACK,
        'visible':True,
    }),
    'tick':RestrictDict({
        'fontfamily':'Times New Roman',
        'fontsize':12,
        'format':'%.2f',
        'color':Color.BLACK,
        'orient':'out',
        'visible':True
    })
})

default_minor_axis_style = RestrictDict({
    'axis':RestrictDict({
        'linewidth':1,
        'linetype':LineType.SOLID,
        'color':Color.BLACK,
        'visible':True,
        'zindex':0
    }),
    'label':RestrictDict({
        'fontfamily':'Times New Roman',
        'fontsize':14,
        'color':Color.BLACK,
        'visible':False
    }),
    'tick':RestrictDict({
        'fontfamily':'Times New Roman',
        'fontsize':12,
        'format':'%.1f',
        'color':Color.BLACK,
        'orient':'out',
        'visible':False
    })
})

default_axis_attr = RestrictDict({
    'range': (None, None),
    'interval': 0.1
})

default_grid_style = RestrictDict({
    'linewidth': 0,
    'linetype':LineType.DASH,
    'linecolor':Color.GREY,
    'visible':False
})

default_dataline_style = RestrictDict({
    'linewidth':1,
    'linetype':LineType.SOLID,
    'linecolor':Color.BLACK,    # 'color' sets both line and point
    'pointsize':0,
    'pointtype':PointType.CIRCLE,
    'edgewidth':1,
    'edgecolor':Color.BLACK,
    'fillcolor':Color.BLACK,
    'visible':True,
    'zindex':0
})

# Global default drawline style
default_drawline_style = RestrictDict({
    'linewidth':1,
    'linetype':LineType.SOLID,
    'linecolor':Color.BLACK,
    'pointsize':0,
    'pointtype':PointType.CIRCLE,
    'edgewidth':1,
    'edgecolor':Color.BLACK,
    'fillcolor':Color.BLACK,
    'visible':True,
    'coord': 'data',
    'zindex':0
})

default_text_style = RestrictDict({
    'fontfamily':'Times New Roman',     # 'font' set both family and size
    'fontsize':14,
    'color':Color.BLACK,
    'visible':True,
    'coord': 'axis',
    'zindex':0
})

default_legend_style = RestrictDict({
    'alpha':0,
    'linewidth':0,
    'linecolor':Color.BLACK,
    'linetype':LineType.NONE,
    'fontfamily':'Times New Roman',
    'fontsize':14,
    'color':Color.BLACK,
    'visible':True,
    'pos':'best',       # both str and (a,b) is valid
    'zindex':0
})

default_legend_attr = RestrictDict({
    'pos': 'best'
})

default_subfigure_style = RestrictDict({
    'padding': [0.1, 0.1, 0.0, 0.0],
    'palatte': 'mpl.Spectral',   # TODO: CHANGE BACK AFTER DEBUGGING!
    'default-dataline': default_dataline_style,
    'default-drawline': default_drawline_style,
    'default-text': default_text_style,
    'title':'',
    'xaxis':{
        'axis':default_major_axis_style['axis'],
        'xlabel':default_major_axis_style['label'],
        'xtick':default_major_axis_style['tick'],
        'xgrid': default_grid_style
    },
    'yaxis':{
        'axis':default_major_axis_style['axis'],
        'ylabel':default_major_axis_style['label'],
        'ytick':default_major_axis_style['tick'],
        'ygrid': default_grid_style
    },
    'raxis':{
        'axis':default_minor_axis_style['axis'],
        'rlabel':default_minor_axis_style['label'],
        'rtick':default_minor_axis_style['tick'],
        'rgrid': default_grid_style
    },
    'taxis':{
        'axis':default_minor_axis_style['axis'],
        'tlabel':default_minor_axis_style['label'],
        'ttick':default_minor_axis_style['tick'],
        'tgrid': default_grid_style
    },
    'legend':default_legend_style
})

default_subfigure_attr = RestrictDict({
    'rsize': (1.0, 1.0),
    'rpos': (0.0, 0.0),
    'group': tuple()
})

# TODO LOW consistency of global options
def init_global_state(m_state):

    m_state.default_figure = state.Figure(
        'default-figure',
        default_figure_style
    )
    m_state.default_figure.subfigures.append(
        state.Subfigure(
            'subfigure0',
            default_subfigure_style
        )
    )
    m_state.options = default_options

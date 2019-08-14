
import argparse

from . import state
from . import errors
from .style import Color, LineType, PointType
from .collection_util import RestrictDict, extract_single

default_options = {
    'auto-adjust-range':True,
    'data-title':'auto',
    'broadcast-style':['linewidth', 'linetype', 'pointsize', 'edgewidth'],
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
# TODO LOW FEATURE dpi aware of high-resolution 
default_figure_size_inches = [6,4]
default_figure_style['size'] = [
    default_figure_size_inches[0]*default_figure_style['dpi'],
    default_figure_size_inches[1]*default_figure_style['dpi'],
    ]

default_figure_attr = RestrictDict({
    'split': [1,1]
})

default_major_axis_style = RestrictDict({
    'linewidth':0.5,
    'linetype':LineType.SOLID,
    'color':Color.BLACK,
    'visible':True,
    'zindex':0,
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
    }),
    'grid':RestrictDict({
        'linewidth': 0,
        'linetype':LineType.DASH,
        'linecolor':Color.GREY,
        'visible':False
    })
})

default_minor_axis_style = RestrictDict({
    'linewidth':0.5,
    'linetype':LineType.SOLID,
    'color':Color.BLACK,
    'visible':True,
    'zindex':0,
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
    }),
    'grid':RestrictDict({
        'linewidth': 0,
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

def init_global_state(m_state):

    m_state.default_figure = state.Figure(
        'default-figure',
        RestrictDict(extract_single(default_figure_style))
    )
    m_state.options = default_options
    m_subfig = m_state.default_figure.subfigures[0]
    m_subfig.datalines = [
        state.FigObject('line%d'%i, RestrictDict({}), RestrictDict({}))
         for i in range(len(m_subfig.dataline_template))
    ]
    for i in range(len(m_subfig.datalines)):
        m_subfig.datalines[i].style = m_subfig.dataline_template[i]

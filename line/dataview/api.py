

import numpy as np

from . import plot
from . import fill
from . import fit as fit_
from ..parse import parse_style_descriptor, build_line_style


def plot_line(m_state, *args, **kwargs):
    return _plot(m_state, 'line', _assemble_xy, *args, **kwargs)


def plot_hist(m_state, *args, **kwargs):
    return _plot(m_state, 'hist', _assemble_x, *args, **kwargs)


def plot_bar(m_state, *args, **kwargs):
    return _plot(m_state, 'bar', _assemble_xy, *args, **kwargs)


def fill_h(m_state, obj1, obj2=None, **kwargs):
    """ Fill the space between two lines, or line + horizontol axis
    """

    if obj2 is None:
        return fill.fill_h(m_state, obj1.data, None, **kwargs)
    elif isinstance(obj2, (int, float)):
        return fill.fill_h(m_state, obj1.data, obj2, **kwargs)
    else:
        return fill.fill_h(m_state, obj1.data, obj2.data, **kwargs)  

def fit(m_state, target, **kwargs):
    return fit_.fit_dataline(m_state.cur_subfigure(), target, **kwargs)


def _plot(m_state, chart_type, assembler, *args, labelfmt='%T', auto_range=None, xlabel='', ylabel='', source='', **kwargs):
    """ Backend for plotting a line.
    Necesary arguments will be passed to `do_plot()` directly;
    Additional arguments will be passed to style
    """

    pg = plot.PlottingGroup()

    pg.xlabel = xlabel
    pg.ylabel = ylabel
    pg.source = source
    pg.style = kwargs

    assembler(pg, *args)

    if isinstance(pg.xdata, (list, tuple)):
        pg.xdata = np.array(pg.xdata)
    if isinstance(pg.ydata, (list, tuple)):
        pg.ydata = np.array(pg.ydata)

    m_state.cur_subfigure(True)
    return plot.do_plot(m_state, 
        (pg,), 
        keep_existed=True, 
        labelfmt=labelfmt,
        auto_range=auto_range,
        chart_type=chart_type)[0]


def _assemble_xy(pg, *args):
    """ Parse argments with cases:
    x, y, style_desc
    y, style_desc
    x, y
    y
    """

    pg.ydata = args[0]
    style_desc = None

    if len(args) > 1:
        if not isinstance(args[1], str):
            pg.xdata = pg.ydata
            pg.ydata = args[1]
            if len(args) > 2:
                style_desc = args[2]
        else:
            style_desc = args[1]
            pg.xdata = np.arange(1, len(pg.ydata) + 1)
    else:
        pg.xdata = np.arange(1, len(pg.ydata) + 1)
        
    if style_desc:
        pg.style.update(build_line_style(*parse_style_descriptor(style_desc)))


def _assemble_x(pg, *args):
    """ Parse arguments with cases:
    x, style_desc
    x
    """
    pg.ydata = args[0]
    
    if len(args) > 1:
        pg.style.update(build_line_style(*parse_style_descriptor(args[1])))
        
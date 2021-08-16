

import numpy as np

from . import plot
from . import fill as fill_
from . import fit as fit_
from ..style_proc import parse_style_descriptor, build_line_style


def plot_line(m_state, *args, **kwargs):
    return _plot(m_state, 'line', _assemble_xy, *args, **kwargs)


def plot_hist(m_state, *args, **kwargs):
    return _plot(m_state, 'hist', _assemble_x, *args, **kwargs)


def plot_bar(m_state, *args, **kwargs):
    return _plot(m_state, 'bar', _assemble_xy, *args, **kwargs)


def fill(m_state, x, y, **kwargs):
    from .datapack import StaticPairedDataPack

    return m_state.cur_subfigure(True).add_polygon(StaticPairedDataPack(np.array(x), np.array(y)), **kwargs)


def fill_between(m_state, x, y1, y2=0, **kwargs):
    if isinstance(x, (list, tuple)):
        x = np.array(x)
    if isinstance(y1, (int, float)):
        y1 = np.ones(x.shape) * y1
    elif isinstance(y1, (list, tuple)):
        y1 = np.array(y1)
    if isinstance(y2, (int, float)):
        y2 = np.ones(x.shape) * y2
    elif isinstance(y2, (list, tuple)):
        y2 = np.array(y2)

    return fill(m_state, np.concatenate((x, np.flip(x))), np.concatenate((y1, np.flip(y2))), **kwargs)


def fill_betweenx(m_state, y, x1, x2=0, **kwargs):
    if isinstance(y, (list, tuple)):
        y = np.array(y)
    if isinstance(x1, (int, float)):
        x1 = np.ones(y.shape) * x1
    elif isinstance(x1, (list, tuple)):
        x1 = np.array(x1)
    if isinstance(x2, (int, float)):
        x2 = np.ones(y.shape) * x2
    elif isinstance(x2, (list, tuple)):
        x2 = np.array(x2)

    return fill(m_state, np.concatenate((x1, x2)), np.concatenate((y, np.flip(y))), **kwargs)


fill_betweenobj = fill_.fill_betweenobj

def fit(m_state, target, **kwargs):
    return fit_.fit_dataline(m_state.cur_subfigure(), target, **kwargs)


def _plot(m_state, chart_type, assembler, *args, labelfmt='%T', auto_range=None, xlabel='', ylabel='', source='', **kwargs):
    """ Backend for plotting a line.
    Necessary arguments will be passed to `do_plot()` directly;
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
        
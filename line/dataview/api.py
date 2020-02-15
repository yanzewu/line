
from . import plot
from ..parse import parse_style_descriptor, build_line_style


def plot_line(m_state, *args, **kwargs):
    return _plot(m_state, 'line', _assemble_xy, *args, **kwargs)


def plot_hist(m_state, *args, **kwargs):
    return _plot(m_state, 'hist', _assemble_x, *args, **kwargs)


def plot_bar(m_state, *args, **kwargs):
    return _plot(m_state, 'bar', _assemble_xy, *args, **kwargs)


def _plot(m_state, chart_type, assembler, *args, labelfmt='%T [%F]', auto_range=None, xlabel='', ylabel='', source='', **kwargs):
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

    m_state.cur_subfigure(True).is_changed = True
    plot.plot_single_group(m_state.cur_subfigure(), pg, 
        keep_existed=False, 
        labelfmt=labelfmt,
        auto_range=auto_range,
        chart_type=chart_type)
    refresh_label(m_state.cur_subfigure())


def _assemble_xy(pg, *args):
    
    pg.xdata = np.array(args[0])
    style_desc = None

    if len(args) > 1:
        if not isinstance(str, args[1]):
            pg.ydata = np.array(args[1])
            if len(args) > 2:
                style_desc = args[2]
        else:
            style_desc = args[1]
            pg.ydata = pg.xdata
            pg.xdata = np.arange(1, len(pg.xdata) - 1)
    else:
        pg.ydata = pg.xdata
        pg.xdata = np.arange(1, len(pg.xdata) - 1)
        
    if style_desc:
        pg.style.update(build_line_style(*parse_style_descriptor(style_desc)))


def _assemble_x(pg, *args):
    pg.ydata = np.array(args[0])
    
    if len(args) > 1:
        pg.style.update(build_line_style(*parse_style_descriptor(args[1])))
        
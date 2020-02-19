
import numpy as np


class PlottingGroup:

    def __init__(self, **kwargs):

        self.xdata = kwargs.get('x', None)
        self.ydata = kwargs.get('y', None)
        self.xlabel = kwargs.get('xlabel', '')
        self.ylabel = kwargs.get('ylabel', '')
        self.source = kwargs.get('source', '')
        self.style = kwargs.get('style', {})


def do_plot(m_state, plot_groups, keep_existed=False, labelfmt='%F:%T', auto_range=None, chart_type='line'):
    """
    Do plotting on gca, create one if necessary.

    plot_groups: List of PlottingGroup instance;
    keep_existed: Don't clear gca;
    label_fmt: Label format when plotting data from multiple files. %T=>title, %F=>filename;
    auto_range: Set automatic range. Set `None` to use program default;
    chart_type: line/bar/hist;
    """

    m_state.cur_subfigure(True).is_changed = True

    # handle append
    if not keep_existed:
        m_state.cur_subfigure().clear()

    # add filename to data label?
    has_multiple_files = len(set((pg.source for pg in plot_groups))) != 1
    for pg in plot_groups:
        plot_single_group(m_state.cur_subfigure(), pg, 
            keep_existed=keep_existed,
            labelfmt=labelfmt if has_multiple_files else '%T',
            auto_range=auto_range,
            chart_type=chart_type)
    
    refresh_label(m_state.cur_subfigure())
    if auto_range or (auto_range is None and m_state.options['auto-adjust-range']):
        m_state.cur_subfigure().update_style({'xrange':'auto', 'yrange':'auto'})
    

def plot_single_group(subfigure, pg, keep_existed=False, labelfmt='%T [%F]', auto_range=None, chart_type='line'):

    from .. import sheet_util

    m_ylabel = labelfmt.replace('%T', pg.ylabel).replace('%F', pg.source)
    m_xdata = sheet_util.flatten(pg.xdata)
    m_ydata = sheet_util.flatten(pg.ydata)

    if chart_type == 'line':
        subfigure.add_dataline((m_xdata, m_ydata), m_ylabel, pg.xlabel, pg.style)
    elif chart_type == 'bar':
        subfigure.add_bar((m_xdata, m_ydata), m_ylabel, pg.xlabel, False, pg.style)
    elif chart_type == 'hist':
        pg.style.setdefault('bin', 10)
        pg.style.setdefault('width', 1.0)
        pg.style.setdefault('norm', 'Distribution')
        subfigure.add_bar(m_ydata, m_ylabel, pg.ylabel, True, pg.style)
        # m_ylabel is not used for axis label.


def refresh_label(subfigure):
    """ Set automatic x/y label for gca.
    """
    xlabels = set((d.get_style('xlabel') for d in subfigure.datalines + subfigure.bars))
    
    if len(xlabels) == 1:
        subfigure.axes[0].label.update_style({'text': xlabels.pop()})
    if not subfigure.datalines and not subfigure.bars:
        return
    histogram_counts = len([b for b in subfigure.bars if b.dynamic_bin])
    if histogram_counts == 0:
        ylabels = set((d.get_style('label') for d in subfigure.datalines))
    elif histogram_counts == len(subfigure.datalines) + len(subfigure.bars):
        ylabels = {'Distribution'}  # The label "Distribution" is set only when all plots are histogram
    else:
        return
    if len(ylabels) == 1:
        subfigure.axes[1].label.update_style({'text': ylabels.pop()})

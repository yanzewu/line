
import numpy as np

from . import datapack


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

    # handle append
    m_state.cur_subfigure(True)
    if not keep_existed:
        m_state.cur_subfigure().clear()

    # add filename to data label?
    has_multiple_files = len(set((pg.source for pg in plot_groups))) != 1
    r = []
    for pg in plot_groups:
        r.append(plot_single_group(m_state.cur_subfigure(), 
            pg, 
            labelfmt=labelfmt if has_multiple_files else '%T',
            chart_type=chart_type))
    
    if auto_range or (auto_range is None and m_state.options['auto-adjust-range']):
        m_state.cur_subfigure().update_style({'xrange':'auto', 'yrange':'auto'})
    
    return r
    

def plot_single_group(subfigure, pg, labelfmt, chart_type='line'):

    from .. import sheet_util

    m_ylabel = labelfmt.replace('%T', pg.ylabel).replace('%F', pg.source)
    m_xdata = sheet_util.flatten(pg.xdata)
    m_ydata = sheet_util.flatten(pg.ydata)

    if chart_type == 'line':
        return subfigure.add_dataline(
            datapack.StaticPairedDataPack(m_xdata, m_ydata), m_ylabel, pg.xlabel, pg.style)
    elif chart_type == 'bar':
        return subfigure.add_bar(
            datapack.StaticPairedDataPack(m_xdata, m_ydata), m_ylabel, pg.xlabel, False, pg.style)
    elif chart_type == 'hist':
        pg.style.setdefault('norm', 'Distribution')
        return subfigure.add_bar(
            datapack.DistributionDataPack(m_ydata, pg.style.get('bin', 10), pg.style.get('norm', 'Distribution')),
            m_ylabel, pg.ylabel, True, pg.style)
        # m_ylabel is not used for axis label.


""" Implementation of plotting functions with matplot backend.
"""

import numpy as np
import logging
import os

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.lines as lines
import matplotlib.ticker as ticker
import matplotlib.font_manager as font_manager

from . import state
from . import style
from .defaults import default_math_font, default_fonts

logger = logging.getLogger('line')

# things between initialize() and finalize() can be viewed as a show() process
# so everything need to be redraw once closed.

matplotlib.rcParams['mathtext.fontset'] = default_math_font
matplotlib.rcParams['font.family'] = default_fonts

def initialize(m_state:state.GlobalState, plt_backend='Qt5Agg'):
    try:
        plt.switch_backend(plt_backend)
    except ImportError:
        logger.info('Fallback to TK backend')
        
    if m_state.is_interactive:
        plt.ion()
        for name, figure in m_state.figures.items():
            _update_figure(figure, name)

def finalize(m_state:state.GlobalState):
    if m_state.is_interactive:
        plt.ioff()
        for figure in m_state.figures.values():
            figure.clear_backend()
    

def update_figure(m_state:state.GlobalState, redraw_subfigures=True):
    """ Replot current figure;
    If `redraw_subfigures` is set, will update all subfigures.
    """

    _update_figure(m_state.cur_figure(), m_state.cur_figurename, redraw_subfigures)


def _update_figure(m_fig:state.Figure, name:str, redraw_subfigures=True):

    dpi = m_fig.attr('dpi')
    size = m_fig.attr('size')
    size_inches = (size[0]/dpi, size[1]/dpi)

    if m_fig.backend == None or not plt.fignum_exists(m_fig.backend.number):
        m_fig.backend = plt.figure(name, figsize=size_inches, dpi=dpi)
        logger.debug('Creating new figure: %s' % name)

        for subfig in m_fig.subfigures:
            subfig.backend = None
    else:
        m_fig.backend.dpi = dpi
        m_fig.backend.set_size_inches(*size_inches)

    m_plt_fig = m_fig.backend
    m_plt_fig.clear()
    margin = m_fig.attr('margin')

    def scale(x):
        return x[0]*(1-margin[3]-margin[0])+margin[0], x[1]*(1-margin[2]-margin[1])+margin[1], \
            x[2]*(1-margin[3]-margin[0]), x[3]*(1-margin[2]-margin[1])

    for subfig in m_fig.subfigures:
        
        pos = subfig.attr('rpos')
        rsize = subfig.attr('rsize')
        padding = subfig.attr('padding')

        ax = subfig.backend
        if ax is None:
            ax = plt.Axes(
                m_plt_fig,
                scale((pos[0]+padding[0], pos[1]+padding[1], 
                rsize[0]-padding[0], rsize[1]-padding[1]))
            )
            subfig.backend = ax
        else:
            ax.set_position((
                scale((pos[0]+padding[0], pos[1]+padding[1], 
                rsize[0]-padding[0], rsize[1]-padding[1]))
            ))

        m_plt_fig.add_axes(ax)
        logger.debug('Subfigure found at %s' % str(ax.get_position().bounds))

    if redraw_subfigures:
        for subfig in m_fig.subfigures:
            _update_subfigure(subfig)
            logger.debug('Updated subfigure %s' % subfig.name)

    #plt.show(block=False)


def update_subfigure(m_state:state.GlobalState):
    """ Update m_state.cur_subfigure()
    """

    # figure is closed -> redraw the figure.
    if not plt.fignum_exists(m_state.cur_figure().backend.number):
        update_figure(m_state)
        return
    
    logger.debug('Updating figure %s, subfigure %d' % (m_state.cur_figurename, m_state.cur_figure().cur_subfigure))
    plt.figure(m_state.cur_figurename)
    _update_subfigure(m_state.cur_subfigure())

def _update_subfigure(m_subfig:state.Subfigure):

    ax = m_subfig.backend
    ax.cla()
    ax.set_visible(m_subfig.attr('visible'))
    ax.set_frame_on(True)

    # ax.set_title(m_subfig.attr('title')) TITLE has fonts...
    # axis
    for i, d in enumerate(('bottom', 'left', 'right', 'top')):
        ax.spines[d].set_visible(m_subfig.axes[i].attr('visible'))
        ax.spines[d].set_linewidth(m_subfig.axes[i].attr('linewidth'))
        ax.spines[d].set_linestyle(m_subfig.axes[i].attr('linetype').to_str())
        ax.spines[d].set_color(m_subfig.axes[i].attr('color'))

    label_styles = []
    tick_styles = []
    grid_styles = []

    for i in range(4):
        label_styles.append(m_subfig.axes[i].label.computed_style)
        tick_styles.append(m_subfig.axes[i].tick.computed_style)
        grid_styles.append(m_subfig.axes[i].grid.computed_style)

    # labels
    ax.set_xlabel(
        m_subfig.axes[0].label.attr('text'),
        color=label_styles[0]['color'],
        fontfamily=label_styles[0]['fontfamily'],
        fontsize=label_styles[0]['fontsize'],
    )
    ax.set_ylabel(
        m_subfig.axes[1].label.attr('text'),
        color=label_styles[1]['color'],
        fontfamily=label_styles[1]['fontfamily'],
        fontsize=label_styles[1]['fontsize'],
    )
    # the right label requires drawing a new axis
    ax.set_xscale(m_subfig.axes[0].attr('scale'))
    ax.set_yscale(m_subfig.axes[1].attr('scale'))

    #ax.set_autoscale_on(False)

    # tick
    for i, a in enumerate('xy'):
        ax.tick_params(
            a,
            direction=tick_styles[i]['orient'],
            labelcolor=tick_styles[i]['color'],
            width=tick_styles[i]['linewidth']
        )
    
    # tick label style
    for xticklabel in ax.get_xmajorticklabels():
        xticklabel.set_fontfamily(tick_styles[0]['fontfamily'])
        xticklabel.set_fontsize(tick_styles[0]['fontsize'])

    for yticklabel in ax.get_ymajorticklabels():
        yticklabel.set_fontfamily(tick_styles[1]['fontfamily'])
        yticklabel.set_fontsize(tick_styles[1]['fontsize'])

    # tick format
    ax.xaxis.set_major_formatter(ticker.FormatStrFormatter(
        m_subfig.axes[0].tick.attr('format')
    ))
    ax.yaxis.set_major_formatter(ticker.FormatStrFormatter(
        m_subfig.axes[1].tick.attr('format')
    ))
    
    logger.debug('Total %d datalines, %d drawlines, %d texts' % (
        len(m_subfig.datalines), len(m_subfig.drawlines), len(m_subfig.texts)))

    # lines
    for dataline in m_subfig.datalines:
        m_style = dataline.computed_style

        ax.plot( 
            dataline.x,
            dataline.y,
            color=m_style['linecolor'],
            label=m_style['label'],
            linestyle=m_style['linetype'].to_str(),
            linewidth=m_style['linewidth'],
            marker=m_style['pointtype'].to_str(),
            mec=m_style['edgecolor'],
            mew=m_style['edgewidth'],
            mfc=m_style['fillcolor'],
            ms=m_style['pointsize'],
            markevery=m_style['skippoint'],
            visible=m_style['visible'],
            zorder=m_style['zindex']
        )

    for bar in m_subfig.bars:
        m_style = bar.computed_style

        ax.bar(
            bar.x,
            bar.y,
            alpha=m_style['alpha'],
            width=m_style['width'],
            label=m_style['label'],
            bottom=0,
            align='center',
            color=m_style['fillcolor'],
            edgecolor=m_style['linecolor'],
            linewidth=m_style['linewidth'],
            tick_label=None
        )

    for drawline in m_subfig.drawlines:
        m_style = drawline.computed_style

        xlo, ylo = drawline.attr('startpos')
        xhi, yhi = drawline.attr('endpos')

        if m_style['coord'] == 'data' and (xlo is None or xhi is None or ylo is None or yhi is None):
            if xlo is None or xhi is None:
                trans = ax.get_yaxis_transform()
                xlo = m_subfig.get_axes_coord(xlo, 0, 'left')
                xhi = m_subfig.get_axes_coord(xhi, 0, 'right')
            else:
                trans = ax.get_xaxis_transform()
                ylo = m_subfig.get_axes_coord(ylo, 1, 'left')
                yhi = m_subfig.get_axes_coord(yhi, 1, 'right')
        else:
            trans = ax.transData if m_style['coord'] == 'data' else ax.transAxes

        ax.add_line(lines.Line2D(
            (xlo, xhi),
            (ylo, yhi),
            color=m_style['linecolor'],
            linestyle=m_style['linetype'].to_str(),
            linewidth=m_style['linewidth'],
            marker=m_style['pointtype'].to_str(),
            mec=m_style['edgecolor'],
            mew=m_style['edgewidth'],
            mfc=m_style['fillcolor'],
            ms=m_style['pointsize'],
            transform=trans,
            visible=m_style['visible'],
            zorder=m_style['zindex']
        ))

    for polygon in m_subfig.polygons:
        m_style = polygon.computed_style

        ax.fill(
            polygon.x,
            polygon.y,
            alpha=m_style['alpha'],
            color=m_style['fillcolor'],
            edgecolor=m_style['linecolor'],
            linestyle=m_style['linetype'].to_str() if m_style['linetype'] != style.LineType.NONE else None,
            linewidth=m_style['linewidth'],
            visible=m_style['visible'],
            zorder=m_style['zindex']
        )

    for text in m_subfig.texts:

        m_style = text.computed_style

        x, y = text.attr('pos')

        ax.text(
            x,
            y,
            text.attr('text'),
            color=m_style['color'],
            fontfamily=m_style['fontfamily'],
            fontsize=m_style['fontsize'],
            transform=ax.transData if m_style['coord'] == 'data' else ax.transAxes,
            visible=m_style['visible'],
            zorder=m_style['zindex']
        )

    x_interval = m_subfig.axes[0].attr('range')[2]
    x_ticks = m_subfig.axes[0].attr('tickpos')
    ax.set_xticks(x_ticks)
    ax.set_xbound(x_ticks[0], x_ticks[-1])

    y_interval = m_subfig.axes[1].attr('range')[2]
    y_ticks = m_subfig.axes[1].attr('tickpos')
    ax.set_yticks(y_ticks)
    ax.set_ybound(y_ticks[0], y_ticks[-1])

    # This is a hack -- when you move your figure, the ticker positions are not gauranteed.
    if m_subfig.axes[0].attr('scale') == 'linear':
        ax.xaxis.set_major_locator(ticker.MaxNLocator(nbins=len(x_ticks), steps=[1,1.5,2,2.5,3,4,5,6,7.5,8,10]))
    elif m_subfig.axes[0].attr('scale') == 'log':
        x_subs = [1.0] + np.arange(int(x_interval*10), 10, int(x_interval*10), dtype=int).tolist() if x_interval else (1.0,)
        ax.xaxis.set_major_locator(ticker.LogLocator(subs=x_subs))
        ax.xaxis.set_minor_locator(ticker.LogLocator(subs=(1,5,)))
    if m_subfig.axes[1].attr('scale') == 'linear':
        ax.yaxis.set_major_locator(ticker.MaxNLocator(nbins=4, steps=[1,1.5,2,2.5,3,4,5,6,7.5,8,10]))
    elif m_subfig.axes[1].attr('scale') == 'log':
        y_subs = [1.0] + np.arange(int(y_interval*10), 10, int(y_interval*10), dtype=int).tolist() if y_interval else (1.0,)
        ax.yaxis.set_major_locator(ticker.LogLocator(subs=y_subs))
        ax.yaxis.set_minor_locator(ticker.LogLocator(subs=(1,5,)))

    # grid
    for i, n in enumerate('xy'):
        ax.grid(grid_styles[i]['visible'], which='major', axis=n, 
            linewidth=grid_styles[i]['linewidth'],
            linestyle=grid_styles[i]['linetype'].to_str(),
            color=grid_styles[i]['linecolor'],
            visible=grid_styles[i]['visible']
        )

    # legend
    if m_subfig.legend.attr('visible') and m_subfig.datalines + m_subfig.bars:

        m_style = m_subfig.legend.computed_style

        legend = ax.legend(
            fancybox=False,
            facecolor=m_style['color'],
            edgecolor=m_style['linecolor'],
            fontsize=m_style['fontsize'],
            loc=m_subfig.legend.attr('pos'),
            frameon=True,
            framealpha=m_style['alpha']
        )

        lt = m_style['linetype'].to_str()
        frame = legend.get_frame()
        frame.set_linewidth(m_style['linewidth'])
        frame.set_linestyle(lt if lt else 'None')
        frame.set_zorder(m_style['zindex'])

        for t in legend.get_texts():
            t.set_fontfamily(m_style['fontfamily'])


def save_figure(m_state:state.GlobalState, filename):
    """ Save current figure. Update if necessary.
    """

    if not m_state.is_interactive:  # delayed evaluation
        update_figure(m_state)
    plt.savefig(
        filename, dpi='figure'
    )
    if not m_state.is_interactive:
        m_state.cur_figure().clear_backend()


# Interactive mode functions

def update_focus_figure(m_state:state.GlobalState):
    """ Bring figure m_state.cur_figure to the front. Only called
    in interactive mode.
    """
    plt.figure(m_state.cur_figurename)
    if plt.get_backend().startswith('Qt'):
        plt.get_current_fig_manager().window.raise_()
    elif plt.get_backend().startswith('Tk'):
        plt.get_current_fig_manager().window.attributes('-topmost', 1)
        plt.get_current_fig_manager().window.attributes('-topmost', 0)


def close_figure(m_state:state.GlobalState):
    """ Close current figure. Only called in interactive mode.
    """
    plt.close(m_state.cur_figurename)


# Noninteractive mode functions

def show(m_state:state.GlobalState):
    """ Showing all figures. Only called in non-interactive mode.
    """
    for name, figure in m_state.figures.items():
        _update_figure(figure, name)

    plt.show()

    for figure in m_state.figures.values():
        figure.clear_backend()


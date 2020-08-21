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
import matplotlib.tight_layout as tight_layout

from . import state
from . import style
from . import defaults

logger = logging.getLogger('line')

# things between initialize() and finalize() can be viewed as a show() process
# so everything need to be redraw once closed.

matplotlib.rcParams['mathtext.fontset'] = defaults.default_math_font
matplotlib.rcParams['font.family'] = defaults.default_fonts

if isinstance(defaults.default_options['mpl-backend'], str):
    defaults.default_options['mpl-backend'] = [defaults.default_options['mpl-backend']]
primary_backend = defaults.default_options['mpl-backend'][0]
alternative_backends = defaults.default_options['mpl-backend'][1:]
silent_backend = defaults.default_options['mpl-silent-backend']

def initialize(m_state:state.GlobalState, silent=None):
    """ silent: If `True`, use silent_backend instead of primary_backend;
                If `None`, detect `m_state.is_interactive`.
    """
    if silent is None:
        silent = not m_state.is_interactive

    try:
        if not silent:
            plt.switch_backend(primary_backend)
        else:
            plt.switch_backend(silent_backend)
    except ImportError:
        switch_success = False
        for ab in alternative_backends:
            try:
                plt.switch_backend(ab)
            except ImportError:
                continue
            else:
                switch_success = True
                logger.info('Fallback to backend %s' % ab)
                break
        if not switch_success:
            logger.info('Cannot switch to any alternative backend. Use default instead')
        
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

        #m_fig.backend.set_dpi(dpi) # TODO incorrect behavior in Windows
        m_fig.backend.set_size_inches(*size_inches)
    else:
        #m_fig.backend.set_dpi(dpi)
        m_fig.backend.set_size_inches(*size_inches)

    m_plt_fig = m_fig.backend
    m_plt_fig.clear()
    margin = m_fig.attr('margin')

    def scale(x):
        return x[0]*(1-margin[2]-margin[0])+margin[0], x[1]*(1-margin[3]-margin[1])+margin[1], \
            x[2]*(1-margin[2]-margin[0]), x[3]*(1-margin[3]-margin[1])

    for subfig in m_fig.subfigures:
        
        pos = subfig.attr('rpos')
        rsize = subfig.attr('rsize')
        padding = subfig.attr('padding')

        ax = subfig.backend
        frame = scale((pos[0]+padding[0], pos[1]+padding[1], 
            rsize[0]-padding[0]-padding[2], rsize[1]-padding[1]-padding[3]))
        if ax is None:
            ax = plt.Axes(m_plt_fig, frame)
            subfig.backend = ax
        else:
            ax.set_position(frame)

        m_plt_fig.add_axes(ax)
        logger.debug('Subfigure found at %s' % str(ax.get_position().bounds))

    if redraw_subfigures:
        for subfig in m_fig.subfigures:
            _update_subfigure(subfig, tight_layout.get_renderer(m_fig.backend))
            logger.debug('Updated subfigure %s' % subfig.name)

    #plt.show(block=False)


def update_subfigure(m_state:state.GlobalState):
    """ Update m_state.cur_subfigure()
    """

    # figure is closed -> redraw the figure.
    if m_state.cur_figure().backend is None or not plt.fignum_exists(m_state.cur_figure().backend.number):
        update_figure(m_state)
        return
    
    logger.debug('Updating figure %s, subfigure %d' % (m_state.cur_figurename, m_state.cur_figure().cur_subfigure))
    fig = plt.figure(m_state.cur_figurename)
    _update_subfigure(m_state.cur_subfigure(), tight_layout.get_renderer(fig))

def _update_subfigure(m_subfig:state.Subfigure, renderer):

    ax = m_subfig.backend
    ax.cla()
    ax.set_visible(m_subfig.attr('visible'))
    ax.set_frame_on(True)

    if m_subfig.title.attr('text') and m_subfig.title.attr('visible'):
        ax.set_title(m_subfig.title.attr('text'),
            fontsize=m_subfig.title.attr('fontsize'),
            fontfamily=m_subfig.title.attr('fontfamily')
        )

    spine_names = ('bottom', 'left', 'right', 'top')

    # axis
    for i, d in enumerate(spine_names):
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

    # creating additional axes for right/top
    for j in (2, 3):
        if m_subfig.axes[j].attr('enabled'):
            if m_subfig.axes[j].backend:
                try:
                    m_subfig.axes[j].backend.remove()
                except KeyError:
                    pass
            m_subfig.axes[j].backend = ax.twinx() if j == 2 else ax.twiny()
            for d in spine_names:
                m_subfig.axes[j].backend.spines[d].set_visible(False)
        else:
            m_subfig.axes[j].backend = None

    backends = (ax, ax, m_subfig.axes[2].backend, m_subfig.axes[3].backend)
    is_xside = (True, False, False, True)

    for i, b in enumerate(backends):
        if b is None:
            continue

        # labels
        set_labelfunc = b.set_xlabel if is_xside[i] else b.set_ylabel
        posname = 'x' if is_xside[i] else 'y'
        set_labelfunc(
            m_subfig.axes[i].label.attr('text'),
            color=label_styles[i]['color'],
            fontfamily=label_styles[i]['fontfamily'],
            fontsize=label_styles[i]['fontsize'],
            visible=label_styles[i]['visible'],
            **{posname: label_styles[i]['pos'][0]},
        )

        # scales
        set_scalefunc = b.set_xscale if is_xside[i] else b.set_yscale
        set_scalefunc(m_subfig.axes[i].attr('scale'))

    #ax.set_autoscale_on(False)

        # ticks
        tick_name = 'x' if is_xside[i] else 'y'
        b.tick_params(
            tick_name,
            which='major',
            direction=tick_styles[i]['orient'],
            labelcolor=tick_styles[i]['color'],
            width=tick_styles[i]['linewidth'],
            length=tick_styles[i]['length']
        )
        b.tick_params(
            tick_name,
            which='minor',
            direction=tick_styles[i]['orient-minor'],
            labelcolor=tick_styles[i]['color'],
            width=tick_styles[i]['linewidth-minor'],
            length=tick_styles[i]['length-minor'],
        )
    
        # tick labels
        major_tick_labels = b.get_xmajorticklabels() if is_xside[i] else b.get_ymajorticklabels()
        for mtl in major_tick_labels:
            mtl.set_fontfamily(tick_styles[i]['fontfamily'])
            mtl.set_fontsize(tick_styles[i]['fontsize'])
            mtl.set_visible(tick_styles[i]['visible'])

        # tick format
        target_axis = b.xaxis if is_xside[i] else b.yaxis
        if 'formatter' in tick_styles[i]:
            target_axis.set_major_formatter(ticker.FuncFormatter(tick_styles[i]['formatter']))
        else:
            target_axis.set_major_formatter(ticker.FormatStrFormatter(tick_styles[i]['format']))
    
    logger.debug('Total %d datalines, %d drawlines, %d texts' % (
        len(m_subfig.datalines), len(m_subfig.drawlines), len(m_subfig.texts)))

    legend_candidate = []

    # lines
    for dataline in m_subfig.datalines:
        m_style = dataline.computed_style

        if m_style['side'] == (style.FloatingPos.LEFT, style.FloatingPos.TOP):
            target_ax = m_subfig.axes[3].backend
        elif m_style['side'] == (style.FloatingPos.RIGHT, style.FloatingPos.BOTTOM):
            target_ax = m_subfig.axes[2].backend
        else:
            target_ax = ax

        b = target_ax.plot( 
            dataline.data.get_x(),
            dataline.data.get_y(),
            clip_on=m_style['clip'],
            color=m_style['linecolor'],
            label=m_style['label'],
            linestyle=m_style['linetype'].to_str(),
            linewidth=m_style['linewidth'],
            marker=m_style['pointtype'].to_str(),
            mec=m_style['edgecolor'],
            mew=m_style['edgewidth'],
            mfc=None if m_style['fillstyle'] == 'none' else m_style['fillcolor'],
            ms=m_style['pointsize'],
            fillstyle=m_style['fillstyle'],
            markevery=m_style['skippoint'],
            visible=m_style['visible'],
            zorder=m_style['zindex']
        )
        if b and m_style['label']:
            legend_candidate.append((b[0], m_style['label']))

    for bar in m_subfig.bars:
        m_style = bar.computed_style

        if m_style['side'] == (style.FloatingPos.LEFT, style.FloatingPos.TOP):
            target_ax = m_subfig.axes[3].backend
        elif m_style['side'] == (style.FloatingPos.RIGHT, style.FloatingPos.BOTTOM):
            target_ax = m_subfig.axes[2].backend
        else:
            target_ax = ax

        b = target_ax.bar(
            bar.data.get_x(),
            bar.data.get_y(),
            alpha=m_style['alpha'],
            width=m_style['barwidth'],
            label=m_style['label'],
            bottom=0,
            align='center',
            color=m_style['fillcolor'],
            edgecolor=m_style['linecolor'],
            linewidth=m_style['linewidth'],
            tick_label=None
        )
        if b and m_style['label']:
            legend_candidate.append((b[0], m_style['label']))

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
            fillstyle=None if m_style['fillstyle'] == 'none' else m_style['fillstyle'],
            transform=trans,
            visible=m_style['visible'],
            zorder=m_style['zindex']
        ))

    for polygon in m_subfig.polygons:
        m_style = polygon.computed_style

        ax.fill(
            polygon.data.get_x(),
            polygon.data.get_y(),
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

        x, y = _translate_loc_normal(*text.attr('pos'))

        t = ax.text(
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
        text.computed_style['frame'] = style.Rect(*t.get_window_extent(renderer).bounds)
        t.set_position(_get_text_loc(m_subfig, text, text.attr('pos')))

    for i, b in enumerate(backends):
        if b is None:
            continue

        a_begin, a_end, a_interval = m_subfig.axes[i].attr('range')
        a_ticks = m_subfig.axes[i].attr('tickpos')
        set_boundfunc = b.set_xbound if is_xside[i] else b.set_ybound
        set_boundfunc(a_begin if a_begin else a_ticks[0], a_end if a_end else a_ticks[-1])

        set_tickfunc = b.set_xticks if is_xside[i] else b.set_yticks
        set_tickfunc(a_ticks)

        # This is a hack -- when you move your figure, the ticker positions are not gauranteed.
        target_axis = b.xaxis if is_xside[i] else b.yaxis
        if m_subfig.axes[i].attr('scale') == 'linear':
            if m_subfig.axes[i].attr('range')[2] is None:
                target_axis.set_major_locator(ticker.MaxNLocator(nbins=len(a_ticks), steps=[1,1.5,2,2.5,3,4,5,6,7.5,8,10]))
            target_axis.set_minor_locator(ticker.AutoMinorLocator(tick_styles[i]['minor'] + 1))
        elif m_subfig.axes[i].attr('scale') == 'log':
            a_subs = [1.0] + np.arange(int(a_interval*10), 10, int(a_interval*10), dtype=int).tolist() if a_interval else (1.0,)
            target_axis.set_major_locator(ticker.LogLocator(subs=a_subs))
            n = tick_styles[i]['minor'] + 1
            if n > 1:
                target_axis.set_minor_locator(ticker.LogLocator(subs=[10/n*j for j in range(1, n)]))

    # grid (only x, y)
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

        legend_pos = m_subfig.legend.attr('pos')
        if legend_pos == style.FloatingPos.AUTO:
            p = 'best'
            b = None
        else:
            p, b = _translate_loc(*legend_pos)

        legend = ax.legend(
            [lc[0] for lc in legend_candidate],
            [lc[1] for lc in legend_candidate],
            fancybox=False,
            facecolor=m_style['color'],
            edgecolor=m_style['linecolor'],
            fontsize=m_style['fontsize'],
            loc=p,
            bbox_to_anchor=b,
            ncol=m_style['column'],
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

        m_subfig.legend.computed_style['frame'] = style.Rect(*legend.get_window_extent(renderer).bounds)
    
    for i, b in enumerate(backends):
        if b is None:
            m_subfig.axes[i].computed_style['frame'] = style.Rect(0,0,0,0)
            m_subfig.axes[i].tick.computed_style['frame'] = style.Rect(0,0,0,0)
            m_subfig.axes[i].label.computed_style['frame'] = style.Rect(0,0,0,0)
        else:
            target_axis = b.get_xaxis() if is_xside[i] else b.get_yaxis()
            tick_labels = b.get_xticklabels() if is_xside[i] else b.get_yticklabels()
            tb_ax = target_axis.get_tightbbox(renderer)
            m_subfig.axes[i].computed_style['frame'] = style.Rect(tb_ax.bounds if tb_ax else (0,0,0,0))
            m_subfig.axes[i].tick.computed_style['frame'] = [style.Rect(l.get_window_extent(renderer).bounds) for l in tick_labels]
            m_subfig.axes[i].label.computed_style['frame'] = style.Rect(target_axis.get_label().get_window_extent(renderer).bounds)

    m_subfig.computed_style['frame'] = style.Rect(*ax.get_window_extent(renderer).bounds)
    m_subfig.title.computed_style['frame'] = style.Rect(ax.title.get_window_extent(renderer).bounds)


def save_figure(m_state:state.GlobalState, filename):
    """ Save current figure. Update if necessary.
    """

    if not m_state.is_interactive:  # delayed evaluation
        update_figure(m_state)
    plt.savefig(
        filename, dpi=m_state.cur_figure().get_style('dpi')
    )
    if not m_state.is_interactive:
        m_state.cur_figure().clear_backend()


# Interactive mode functions

def update_focus_figure(m_state:state.GlobalState):
    """ Bring figure m_state.cur_figure to the front. Only called
    in interactive mode.
    """
    if not plt.fignum_exists(m_state.cur_figure().backend.number):
        update_figure(m_state, True)

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

def _translate_loc(x, y):
    # this is just ad-hoc. Should use redrawing or float system in the future.

    try:
        return _mpl_loc_code[(x, y)]
    except KeyError:
        return (x, y), None
    
def _translate_loc_normal(x, y):
    return (
        {style.FloatingPos.OUTLEFT:0, style.FloatingPos.LEFT:0, style.FloatingPos.CENTER:0.5, 
            style.FloatingPos.RIGHT:1, style.FloatingPos.OUTRIGHT:1}.get(x, x),
        {style.FloatingPos.OUTBOTTOM:0, style.FloatingPos.BOTTOM:0, style.FloatingPos.CENTER:0.5, 
            style.FloatingPos.TOP:1, style.FloatingPos.OUTTOP:1}.get(y, y))

def _get_text_loc(subfigure, text, pos):

    if pos == style.FloatingPos.AUTO:
        raise ValueError("Text position cannot be auto")
    
    try:
        sf = subfigure.attr('frame')
        tf = text.attr('frame')
    except KeyError:
        return _translate_loc_normal(*pos)
    
    w = tf.width / sf.width
    h = tf.height / sf.height
    margin = text.attr('margin') 

    if pos[0] == style.FloatingPos.LEFT:
        x = margin[0]
    elif pos[0] == style.FloatingPos.CENTER:
        x = 0.5 - w/2
    elif pos[0] == style.FloatingPos.RIGHT:
        x = 1.0 - margin[2] - w
    elif pos[0] == style.FloatingPos.OUTLEFT:
        x = -margin[2] - w
    elif pos[0] == style.FloatingPos.OUTRIGHT:
        x = 1.0 + margin[0]
    else:
        x = pos[0]

    if pos[1] == style.FloatingPos.TOP:
        y = 1.0 - margin[3] - h
    elif pos[1] == style.FloatingPos.CENTER:
        y = 0.5 + h/2
    elif pos[1] == style.FloatingPos.BOTTOM:
        y = margin[1]
    elif pos[1] == style.FloatingPos.OUTTOP:
        y = 1.0 + margin[1] + h
    elif pos[1] == style.FloatingPos.OUTBOTTOM:
        y = -margin[3]
    else:
        y = pos[1]

    return x, y



_mpl_loc_code = {
    (style.FloatingPos.LEFT, style.FloatingPos.BOTTOM): (3, None),
    (style.FloatingPos.LEFT, style.FloatingPos.CENTER): (6, None),
    (style.FloatingPos.LEFT, style.FloatingPos.TOP):    (2, None),
    (style.FloatingPos.RIGHT, style.FloatingPos.BOTTOM):    (4, None),
    (style.FloatingPos.RIGHT, style.FloatingPos.CENTER):    (7, None),
    (style.FloatingPos.RIGHT, style.FloatingPos.TOP):       (1, None),
    (style.FloatingPos.CENTER, style.FloatingPos.BOTTOM):   (8, None),
    (style.FloatingPos.CENTER, style.FloatingPos.CENTER):   (10,None),
    (style.FloatingPos.CENTER, style.FloatingPos.TOP):      (9, None),
    (style.FloatingPos.LEFT, style.FloatingPos.OUTBOTTOM):  (2, (0,0)),
    (style.FloatingPos.LEFT, style.FloatingPos.OUTTOP):     (3, (0,1)),
    (style.FloatingPos.RIGHT, style.FloatingPos.OUTBOTTOM): (1, (1,0)),
    (style.FloatingPos.RIGHT, style.FloatingPos.OUTTOP):    (4, (1,1)),
    (style.FloatingPos.CENTER, style.FloatingPos.OUTBOTTOM):(9, (0.5,0)),
    (style.FloatingPos.CENTER, style.FloatingPos.OUTTOP):   (8, (0.5,1)),
    (style.FloatingPos.OUTLEFT, style.FloatingPos.BOTTOM):  (4, (0,0)),
    (style.FloatingPos.OUTLEFT, style.FloatingPos.CENTER):  (7, (0,0.5)),
    (style.FloatingPos.OUTLEFT, style.FloatingPos.TOP):     (1, (0,1)),
    (style.FloatingPos.OUTRIGHT, style.FloatingPos.BOTTOM):  (3, (1,0)),
    (style.FloatingPos.OUTRIGHT, style.FloatingPos.CENTER):  (6, (1,0.5)),
    (style.FloatingPos.OUTRIGHT, style.FloatingPos.TOP):     (2, (1,1)),
    (style.FloatingPos.OUTLEFT, style.FloatingPos.OUTBOTTOM):   (1, (0,0)),
    (style.FloatingPos.OUTLEFT, style.FloatingPos.OUTTOP):      (4, (0,1)),
    (style.FloatingPos.OUTRIGHT, style.FloatingPos.OUTBOTTOM):  (2, (1,0)),
    (style.FloatingPos.OUTRIGHT, style.FloatingPos.OUTTOP):     (3, (1,1)),
}
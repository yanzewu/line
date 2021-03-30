
import numpy as np
from ..style import FloatingPos, Rect

def get_compact_figure_padding(figure):

    figure_size = figure.attr('frame')
    paddings = [0,0,0,0]
    legend_enabled = figure.legend.attr('visible') and figure.legend.attr('source')
    legend_size = figure.legend.attr('frame') if legend_enabled else Rect(0,0,0,0)
    title_h = figure.title.attr('frame').height if figure.title.attr('visible') and figure.title.attr('text') else 0

    legend_pos = figure.legend.attr('pos')  # resize only happens when it is a floating position
    if isinstance(legend_pos, tuple):
        fp = [FloatingPos.LEFT, FloatingPos.BOTTOM, FloatingPos.RIGHT, FloatingPos.TOP]
        for i in [3,1,0,2]:
            if fp[i] in legend_pos:
                paddings[i] = 10 + legend_size[2 + (i%2)]    # 0,2=>2 (width) 1,3=>3 (height)
                break

    if title_h > 0:
        if legend_pos == (FloatingPos.CENTER, FloatingPos.TOP) and legend_enabled:
            paddings[3] = figure_size.height - legend_size.bottom()
        else:
            paddings[3] = max(paddings[3], title_h)     # we don't care if they overlap

    return [
        max(paddings[0]/figure_size.width + 0.02, 0.03),    # 0.02 is MPL default
        max(paddings[1]/figure_size.height + 0.02, 0.03),
        max(paddings[2]/figure_size.width + 0.02, 0.03),
        max(paddings[3]/figure_size.height + 0.02, 0.03),  # if user want to customize, they can disable --auto-compact 
    ]


def get_compact_subfigure_padding(subfigure):
    """ Calculate and update the padding (relative to figure size) that a compact 
    subfigure should have.
    """
    subfig_size = subfigure.attr('frame')
    rsize = subfigure.attr('rsize')
    padding = subfigure.attr('padding')
    
    label_size_y, ticklabel_size_y, has_label_y, has_tick_y = _get_label_and_tick_size(subfigure, 'y')
    label_size_x, ticklabel_size_x, has_label_x, has_tick_x = _get_label_and_tick_size(subfigure, 'x')

    offset_left, offset_right = _get_outmost_ticklabel_offset(subfigure, 'x') if has_tick_x else (0, 0)
    offset_bottom, offset_top = _get_outmost_ticklabel_offset(subfigure, 'y') if has_tick_y else (0, 0)
    
    axis_left_d = subfigure.axes[1].attr('frame').width if subfigure.axes[1].attr('visible') else 0
    axis_bottom_d = subfigure.axes[0].attr('frame').height if subfigure.axes[0].attr('visible') else 0
    axis_right_d = subfigure.axes[2].attr('frame').width if subfigure.axes[2].attr('visible') else 0
    axis_top_d = subfigure.axes[3].attr('frame').height if subfigure.axes[3].attr('visible') else 0

    fig_size_h = subfig_size.width / (rsize[0] - padding[0] - padding[2])
    fig_size_v = subfig_size.height / (rsize[1] - padding[1] - padding[3])

    title_h = subfigure.title.attr('frame').top() - subfig_size.top() if subfigure.title.attr('visible') and subfigure.title.attr('text') else 0
    legend_offset = _get_legend_offset(subfigure, subfigure.legend)

    padding_left = 10 + max(offset_left, axis_left_d, legend_offset[0])
    padding_bottom = 10 + max(offset_bottom, axis_bottom_d, legend_offset[1])
    padding_right = 10 + max(offset_right, axis_right_d, legend_offset[2])
    padding_top = 10 + max(offset_top, title_h + max(axis_top_d, 0), legend_offset[3])

    return [padding_left / fig_size_h, padding_bottom / fig_size_v, 
        padding_right / fig_size_h, padding_top / fig_size_v]


def _get_label_and_tick_size(subfigure, axis):

    axis_idx = 1 if axis == 'y' else 0
    size_idx = 2 if axis == 'y' else 3

    m_tick = subfigure.axes[axis_idx].tick
    m_label = subfigure.axes[axis_idx].label

    has_label = m_label.attr('visible') and subfigure.axes[axis_idx].attr('visible')
    has_tick = m_tick.attr('visible') and subfigure.axes[axis_idx].attr('visible')
    has_ticklabel = len(subfigure.axes[axis_idx].get_style('tickpos')) > 0 and has_tick

    label_width = m_label.attr('frame')[size_idx] if has_label else 0
    ticklabel_width = max((x[size_idx] for x in m_tick.attr('frame'))) if has_ticklabel else 0

    return label_width, ticklabel_width, has_label, has_ticklabel


def _get_outmost_ticklabel_offset(subfigure, axis):
    """ direction='h' => graph.left - leftmost tick.left, rightmost tick.right - graph.right
        direction='v' => graph.bottom - bottommost tick.bottom, top tick.top - graph.top
        Both are absolute positions.
        If value is negative, return 0.
    """

    axis_idx = 0 if axis == 'x' else 1
    inner = (lambda x: x.left()) if axis == 'x' else (lambda x: x.bottom())
    outer = (lambda x: x.right()) if axis == 'x' else (lambda x: x.top())

    tick_poses = subfigure.axes[axis_idx].tick.attr('frame')
    subfig_pos = subfigure.attr('frame')

    inner_offset = 0
    outer_offset = 0
    for i in range(0, len(tick_poses)):
        if outer(tick_poses[i]) > inner(subfig_pos):
            inner_offset = max(0, inner(subfig_pos) - inner(tick_poses[i]))
            break

    for i in range(len(tick_poses)-1, -1, -1):
        if inner(tick_poses[i]) < outer(subfig_pos):
            outer_offset = max(0, outer(tick_poses[i]) - outer(subfig_pos))
            break

    return inner_offset, outer_offset


def _get_legend_offset(subfigure, legend):

    if not subfigure.legend.attr('visible'):
        return 0,0,0,0

    sf = subfigure.attr('frame')
    try:
        lf = legend.attr('frame')
    except KeyError:
        return 0,0,0,0

    return max(0, sf.left() - lf.left()), max(0, sf.bottom() - lf.bottom()), max(0, lf.right() - sf.right()), max(0, lf.top() - sf.top())

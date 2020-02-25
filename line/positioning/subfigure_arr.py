
import numpy as np


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
    
    fig_size_h = subfig_size.width / (rsize[0] - padding[0] - padding[2])
    fig_size_v = subfig_size.height / (rsize[1] - padding[1] - padding[3])

    padding_left = 10 + max(offset_left, subfigure.axes[1].attr('frame').width)
    padding_bottom = 10 + max(offset_bottom, subfigure.axes[0].attr('frame').height)
    padding_right = 10 + offset_right
    padding_top = 10 + offset_top

    # TODO add title and legend

    return (padding_left / fig_size_h, padding_bottom / fig_size_v, 
        padding_right / fig_size_h, padding_top / fig_size_v)


def _get_label_and_tick_size(subfigure, axis):

    axis_idx = 1 if axis == 'y' else 0
    size_idx = 2 if axis == 'y' else 3

    m_tick = subfigure.axes[axis_idx].tick
    m_label = subfigure.axes[axis_idx].label

    has_label = m_label.attr('visible')
    has_tick = m_tick.attr('visible')
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

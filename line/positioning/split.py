
import math
import numpy as np
import itertools

from . import errors
from ..element import subfigure


def split_figure(figure, hsplitnum:int, vsplitnum:int, resize_figure=True):
    """ Split current figure by certain grids.
    Will remove additional subfigures if necessary.
    """

    if hsplitnum < 1 or vsplitnum < 1:
        raise errors.LineProcessError('Split number should be greater than 1, got %d' % max(hsplitnum, vsplitnum))

    hsplit, vsplit = figure.attr('split')
    hspacing, vspacing = figure.attr('spacing')

    subfig_state_2d = []
    for i in range(vsplitnum):
        subfig_state_2d.append([])
        for j in range(hsplitnum):
            subfig_name = 'subfigure%d' % (i*hsplitnum + j)
            if i < vsplit and j < hsplit:
                subfig_state_2d[i].append(figure.subfigures[i*hsplit + j])
                subfig_state_2d[i][-1].name = subfig_name
            else:
                subfig_state_2d[i].append(subfigure.Subfigure(subfig_name))
    
    figure.subfigures = list(itertools.chain.from_iterable(subfig_state_2d))
    figure.is_changed = True
    
    if resize_figure:
        split_old = figure.get_style('split')
        size_old = figure.get_style('size')
        figure.update_style({'size': [
            round(size_old[0]*math.sqrt(hsplitnum/split_old[0] * split_old[1]/vsplitnum)), 
            round(size_old[1]*math.sqrt(vsplitnum/split_old[1] * split_old[0]/hsplitnum))]
            })

    figure.update_style({'split': [hsplitnum, vsplitnum]})
    if figure.cur_subfigure >= len(figure.subfigures):
        figure.cur_subfigure = 0


def align_subfigures(figure, alignment='axis'):
    hsplitnum, vsplitnum = figure.attr('split')
    hspacing, vspacing = figure.attr('spacing')

    if alignment == 'axis':
        poses, sizes = get_alignment_by_axis(figure.subfigures, hsplitnum, vsplitnum, hspacing, vspacing)
    elif alignment == 'subfigure':
        poses, sizes = get_alignment_by_subfigure(hsplitnum, vsplitnum, hspacing, vspacing)
    else:
        raise ValueError(alignment)
    
    for p, s, sf in zip(poses, sizes, figure.subfigures):
        sf.update_style({'rpos': p, 'rsize': s})

    figure.is_changed = True


def get_alignment_by_subfigure(hsplitnum, vsplitnum, hspacing, vspacing):
    """ Evenly distribute the subfigure size. Align them by subfigure border.
    """

    poses = []
    sizes = []

    for i in range(vsplitnum):
        for j in range(hsplitnum):
            poses.append((
                j * (1 + hspacing) / hsplitnum,
                (vsplitnum - 1 - i) * (1 + vspacing) / vsplitnum
                ))
            sizes.append((
                1 / hsplitnum -  (1 - 1/hsplitnum) * hspacing,
                1 / vsplitnum - (1 - 1/vsplitnum) * vspacing
            ))
    return poses, sizes


def get_alignment_by_axis(subfigures, hsplitnum, vsplitnum, hspacing, vspacing):
    """ Evenly distribute the subfigure size. Align them by axis border.
    """

    paddings = []

    for subfigure in subfigures:
        paddings.append(subfigure.attr('padding'))
    
    loc = lambda x, y: (vsplitnum-1-y)*hsplitnum + x

    spacings_h = [0] * (hsplitnum + 1)
    spacings_v = [0] * (vsplitnum + 1)
    
    for x in range(1, hsplitnum):
        spacings_h[x] = hspacing + max((
            paddings[loc(x-1,y)][2] + paddings[loc(x,y)][0] for y in range(vsplitnum)))

    for y in range(1, vsplitnum):
        spacings_v[y] = vspacing + max((
            paddings[loc(x,y-1)][3] + paddings[loc(x,y)][1] for x in range(hsplitnum)))

    spacings_h[0] = max((paddings[loc(0,y)][0] for y in range(vsplitnum)))
    spacings_h[-1] = max((paddings[loc(hsplitnum-1,y)][2] for y in range(vsplitnum)))
    spacings_v[0] = max((paddings[loc(x,0)][1] for x in range(hsplitnum)))
    spacings_v[-1] = max((paddings[loc(x,vsplitnum-1)][3] for x in range(hsplitnum)))

    axis_size_h = (1 - sum(spacings_h)) / hsplitnum
    axis_size_v = (1 - sum(spacings_v)) / vsplitnum

    axis_poses_h = np.cumsum(spacings_h) + np.arange(hsplitnum+1) * axis_size_h
    axis_poses_v = np.cumsum(spacings_v) + np.arange(vsplitnum+1) * axis_size_v

    poses = [0] * (hsplitnum*vsplitnum)
    sizes = [0] * (hsplitnum*vsplitnum)

    for x in range(hsplitnum):
        for y in range(vsplitnum):
            n = loc(x, y)
            poses[n] = (axis_poses_h[x] - paddings[n][0], axis_poses_v[y] - paddings[n][1])
            sizes[n] = (axis_size_h + paddings[n][0] + paddings[n][2], 
                axis_size_v + paddings[n][1] + paddings[n][3])
            
    return poses, sizes

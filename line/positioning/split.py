
import math
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

            subfig_state_2d[i][j].update_style({'rpos': (
                j * (1 + hspacing) / hsplitnum,
                (vsplitnum - 1 - i) * (1 + vspacing) / vsplitnum
                ), 
                'rsize': (
                1 / hsplitnum -  (1 - 1/hsplitnum) * hspacing,
                1 / vsplitnum - (1 - 1/vsplitnum) * vspacing
            )})
    
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
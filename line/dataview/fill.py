

import numpy as np
from . import datapack


def fill_h(m_state, dp1:datapack.DataPack, dp2=0, **kwargs):
    """ Fill horizontally. dp1 must be DataPack;
         dp2 can be DataPack or number.
         kwargs will be passed to add_polygon()
    """

    subfig = m_state.cur_subfigure()

    return subfig.add_polygon(_fill_polygon(dp1, dp2), **kwargs)


def _fill_polygon(dp1, dp2):
    if isinstance(dp2, datapack.DataPack):
        return datapack.StaticPairedDataPack(
            np.concatenate((dp1.get_x(), np.flip(dp2.get_x()))), 
            np.concatenate((dp1.get_y(), np.flip(dp2.get_y())))
            )

    else:
        return datapack.StaticPairedDataPack(
            np.concatenate((dp1.get_x(), np.flip(dp1.get_x()))), 
            np.concatenate((dp1.get_y(), np.ones_like(dp1.get_x()) * dp2))
            )

def fill_betweenobj(m_state, obj1, obj2=None, **kwargs):
    """ Fill the space between two lines, or line + horizontol axis
    """

    if obj2 is None:
        return fill_h(m_state, obj1.data, **kwargs)
    elif isinstance(obj2, (int, float)):
        return fill_h(m_state, obj1.data, obj2, **kwargs)
    else:
        return fill_h(m_state, obj1.data, obj2.data, **kwargs)  

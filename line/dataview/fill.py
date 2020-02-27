

import numpy as np
from . import datapack


def fill_h(m_state, dp1:datapack.DataPack, dp2, **kwargs):
    """ Fill horizontally. dp1 must be DataPack;
         dp2 can be DataPack or number.
         kwargs will be passed to add_polygon()
    """

    subfig = m_state.cur_subfigure()

    if dp2 is None:
        dp2 = subfig.axes[1].get_style('range')[0]

    subfig.add_polygon(_fill_polygon(dp1, dp2), kwargs)


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

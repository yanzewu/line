
import numpy as np

from . import datapack


def _buildpolyfunc(coeffs):

    return lambda x: np.polyval(coeffs, x)
        

def polyfit(dp:datapack.DataPack, deg, residual=False):

    if not residual:
        p = np.polyfit(dp.get_x(), dp.get_y(), deg)
        return _buildpolyfunc(p)
    else:
        ret = np.polyfit(dp.get_x(), dp.get_y(), deg, full=True)
        p = ret[0]
        r = 0 if ret[1].size == 0 else ret[1][0]
        return _buildpolyfunc(p), r


def linearfit(dp:datapack.DataPack, intercept=None, residual=False):

    if not intercept:
        return polyfit(dp, 1, residual=residual)
    else:
        pass



def add_fitline(subfigure, fittedfunc, range_=None, xlabel='', ylabel='', **kwargs):
    """ Add a new line to the subfigure which is considered as 'fit'.
    """
    
    if range_ is None:
        xr = subfigure.get_style('xrange')
        step_ = xr[2] if xr[2] else (xr[1] - xr[0])/100
        range_ = np.arange(xr[0], xr[1] + step_, step_)

    return subfigure.add_smartdataline(
        datapack.EvaluatableDataPack(fittedfunc, range_), ylabel, xlabel, kwargs
    )


def fit_dataline(subfigure, dataline, function='linear', range_=None, labelfmt='Fit %T', **kwargs):
    """ Generate a fitted dataline instance in subfigure.
    Args:
        subfigure: `Subfigure' instance;
        dataline: `DataLine' or `Bar' instance (which has `.data.get_x()', and `.data.get_y()');
        function: `linear', 'quad'
        range_: array-like object to determine x; if `None', use current subfigure width;
        labelfmt: Format for auto-generated label. Special formats are:
            '%T' to represent original data title;
            '%N' to represent the name;
    Kwargs:
        Passed to the style of fitted line.
    """ # TODO support self-defined function

    func = {'linear': linearfit, 'quad':lambda x:polyfit(x, 2)}.get(function, None)
    if not func:
        raise ValueError(function)

    xlabel = dataline.get_style('xlabel')
    ylabel = labelfmt.replace('%T', dataline.get_style('label')).replace('%N', dataline.name)

    fitresult = func(dataline.data)

    return add_fitline(subfigure, fitresult, range_, xlabel, ylabel, **kwargs)


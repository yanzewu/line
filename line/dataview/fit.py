
import numpy as np

from . import datapack


class NamedCallable:

    def __init__(self, func, name=''):
        self.func = func
        self.name = name

    def __call__(self, *args):
        return self.func(*args)


def _buildpolyfunc(coeffs):

    pow2str = lambda i: '' if i == 0 else ('x' if i == 1 else 'x^%d' % i)
    coeff2str = lambda i: '%.4g' % coeffs[i] if i == 0 else '%+.4g' % coeffs[i]

    return NamedCallable(
        lambda x: np.polyval(coeffs, x), 
        ''.join(('%s%s' % (coeff2str(j), pow2str(len(coeffs)-j)) for j in range(len(coeffs)))))
        

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

    if intercept is None:
        return polyfit(dp, 1, residual=residual)
    else:
        return customfit(dp, lambda x, a: a*x + intercept, residual=residual)


def expfit(dp:datapack.DataPack, weighted=False, absolute=False, residual=False):
    y = dp.get_y() if not absolute else np.abs(dp.get_y())
    ret = np.polyfit(dp.get_x(), np.log(y), 1, w=None if not weighted else np.sqrt(y), full=True)
    p, r = ret[0], ret[1]
    f = NamedCallable(lambda x: np.exp(p[1] + p[0]*x), '%.4ge^{%.4gx}' % (np.exp(p[1]), p[0]))

    if not residual:    
        return f
    else:
        return f, r[0]


def customfit(dp:datapack.DataPack, function, p0=None, residual=False):
    
    import scipy.optimize

    param, _ = scipy.optimize.curve_fit(function, dp.get_x(), dp.get_y(), p0)

    fun = NamedCallable(lambda x: function(x, *param), '<expr>')
    if residual:
        y = dp.get_y()
        yt = fun(dp.get_x())
        return fun, 1.0 - np.sum((y-yt)**2)/np.sum((y-np.mean(y))**2)
    else:
        return fun


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
        function: `linear', 'quad', 'exp', 'prop', or callable object for `scipy.optimize.curve_fit()'
        range_: array-like object to determine x; if `None', use current subfigure width;
        labelfmt: Format for auto-generated label. Special formats are:
            '%T' to represent original data title;
            '%N' to represent the name;
    Kwargs:
        Passed to the style of fitted line.
    """

    if isinstance(function, str):
        func = {
            'linear': linearfit, 
            'quad':lambda x:polyfit(x, 2), 
            'exp':expfit, 
            'prop':lambda x: linearfit(x, 0),
            }.get(function, None)
    else:
        func = lambda x: customfit(x, function)
            
    if not func:
        raise ValueError(function)

    fitresult = func(dataline.data)

    xlabel = dataline.get_style('xlabel')
    ylabel = labelfmt.replace('%T', dataline.get_style('label')).replace('%N', dataline.name).replace(r'%E', fitresult.name)

    return add_fitline(subfigure, fitresult, range_, xlabel, ylabel, **kwargs)


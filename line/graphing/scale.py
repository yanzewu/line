
import numpy as np

def get_ticks(vmin, vmax, vstep=None, numticks=4):
    """ Get linear tick positions.
    If `vstep' is set, use vmin:vstep:vmax;
    Otherwise try to match `numticks'.
    """

    if vstep:
        return np.arange(vmin, vmax + vstep/10, vstep)

    else:
        return _get_ticks_by_num(vmin, vmax, numticks)


def _get_ticks_by_num(vmin, vmax, numticks):
    
    from matplotlib.ticker import MaxNLocator
    locator = MaxNLocator(nbins=numticks, steps=[1,1.5,2,2.5,3,4,5,6,7.5,8,10], prune=None)
    return locator.tick_values(vmin, vmax)
    

def get_ticks_log(vmin, vmax, numticks=None, extend='outer'):
    """ extend: how the min/max poses defined. 
            'outer': will try to extend it outwards (make min<vmin, max>vmax);
            'inner': will try to shrink it inwards;
    """

    from math import log10, ceil, floor
    from matplotlib.ticker import LogLocator

    if vmax > 0:
        vmin = max(vmin, min(10**int(log10(vmax/10)-1), 1e-3))
    else:
        vmax = 1.0
        vmin = 0.1

    if not numticks:
        numticks = 5

    if extend == 'outer':
        lvmin, lvmax = ceil(log10(vmin)), floor(log10(vmax))
    elif extend == 'inner':
        lvmin, lvmax = floor(log10(vmin)), ceil(log10(vmax))

    n = lvmax - lvmin
    stepm = max(1, floor(n/numticks))
    if n - stepm * numticks < (stepm+1)*numticks - n:
        step = stepm
    else:
        step = stepm+1

    ticks = 10.0**np.arange(lvmin, lvmax, step)   
    return ticks

    # The default scaling algorithm of MPL, not used

    subs = np.arange(int(10/numticks), 10, int(10/numticks), dtype=int) if numticks else (1.0,)
    locator = LogLocator(subs=subs)
    return [t for t in locator.tick_values(vmin, vmax) if t > vmin/10 and t < vmax*10]
    

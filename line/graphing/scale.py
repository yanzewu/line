
import numpy as np

class AxisRange:
    def __init__(self, vmin, vmax, vinterval, tickpos:np.ndarray, is_default_tickpos=True):
        self.vmin = vmin
        self.vmax = vmax
        self.vinterval = vinterval
        self.tickpos = tickpos
        self.is_default_tickpos = is_default_tickpos

    def __eq__(self, other):
        if isinstance(other, AxisRange):
            if self.is_default_tickpos and other.is_default_tickpos:
                return self.vmin == other.vmin and self.vmax == other.vmax and \
                    self.vinterval == other.vinterval
            elif not self.is_default_tickpos and not other.is_default_tickpos:
                return self.vmin == other.vmin and self.vmax == other.vmax and \
                    self.vinterval == other.vinterval and (self.tickpos == other.tickpos).all()
            else:
                return False
        else:
            return False

    def __getitem__(self, idx):
        return (self.vmin, self.vmax, self.vinterval, self.tickpos)[idx]

    def __iter__(self):
        return iter((self.vmin, self.vmax, self.vinterval, self.tickpos))

    def __str__(self):
        return 'AxisRange(range=%s:%s:%s, ticks=%s, default=%s)' % (self.vmin, self.vinterval, self.vmax, self.tickpos, self.is_default_tickpos)


def make_range(vmin, vmax, tickpos):
    return AxisRange(vmin, vmax, None, np.array(tickpos), False)
    

def compute_range_and_tickpos(vmin, vmax, vinterval, align_bound=(False, False), scale='linear'):
    """ compute tick pos accroding to (vmin, vmax, vinterval).
    align_bound is a tuple (left, right): Will set the corresponding boundary to the minimum/maximum of the tick positions.
    """

    # TODO minpos, maxpos are not always vmin, vmax; they may have some padding around data.
    bound = [None, None]

    if scale == 'linear':
        tickpos = get_ticks(vmin, vmax, vinterval)
        return AxisRange(tickpos[0] if align_bound[0] else vmin, tickpos[-1] if align_bound[1] else vmax, tickpos[1] - tickpos[0], tickpos)
        
    elif scale == 'log':
        numticks = int(1.0/vinterval) if vinterval else None
        tickpos = get_ticks_log(vmin, vmax, numticks)
        return AxisRange(tickpos[0] if align_bound[0] else vmin, tickpos[-1] if align_bound[1] else vmax, 1.0/numticks if numticks else None, tickpos)
    else:
        raise ValueError("scale should be linear/log")


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

    if vmax <= 0:
        vmax = 1.0
        vmin = 0.1
    elif vmax > 0 and vmin <= 0:
        vmin = max(vmin, min(10**int(log10(vmax/10)-1), 1e-3))

    if not numticks:
        numticks = 5

    if extend == 'inner':
        lvmin, lvmax = ceil(log10(vmin)), floor(log10(vmax))
    elif extend == 'outer':
        lvmin, lvmax = floor(log10(vmin)), ceil(log10(vmax))
    if lvmin == lvmax:
        lvmax = lvmin + 1

    n = lvmax - lvmin
    stepm = max(1, floor(n/numticks))
    if n - stepm * numticks < (stepm+1)*numticks - n:
        step = stepm
    else:
        step = stepm+1

    ticks = 10.0**np.arange(lvmin, lvmax+0.1, step)   
    return ticks

    # The default scaling algorithm of MPL, not used

    subs = np.arange(int(10/numticks), 10, int(10/numticks), dtype=int) if numticks else (1.0,)
    locator = LogLocator(subs=subs)
    return [t for t in locator.tick_values(vmin, vmax) if t > vmin/10 and t < vmax*10]
    

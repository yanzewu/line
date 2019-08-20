

def get_ticks(vmin, vmax):
    
    from matplotlib.ticker import MaxNLocator
    locator = MaxNLocator(nbins=4, steps=[1,1.5,2,2.5,3,4,5,6,7.5,8,10], prune=None)
    return locator.tick_values(vmin, vmax)
    
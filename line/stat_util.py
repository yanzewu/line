
import numpy as np

    
def histogram(mat, bins=10, norm='pdf'):

    h, e = np.histogram(np.array(mat).flatten(), bins, density=False)
    if norm in ('Density', 'density', 'PDF', 'pdf', 'Distribution', 'distribution'):
        h = h / np.sum(h) / (e[1]-e[0])
    elif norm in ('Probability', 'probability', 'Prob', 'prob'):
        h = h / np.sum(h)

    e = e[1:] - (e[1]-e[0])/2
    return np.hstack((e[:, None], h[:, None]))

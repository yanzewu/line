
import collections
import numpy as np

from . import state
from . import defaults
from . import backend as _plot
from . import process

m_state = None

def init_m_state():

    global m_state

    m_state = state.GlobalState()
    defaults.init_global_state(m_state)
    m_state.is_interactive = False

    process.initialize()


def figure(name=None):

    _process_command(['figure'] if not name else ['figure', str(name)])
    return m_state.cur_figure()
    

def subfigure(*arg):
    
    if len(arg) == 1:
        _process_command(['subfigure', str(arg[0])])
    elif len(arg) == 3:
        _process_command(['subfigure', str(arg[0]), ',', str(arg[1]), ',', str(arg[2])])
    else:
        raise ValueError(arg)
    return m_state.cur_subfigure()


def plot(x, y, *args, **kwargs):
    if not m_state:
        init_m_state()
    m_state.variables['__varmx'] = np.array(x)
    m_state.variables['__varmy'] = np.array(y)

    _args = ['plot', '$mx', ':', '$my'] + list(map(str, args))
    for k, d in kwargs.items():
        _args += [k, '=', str(d)]

    _process_command(_args)
    return m_state.cur_subfigure().datalines[-1]

def show():
    if not m_state:
        return
    _plot.initialize(m_state)
    m_state.refresh_style(True)
    process.process_display(m_state)
    _plot.finalize(m_state)


def gcf():
    return m_state.cur_figure(True)


def gca():
    return m_state.cur_subfigure(True)


def load_file(filename, *args, **kwargs):
    from . import sheet_util

    return sheet_util.load_file(filename, *args, **kwargs)

def _process_command(command):

    if not m_state:
        init_m_state()

    process.parse_and_process_command(collections.deque(command), m_state)


import collections as _collections

from . import backend as _plot
from . import process as _process

_m_state = None


def _init_state():

    from . import state
    from . import defaults

    global _m_state

    _m_state = state.GlobalState()
    defaults.init_global_state(_m_state)
    _m_state.is_interactive = False
    _process.initialize()

    if defaults.default_options['remote']:
        from . import remote
        remote.start_application(defaults.default_options['port'])


def _get_state():
    if _m_state is None:
        _init_state()
    
    return _m_state


def _process_command(command):
    _process.parse_and_process_command(_collections.deque(command), _get_state())


def figure(name=None):
    return _get_state().figure(name)


def subfigure(*arg):
    
    if len(arg) == 1:
        _process_command(['subfigure', str(arg[0])])
    elif len(arg) == 3:
        _process_command(['subfigure', str(arg[0]), ',', str(arg[1]), ',', str(arg[2])])
    else:
        raise ValueError(arg)
    return _m_state.cur_subfigure()

subplot = subfigure

def plot(*args, **kwargs):
    """ Plot a new set of data.
    Args:
        x, y (at least one or both): Array-like object;
        style_descriptor: Matlab-style descriptor, e.g. 'r-';
    Kwargs: Style args for `DataLine'.

    Returns:
        `element.DataLine' instance.
    """
    from . import dataview

    return dataview.api.plot_line(_get_state(), *args, **kwargs)


def bar(*args, **kwargs):

    from . import dataview

    return dataview.api.plot_bar(_get_state(), *args, **kwargs)


def hist(*args, **kwargs):

    from . import dataview

    return dataview.api.plot_hist(_get_state(), *args, **kwargs)


def fill(*args, **kwargs):

    from . import dataview

    return dataview.api.fill_h(_get_state(), *args, **kwargs)
    

def line(target1, target2, **kwargs):
    _get_state().cur_subfigure(True).add_drawline(target1, target2, kwargs)


def xline(x, **kwargs):
    _get_state().cur_subfigure(True).add_drawline((x, None), (x, None), kwargs)


def yline(y, **kwargs):
    _get_state().cur_subfigure(True).add_drawline((None, y), (None, y), kwargs)


def text(txt, pos, **kwargs):
    from . import style

    _get_state().cur_subfigure(True).add_text(
        txt, style.str2pos(pos) if isinstance(pos, str) else pos, **kwargs)

def legend(labels=None, **kwargs):
    if labels is None:
        _m_state.gca().legend.update_style(visible=not _m_state.gca().legend.get_style('visible'))
    else:
        _m_state.gca().update_style(legend=labels)
    _m_state.gca().legend.update_style(**kwargs)
    return _m_state.gca().legend

def show():
    if not _m_state:
        return
    _plot.initialize(_m_state)
    _m_state.refresh_style(True)
    _process.process_display(_m_state)
    _plot.finalize(_m_state)


def gcf():
    return _m_state.gcf(True)


def gca():
    return _m_state.gca(True)


def clear():
    _m_state.gca().clear()


def cla():
    clear()


def save(filename):
    _process.process_save(_get_state(), filename)


def load_file(filename, *args, **kwargs):
    from . import model

    return model.load_file(filename, *args, **kwargs)

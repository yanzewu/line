
import collections as _collections

from . import backend as _plot
from . import process as _process
from . import style
from . import keywords
from . import proc_api

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

def _translate_style(kwargs):
    return dict(((keywords.style_alias.get(s, s), v) for s, v in kwargs.items()))

# Figure/subfigure management

def figure(name=None):
    return _get_state().figure(name)


def subfigure(*args):
    return proc_api.subfigure(_get_state(), *args)

subplot = subfigure

def gcf():
    return _m_state.gcf(True)


def gca():
    return _m_state.gca(True)

def remove_figure(name):
    return _get_state().remove_figure(name)

def get_element(name, multiple=False):
    return _get_state().get_element_by_name(name, multiple=multiple)

def get(obj, *args):

    if args:
        return [obj.get_style(keywords.style_alias.get(a, a)) for a in args]
    else:
        return obj.export_styles()

getp = get

def setp(obj, **kwargs):
    from . import element
    assert isinstance(obj, element.FigObject), "Figobject required"

    obj.update_style(_translate_style(kwargs))

# Plotting

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
    return dataview.api.plot_line(_get_state(), *args, **_translate_style(kwargs))


def bar(*args, **kwargs):
    from . import dataview
    return dataview.api.plot_bar(_get_state(), *args, **_translate_style(kwargs))


def hist(*args, **kwargs):
    from . import dataview
    return dataview.api.plot_hist(_get_state(), *args, **_translate_style(kwargs))


def fill(*args, **kwargs):
    from . import dataview
    return dataview.api.fill(_get_state(), *args, **_translate_style(kwargs))
    
area = fill

def fill_between(*args, **kwargs):
    from . import dataview
    return dataview.api.fill_between(_get_state(), *args, **_translate_style(kwargs))
    
def fill_betweenx(*args, **kwargs):
    from . import dataview
    return dataview.api.fill_betweenx(_get_state(), *args, **_translate_style(kwargs))


def line(target1, target2, **kwargs):
    return proc_api.line(_get_state(), startpos=target1, endpos=target2, style_dict=_translate_style(kwargs))

def hlines(y, xmin, xmax, **kwargs):
    """ 
    """
    return [line((xmin, y_), (xmax, y_), **kwargs) for y_ in y]

def vlines(x, ymin, ymax, **kwargs):
    """ 
    """
    return [line((x_, ymin), (x_, ymax), **kwargs) for x_ in x]

def xline(x, **kwargs):
    return line((x, None), (x, None), **kwargs)

axhline = xline

def yline(y, **kwargs):
    return line((None, y), (None, y), **kwargs)

axvline = yline

def text(txt, pos, **kwargs):
    return proc_api.text(_get_state(), text=txt, pos=pos, style_dict=_translate_style(kwargs))

# Other element management

def xlabel(text:str, **kwargs):
    _m_state.gca().axes[0].label.update_style(text=text, **_translate_style(kwargs))

def ylabel(text:str, **kwargs):
    _m_state.gca().axes[1].label.update_style(text=text, **_translate_style(kwargs))

def _set_lim(axis, *args, **kwargs):
    if kwargs:
        v0 = kwargs.get('left', None)
        v1 = kwargs.get('right', None)
    elif len(args) == 1:
        assert len(args[0]) == 2, "Expect a list"
        v0, v1 = args[0]
    elif len(args) == 2:
        v0, v1 = args
    else:
        raise ValueError("Invalid args")
    _get_state().gca().axes[axis].update_style(range=(v0, v1, kwargs.get('step', None)))
    
def xlim(*args, **kwargs):
    _set_lim(0, *args, **kwargs)

def ylim(*args, **kwargs):
    _set_lim(1, *args, **kwargs)

def xscale(value):
    _m_state.gca().axes[0].update_style(scale=value)

def yscale(value):
    _m_state.gca().axes[1].update_style(scale=value)

def tick_params(axis='both', **kwargs):
    axis_idx = {'x':(0,), 'y':(1,), 'both':(0, 1)}[axis]
    if kwargs:
        for a in axis_idx:
            _m_state.gca().axes[a].tick.update_style(_translate_style(kwargs))
    else:
        if len(axis_idx) == 2:
            return [_m_state.gca().axes[a].tick.export_style() for a in axis]
        else:
            return _m_state.gca().axes[axis[0]].tick.export_style()


def legend(labels=None, **kwargs):
    if labels is None:
        _m_state.gca().legend.update_style(visible=not _m_state.gca().legend.get_style('visible'))
    else:
        _m_state.gca().update_style(legend=labels, visible=True)
    _m_state.gca().legend.update_style(_translate_style(kwargs))
    return _m_state.gca().legend

def title(text:str, **kwargs):
    _m_state.gca().title.update_style(text=text, **_translate_style(kwargs))

def suptitle(text:str, **kwargs):
    _m_state.gcf().title.update_style(text=text, **_translate_style(kwargs))

def grid(on:bool=True, axis:str='both', **kwargs):
    axis_idx = {'x':(0,), 'y':(1,), 'both':(0, 1)}[axis]
    for a in axis_idx:
        _m_state.gca().axes[a].grid.update_style(visible=bool(on), **_translate_style(kwargs))

def group(group_desc:str):
    from . import group_proc
    _get_state().gca().update_style(group=group_proc.parse_group(group_desc))
    _get_state().refresh_style()


def palette(palette_name:str, target:str='line', target_style:str='color'):
    return proc_api.palette(_get_state(), palette_name, target, target_style)

set_cmap = palette

def clear():
    _m_state.gca().clear()

cla = clear


# IO

def draw():
    if not _m_state:
        return
    proc_api.set_redraw(_m_state, compact=_m_state.options['auto-compact'])
    _process.render_cur_figure(_m_state)

def show():
    if not _m_state:
        return
    _plot.initialize(_m_state)
    _m_state.refresh_style(True)
    _process.process_display(_m_state)
    _plot.finalize(_m_state)


def save(filename):
    draw()
    _plot.save_figure(_m_state, filename)
    _m_state.cur_save_filename = filename

savefig = save

def load_file(filename, *args, **kwargs):
    from . import model

    return model.load_file(filename, *args, **kwargs)

def pause(interval):
    from time import sleep
    sleep(interval)

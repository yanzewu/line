
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

def figure(name=None, **kwargs):
    """ Create or switch to a figure.

    Kwargs: Will be passed to figure styles.
    """
    return _get_state().figure(name, **kwargs)


def subfigure(*args, **kwargs):
    """ Switch to a subfigure, will split current figure if necessary.

    Usage:
    - subfig (idx) => set current subfigure to idx
    - subfig (a, b, idx) => split, set current subfigure to idx
    - subfig (desc) => same as (a, b, idx). e.g., subfigure (111) is same as subfigure (1, 1, 1)
    """
    return proc_api.subfigure(_get_state(), *args, **kwargs)

subplot = subfigure

def gcf():
    """ Get current Figure instance. Create one if no figure exists.
    """
    return _m_state.gcf(True)


def gca():
    """ Get current Subfigure instance. Create one if no figure exists.
    """
    return _m_state.gca(True)

def remove_figure(name):
    """ Remove a figure.
    """
    return _get_state().remove_figure(name)

def get_element(name, multiple=False):
    """ Get element by name. If `multiple` is set, return all that matches, otherwise return one of them.
    """
    return _get_state().get_element_by_name(name, multiple=multiple)

def get(obj, *args):
    """ Get properties from a certain element. Nearly equivalent to `object.get_style()` after style aliasing.

    args: list of style names (string). If set, only return certain styles as a list, 
        otherwise return all styles as a dict {name:value}.
    """
    if args:
        return [obj.get_style(keywords.style_alias.get(a, a)) for a in args]
    else:
        return obj.export_styles()

getp = get

def setp(obj, **kwargs):
    """ Set properties of a certain element. Equivalent to `obj.update_style(kwargs)` after style aliasing.
    """
    from . import element
    assert isinstance(obj, element.FigObject), "Figobject required"

    obj.update_style(_translate_style(kwargs))

# Plotting

def plot(*args, **kwargs):
    """ Plot a new set of data.
    Usage:
        `plot(x, y)`
        `plot(y)`
        `plot(..., style_descriptor)`
        `plot(..., style=value, ...)`
    Args:
        x, y (at least one or both): Array-like object. If x is omitted, will be 1 ... len(y).
        style_descriptor: Matlab-style descriptor, e.g. 'r-';
    Kwargs: Style args for `DataLine'.

    Returns:
        `element.DataLine' instance.
    """
    from . import dataview
    return dataview.api.plot_line(_get_state(), *args, **_translate_style(kwargs))


def bar(*args, **kwargs):
    """ Plot data as bar graph.
    Usage:
        `bar(x, y)`
        `bar(y)`
        `bar(..., style=value, ...)`
    Args:
        x, y (at least one or both): Array-like object. If x is omitted, will be 1 ... len(y).
    Kwargs: Style args for `Bar'.

    Returns:
        `element.Bar' instance.
    """
    from . import dataview
    return dataview.api.plot_bar(_get_state(), *args, **_translate_style(kwargs))


def hist(*args, **kwargs):
    """ Plot histogram.
    Usage:
        `hist(y)`
        `hist(..., style=value, ...)`
    Args:
        y: Array-like object. The data.
    Kwargs: Style args for `Bar'.
        bin: Interval of histogram.
        norm: can be 'density' (normed by density) or 'probability' (normed by divided by total number).
    Returns:
        `element.Bar' instance.
    """
    from . import dataview
    return dataview.api.plot_hist(_get_state(), *args, **_translate_style(kwargs))


def fill(*args, **kwargs):
    """ Fill set of region (i.e. create a polygon).
    Usage:
        `fill(x, y)`
        `fill(..., style=value, ...)`
    Args:
        x, y: Coordinates of verticies.
    Kwargs:
        Style args for `Polygon`.
    Returns:
        `element.Polygon` instance.
    """
    from . import dataview
    return dataview.api.fill(_get_state(), *args, **_translate_style(kwargs))
    
area = fill

def fill_between(*args, **kwargs):
    """ Fill a region where vertices share x values.
    Usage:
        `fill_between(x, y1)`
        `fill_between(x, y1, y2)`
        `fill_between(..., style=value, ...)`
    Args:
        x: x coordinates.
        y1: the first set of y coordinates, or a single number.
        y2: the second set of y coordinates, or a single number (default = 0).
    Kwargs:
        Style args for `Polygon`.
    Returns:
        `element.Polygon` instance.
    """
    from . import dataview
    return dataview.api.fill_between(_get_state(), *args, **_translate_style(kwargs))
    
def fill_betweenx(*args, **kwargs):
    """ Fill a region where vertices share y values.
    Usage:
        `fill_between(y, x1)`
        `fill_between(y, x1, x2)`
        `fill_between(..., style=value, ...)`
    Args:
        y: y coordinates.
        x1: the first set of x coordinates, or a single number.
        x2: the second set of x coordinates, or a single number (default = 0).
    Kwargs:
        Style args for `Polygon`.
    Returns:
        `element.Polygon` instance.
    """
    from . import dataview
    return dataview.api.fill_betweenx(_get_state(), *args, **_translate_style(kwargs))


def line(target1, target2, **kwargs):
    """ Draw a line from position target1 to position target2 in axis coordinate.

    Args:
        target1, target2: tuple/list/array of two float numbers.
    Kwargs:
        Style args for `DrawLine`.
    Returns:
        `element.DrawLine` instance.
    """
    return proc_api.line(_get_state(), startpos=target1, endpos=target2, style_dict=_translate_style(kwargs))

def hlines(y, xmin, xmax, **kwargs):
    """ Draw a series horitonzal lines from different y. Equivalent to `[line((xmin, y1), (xmax, y1)) for y1 in y]`
    """
    return [line((xmin, y_), (xmax, y_), **kwargs) for y_ in y]

def vlines(x, ymin, ymax, **kwargs):
    """ Draw a series vertical lines from different y. Equivalent to `[line((x1, ymin), (x1, ymax)) for x1 in x]`
    """
    return [line((x_, ymin), (x_, ymax), **kwargs) for x_ in x]

def xline(x, **kwargs):
    """ Draw a vertical line extends to coordinate boundary.
    """
    return line((x, None), (x, None), **kwargs)

axhline = xline

def yline(y, **kwargs):
    """ Draw a horizontal line extends to coordinate boundary.
    """
    return line((None, y), (None, y), **kwargs)

axvline = yline

def text(content, pos, **kwargs):
    """ Plot text.
    Args:
        content: Content of the text.
        pos: position descriptor in current subfigure (e.g. 'top,left', 'top,center'). Available choices are:
            top, center, bottom, left, right.
    Kwargs:
        Style args for `Text`.
    Returns:
        `element.Text` instance.
    """
    return proc_api.text(_get_state(), text=content, pos=pos, style_dict=_translate_style(kwargs))

# Other element management

def xlabel(text:str, **kwargs):
    """ Set xlabel. Additional args will be passed to style properties.
    """
    _m_state.gca().axes[0].label.update_style(text=text, **_translate_style(kwargs))

def ylabel(text:str, **kwargs):
    """ Set ylabel. Additional args will be passed to style properties.
    """
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
    """ Set range of x coord. Can be called as `xlim(a, b)`, `xlim([a, b])`, `xlim(left=a)` or `xlim(right=b)`.
    Additional args will be passed to style properties.

    If one of or both range parameters (a, b) are None, that bound will be automatically determined from data.
    """
    _set_lim(0, *args, **kwargs)

def ylim(*args, **kwargs):
    """ Set range of y coord. Can be called as `ylim(a, b)`, `ylim([a, b])`, `ylim(left=a)` or `ylim(right=b)`.
    Additional args will be passed to style properties.

    If one of or both range parameters (a, b) are None, that bound will be automatically determined from data.
    """
    _set_lim(1, *args, **kwargs)

def xscale(value):
    """ Set scale of xaxis. value can be 'linear' or 'log'.
    """
    _m_state.gca().axes[0].update_style(scale=value)

def yscale(value):
    """ Set scale of yaxis. value can be 'linear' or 'log'.
    """
    _m_state.gca().axes[1].update_style(scale=value)

def tick_params(axis='both', **kwargs):
    """ Get/Set tick properties. 
    Args:
        axis: 'x'/'y'/'both'.
    Kwargs:
        If not provided, will return styles (dict, or list of dicts) instead of setting them.
    """
    axis_idx = {'x':(0,), 'y':(1,), 'both':(0, 1)}[axis]
    if kwargs:
        for a in axis_idx:
            _m_state.gca().axes[a].tick.update_style(_translate_style(kwargs))
    else:
        if len(axis_idx) == 2:
            return [_m_state.gca().axes[a].tick.export_style() for a in axis]
        else:
            return _m_state.gca().axes[axis[0]].tick.export_style()


def legend(*args, **kwargs):
    """ Setting legends.

    Usage:
    - If no args and kwargs are provided, will toggle visibility of the legend.
    - If only kwargs are provided, will set legend properties.
    - If called as legend([label1, label2, label3]), will set labels of lines and bars according to sequence.
    - If called as legend([elem1, elem2], [label1, label2]), will set labels of elements.
    In the last two cases, kwargs will also be passed.
    """
    if len(args) == 2:
        args = [args[1], args[0]]
    proc_api.legend(_get_state(), *args, **kwargs)
    return _m_state.gca().legend

def title(text:str, **kwargs):
    """ Set subfigure title. Additional args will be passed as style properties of `Text`.
    """
    _m_state.gca().title.update_style(text=text, **_translate_style(kwargs))

def suptitle(text:str, **kwargs):
    """ Set figure title. Additional args will be passed as style properties of `Text`.
    """
    _m_state.gcf().title.update_style(text=text, **_translate_style(kwargs))

def grid(on:bool=True, axis:str='both', **kwargs):
    """ Set grid visibility on certain axis. 
    Args:
        axis: 'x'/'y'/'both'
    Kwargs:
        Will be passed as style properties of `Grid`.
    """
    axis_idx = {'x':(0,), 'y':(1,), 'both':(0, 1)}[axis]
    for a in axis_idx:
        _m_state.gca().axes[a].grid.update_style(visible=bool(on), **_translate_style(kwargs))

def group(group_desc:str):
    """ Set lines groupid and colorid from a short description (e.g. aabbcc). See doc.md#group for details.
    """
    from . import group_proc
    _get_state().gca().update_style(group=group_proc.parse_group(group_desc))
    _get_state().refresh_style()


def palette(palette_name:str, target:str='line', target_style:str='color'):
    """ Set the palette (colormap) for certain objects. See doc.md#set for details.

    Args:
        palette_name: the name of palette.
        target: the name of target, can be 'line', 'bar', 'point', 'polygon' or 'drawline'.
        target_style: can be 'color', 'facecolor', 'edgecolor' or 'linecolor' as long as the element supports it.
    """
    return proc_api.palette(_get_state(), palette_name, target, target_style)

set_cmap = palette

def clear():
    """ Clear the current subfigure.
    """
    _m_state.gca().clear()

cla = clear


# IO

def draw():
    """ Render current figure. Will not display it.
    """
    if not _m_state:
        return
    proc_api.set_redraw(_m_state, compact=_m_state.options['auto-compact'])
    _process.render_cur_figure(_m_state)

def show():
    """ Render all exisiting figures and display them.
    """
    if not _m_state:
        return
    _plot.initialize(_m_state, silent=True)
    _m_state.refresh_style(True)
    _process.process_display(_m_state)
    _plot.finalize(_m_state)


def save(filename):
    """ Save current figure. The file format is automatically determined from filename.
    """
    draw()
    _plot.save_figure(_m_state, filename)
    _m_state.cur_save_filename = filename

savefig = save

def load_file(filename, *args, **kwargs):
    """ Load file as a data sheet.
    """
    from . import model

    return model.load_file(filename, *args, **kwargs)

def pause(interval):
    from time import sleep
    sleep(interval)

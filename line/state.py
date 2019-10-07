
import copy

from collections import OrderedDict
from itertools import chain

from . import defaults
from .style import *
from .errors import warn, LineProcessError, print_as_warning
from .collection_util import RestrictDict, extract_single

from .style_man import *

class GlobalState:
    """ State of program.
    """
    
    def __init__(self):
        
        self.figures = OrderedDict()        # name:Figure
        self.cur_figurename = None          # Name of current figure
        self.default_stylesheet = StyleSheet()
        self.custom_stylesheet = StyleSheet()
        self.class_stylesheet = StyleSheet()

        self.cur_open_filename = None
        self.cur_save_filename = None
        self.is_interactive = None

        self.options = {}   # Additional program options

    def cur_figure(self):
        """ Get current figure state
        """
        
        if self.cur_figurename is None:
            raise LineProcessError("No figure is created yet")

        return self.figures[self.cur_figurename]


    def cur_subfigure(self):
        """ Get current subfigure state
        """
        if self.cur_figurename is None:
            raise LineProcessError("No figure is created yet")

        return self.figures[self.cur_figurename].subfigures[
            self.figures[self.cur_figurename].cur_subfigure
        ]

    def create_figure(self):
        """ Create a new figure with subfigure initialized.
        Used at the beginning or `figure` command.
        """

        if self.cur_figurename is None:
            self.cur_figurename = '1'
        self.figures[self.cur_figurename] = Figure('figure%s' % self.cur_figurename)

    def refresh_style(self):
        """ Recompute style of children
        """
        if len(self.figures) > 0:
            compute_style(self.cur_figure(), self.default_stylesheet)


class FigObject:
    """ Style-modifiable object in the figure.
    """

    def __init__(self, typename, name, custom_style_setter={}, custom_style_getter={}):
        """ typename -> object idenfier;
            style -> exportable style;
            attr -> unexportable style;

        get_style() and set_style() will modify both attr and style;
        export_style() will export style only;
        """

        self.typename = typename
        self.name = name
        self.classnames = set()
        self.style = Style() #defaults.get_default_style_entries(name)
        self.computed_style = None
        self.custom_style_setter = custom_style_setter   # dict of lambda exprs.
        self.custom_style_getter = custom_style_getter

    def update_style(self, style_dict):
        """ Update style from style_dict.
        If a name is in custom_style_setter, it will be called to get real value;
        Otherwise will call default setter.

        Will not raise expression if a style is not found.
        """

        has_updated = False

        for d, v in style_dict.items():
            if d in self.custom_style_setter:
                self.custom_style_setter[d](self.style, v)
                has_updated = True
            else:
                self.style[d] = v
                has_updated = True
            
                # TODO smarter recognition of invalid style name

        return has_updated

    def get_style(self, name):
        """ Get value of style
        """
        if name in self.custom_style_getter:
            return self.custom_style_getter[name](self.style)
        else:
            return self.style[name]

    def attr(self, name):
        """ Alias for get_computed_style
        """
        return self.computed_style[name]

    def export_style(self):
        """ Export style to Style object
        """
        return self.style.export()

    def get_computed_style(self, name):
        """ Lower level get style for backend.
        """
        return self.computed_style[name]

    def add_class(self, name):
        """ Add a name to class
        """
        self.classnames.add(name)

    def remove_class(self, name):
        """ Remove style class without error
        """
        try:
            self.classnames.remove(name)
        except KeyError:
            pass

    def has_name(self, name):
        return name == self.name

    def get_children(self):
        return []

    def find_elements(self, name):
        if self.has_name(name):
            return [self]
        else:
            return list(chain.from_iterable((c.find_elements() for c in self.get_children())))

    def copy(self, copy_attr=False):
        """ Copies only style if copy_attr is not set.
        """
        new_obj = type(self)(self.typename)
        if copy_attr:
            new_obj.style = self.style.copy()
        else:
            new_obj.style.copy_from(self.style)


class Figure(FigObject):


    def __init__(self, figure_name):
        
        self.subfigures = [Subfigure('subfigure0')]        # list of subfigures
        self.cur_subfigure = 0      # index of subfigure
        self.is_changed = True      # changed
        self.backend = None         # object for plotting

        super().__init__('figure', figure_name, {
            'dpi':self._set_dpi,
            'hspacing':lambda x:   _assign_list(x[0]['spacing'], 0, x[1]),
            'vspacing': lambda x:   _assign_list(x[0]['spacing'], 1,  x[1]),
            'margin-bottom': lambda x: _assign_list(x[0]['margin'], 0, x[1]),
            'margin-left': lambda x: _assign_list(x[0]['margin'], 1, x[1]),
            'margin-right': lambda x:_assign_list(x[0]['margin'], 2, x[1]),
            'margin-top': lambda x:  _assign_list(x[0]['margin'], 3, x[1]),
        }, {
            'hspacing': lambda x: x['spacing'][0],
            'vspacing': lambda x: x['spacing'][1]
        })

    def _set_dpi(self, m_style, value):
        if value == 'high': # 4k resolution
            m_style['dpi'] = 200
        elif value == 'mid':    # 2k resolution
            m_style['dpi'] = 150
        elif value == 'low':    # <= 1k
            m_style['dpi'] = 100
        m_style['size'] = [
            defaults.default_figure_size_inches[0]*m_style['dpi'],
            defaults.default_figure_size_inches[1]*m_style['dpi']]

    def has_name(self, name):
        return name == 'gcf' or name == self.name

    def get_children(self, dynamical=True):
        if dynamical:
            return [self.subfigures[self.cur_subfigure]]
        else:
            return self.subfigures

    def clear_backend(self):
        self.backend = None
        for m_subfig in self.subfigures:
            m_subfig.backend = None


class Subfigure(FigObject):

    def __init__(self, subfigure_name):

        super().__init__('subfigure', subfigure_name, {
            'padding-bottom': lambda x:_assign_list(x[0]['padding'], 0, x[1]),
            'padding-left': lambda x: _assign_list(x[0]['padding'], 1, x[1]),
            'padding-right': lambda x:_assign_list(x[0]['padding'], 2, x[1]),
            'padding-top': lambda x:  _assign_list(x[0]['padding'], 3, x[1]),
            'xlabel': lambda x:self.axes[0].update_style('text', x[1]),
            'ylabel': lambda x:self.axes[1].update_style('text', x[1]),
            'rlabel': lambda x:self.axes[2].update_style('text', x[1]),
            'tlabel': lambda x:self.axes[3].update_style('text', x[1]),
            'xrange': lambda x:self.axes[0].update_style('range', x[1]),
            'yrange': lambda x:self.axes[1].update_style('range', x[1]),
            'rrange': lambda x:self.axes[2].update_style('range', x[1]),
            'trange': lambda x:self.axes[3].update_style('range', x[1]),
        }, {
            'xlabel': lambda x:self.axes[0].get_style('text'),
            'ylabel': lambda x:self.axes[1].get_style('text'),
            'rlabel': lambda x:self.axes[2].get_style('text'),
            'tlabel': lambda x:self.axes[3].get_style('text'),
            'xrange': lambda x:self.axes[0].get_style('range'),
            'yrange': lambda x:self.axes[1].get_style('range'),
            'rrange': lambda x:self.axes[2].get_style('range'),
            'trange': lambda x:self.axes[3].get_style('range'),
        })

        self.axes = [Axis('xaxis'), Axis('yaxis'), Axis('raxis'), Axis('taxis')]
        self.legend = Legend('legend')

        self.datalines = [] # datalines
        self.drawlines = [] # drawlines
        self.texts = []

        self.is_changed = True
        self.backend = None

    def has_name(self, name):
        return name == 'gca' or self.name == name

    def get_children(self):
        return self.axes + [self.legend] + self.datalines + self.drawlines + self.texts 

    def add_dataline(self, data, label, xlabel, style_dict):

        self.datalines.append(
            DataLine(data, label, xlabel, 'line%d'%len(self.datalines))
        )
        self.datalines[-1].update_style(style_dict)

    def add_drawline(self, start_pos, end_pos, style_dict):
        
        self.drawlines.append(
            DrawLine(start_pos, end_pos, 'drawline%d'%len(self.drawlines))
        )
        self.drawlines[-1].update_style(style_dict)

    def add_text(self, text, pos, style_dict):
        
        self.texts.append(
            Text(text, pos, 'text%d'%len(self.texts), new_style)
        )
        self.texts[-1].update_style(style_dict)
    
    def clear(self):
        """ Clear lines and texts but keep style.
        """
        self.datalines.clear()
        self.drawlines.clear()
        self.texts.clear()
        for i in range(4):
            self.axes[i].label.update_style({'text': ''})

    def get_axes_coord(self, d, axis=0, side='left'):

        if d is not None:
            lo, hi = self.axes[axis].attr['range']
            return (d-lo)/(hi-lo)
        else:
            return 0 if side == 'left' else 1.0

    def set_group(self, group, old_ss, palette_name=None):
        """ group: group generated by parse.parse_group();
            old_ss: GlobalState.class_stylesheet;
            palette_name: the current palette using, by default load the first class.
        """

        if palette_name is None:
            palette_name = self.classnames[0]

        prefix, repeator, suffix = group
        ss = StyleSheet()

        # TODO fix possible errors

        for idx, cidx in enumerate(prefix):
            ss.data[NameSelector('line%d' %idx)] = old_ss.get_style_by_name('.%s #line%d' % (palette_name, cidx))

        if suffix:
            for idx in range(max(len(prefix), len(self.datalines)-len(suffix)), len(self.datalines)):
                cidx = suffix[idx - len(self.datalines) + len(suffix)]
                ss.data[NameSelector('line%d' %idx)] = old_ss.get_style_by_name('.%s #line%d' % (palette_name, cidx))

        if repeator and len(self.datalines) > len(prefix) + len(suffix):
            for idx in range(len(prefix), len(self.datalines) - len(suffix)):
                ss.data[NameSelector('line%d' %idx)] = old_ss.get_style_by_name(
                    '.%s #line%d' % (palette_name, repeator[(idx - len(prefix))%len(repeator)]))

        ss.apply_to(self)


class Axis(FigObject):

    def __init__(self, axis_name):

        self.label = Label(axis_name[0] + 'label')
        self.tick = Tick(axis_name[0] + 'tick')
        self.grid = Grid(axis_name[0] + 'grid')

        super().__init__('axis', axis_name, {
            'range':self._set_range
        })

    def get_children(self):
        return [self.label, self.tick, self.grid]

    def _set_range(self, m_style, value):
        m_style['range'] = (value[0], value[1])
        if value[2] is not None:
            m_style['interval'] = value[2]
        else:
            from . import scale
            t = scale.get_ticks(value[0], value[1])
            m_style['interval'] = t[1] - t[0]

class Tick(FigObject):
    def __init__(self, name):
        super().__init__('tick', name)

class Grid(FigObject):
    def __init__(self, name):
        super().__init__('grid', name)

class Legend(FigObject):
    def __init__(self, name):
        super().__init__('legend', name)

class DataLine(FigObject):

    def __init__(self, data, label, xlabel, name):
        self.x = data[0]
        self.y = data[1]

        super().__init__('line', name, {
            'color':self._set_color
        })
        self.update_style({
            'label':label, 'xlabel':xlabel, 'skippoint':1
        })

    def _set_color(self, m_style, value):
        m_style['linecolor'] = value
        m_style['edgecolor'] = value


class DrawLine(FigObject):

    def __init__(self, start_pos, end_pos, name):

        super().__init__('drawline', name, {
            'color':self._set_color
        })
        self.update_style({'startpos':start_pos, 'endpos':end_pos})

    def _set_color(self, m_style, value):
        m_style['linecolor'] = value
        m_style['edgecolor'] = value
    

class Text(FigObject):

    def __init__(self, text, pos, name):

        super().__init__('text', name, {
            'font':self._set_font
        }, {
            'font':lambda x:x['fontfamily']
        })
        self.update_style({'text':text, 'pos':pos})

    def _set_font(self, m_style, value):
        m_style['fontfamily'] = value[0]
        m_style['fontsize'] = value[1]


class Label(FigObject):
    def __init__(self, name):

        super().__init__('label', name, {
            'font':self._set_font
        }, {
            'font':lambda x:x['fontfamily']
        })

    def _set_font(self, m_style, value):
        m_style['fontfamily'] = value[0]
        m_style['fontsize'] = value[1]

    
def _assign_list(a, idx, v):
    a[idx] = v
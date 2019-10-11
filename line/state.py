
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
        self.custom_stylesheet.apply_to(self.cur_figure())

    def refresh_style(self, refresh_all_subfigure=False):
        """ Recompute style of children
        """
        if len(self.figures) > 0:
            self.cur_figure().set_dynamical = not refresh_all_subfigure
            self.class_stylesheet.apply_to(self.cur_figure())
            compute_style(self.cur_figure(), self.default_stylesheet)
            self.cur_figure().set_dynamical = True


class FigObject:
    """ Style-modifiable object in the figure.
    """

    def __init__(self, typename, name, custom_style_setter={}, custom_style_getter={}):
        """ typename -> object idenfier;
            name -> object name;
            custom_style_setter: lambda accepts style, value;
            custom_style_getter: lambda accepts name;
        """

        self.typename = typename
        self.name = name
        self.classnames = []
        self.style = Style()
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
            elif d in defaults.default_style_entries[self.typename]:
                self.style[d] = v
                has_updated = True
            else:
                warn('Skipping invalid style: "%s"' % d)

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
        if name not in self.classnames:
            self.classnames.append(name)

    def remove_class(self, name):
        """ Remove style class without error
        """
        try:
            self.classnames.pop(self.classnames.index(name))
        except ValueError:
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
        self.set_dynamical = True
        self.backend = None         # object for plotting

        super().__init__('figure', figure_name, {
            'dpi':self._set_dpi,
            'hspacing':lambda s, v:   _assign_list(s['spacing'], 0, v),
            'vspacing': lambda s, v:   _assign_list(s['spacing'], 1,  v),
            'margin-bottom': lambda s,v: _assign_list(s['margin'], 0, v),
            'margin-left': lambda s,v: _assign_list(s['margin'], 1, v),
            'margin-right': lambda s,v:_assign_list(s['margin'], 2, v),
            'margin-top': lambda s,v:  _assign_list(s['margin'], 3, v),
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

    def get_children(self):
        if self.set_dynamical:
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
            'padding-bottom': lambda s,v:_assign_list(s['padding'], 0, v),
            'padding-left': lambda s,v: _assign_list(s['padding'], 1, v),
            'padding-right': lambda s,v:_assign_list(s['padding'], 2, v),
            'padding-top': lambda s,v:  _assign_list(s['padding'], 3, v),
            'xlabel': lambda s,v:self.axes[0].label.update_style({'text': v}),
            'ylabel': lambda s,v:self.axes[1].label.update_style({'text': v}),
            'rlabel': lambda s,v:self.axes[2].label.update_style({'text': v}),
            'tlabel': lambda s,v:self.axes[3].label.update_style({'text': v}),
            'xrange': lambda s,v:self.axes[0].update_style({'range': v}),
            'yrange': lambda s,v:self.axes[1].update_style({'range': v}),
            'rrange': lambda s,v:self.axes[2].update_style({'range': v}),
            'trange': lambda s,v:self.axes[3].update_style({'range': v}),
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
        if not self.computed_style or not self.attr('group'):
            self.datalines[-1].update_style({'colorid':len(self.datalines), 'groupid':1})
        else:
            self.update_colorid()

    def add_drawline(self, start_pos, end_pos, style_dict):
        
        self.drawlines.append(
            DrawLine(start_pos, end_pos, 'drawline%d'%len(self.drawlines))
        )
        self.drawlines[-1].update_style(style_dict)

    def add_text(self, text, pos, style_dict):
        
        self.texts.append(
            Text(text, pos, 'text%d'%len(self.texts))
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

    def update_colorid(self):
        """ refresh colorid and groupid for each line.
        """
        prefix, repeator, suffix = self.get_style('group')
        # they are all list of ints

        cidx_refnum = [1] * (max(prefix+repeator+suffix)+1)   # occurrence of colorid
        colorids = []
        groupids = []

        for idx, cidx in enumerate(prefix):
            colorids.append(cidx)
            if cidx != 0:
                groupids.append(cidx_refnum[cidx])
                cidx_refnum[cidx] += 1
            else:
                groupids.append(0)

        if suffix:
            for idx in range(max(len(prefix), len(self.datalines)-len(suffix)), len(self.datalines)):
                cidx = suffix[idx - len(self.datalines) + len(suffix)]
                colorids.append(cidx)
                if cidx != 0:
                    groupids.append(cidx_refnum[cidx])
                    cidx_refnum[cidx] += 1
                else:
                    groupids.append(0)

        if repeator and len(self.datalines) > len(prefix) + len(suffix):
            for idx in range(len(prefix), len(self.datalines) - len(suffix)):
                cidx = repeator[(idx - len(prefix))%len(repeator)]
                colorids.append(cidx)
                if cidx != 0:
                    groupids.append(cidx_refnum[cidx])
                    cidx_refnum[cidx] += 1
                else:
                    groupids.append(0)

        for l, cidx, gidx in zip(self.datalines, colorids, groupids):
            l.update_style({'colorid':cidx, 'groupid':gidx})
            

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
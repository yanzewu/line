
import copy

from collections import OrderedDict
from itertools import chain

from . import defaults
from .style import *
from .errors import warn
from .collection_util import RestrictDict


class GlobalState:
    """ State of program.
    """
    
    def __init__(self):
        
        self.figures = OrderedDict()        # name:Figure
        self.cur_figurename = None          # Name of current figure

        self.default_figure = None      # figure template

        self.cur_open_filename = None
        self.cur_save_filename = None
        self.is_interactive = None

        self.options = {}   # Additional program options

    def cur_figure(self):
        """ Get current figure state
        """
        return self.figures[self.cur_figurename]


    def cur_subfigure(self):
        """ Get current subfigure state
        """
        return self.figures[self.cur_figurename].subfigures[
            self.figures[self.cur_figurename].cur_subfigure
        ]

    def create_figure(self):
        """ Create a new figure with subfigure initialized.
        Used at the beginning or `figure` command.
        """

        # beginning
        if self.cur_figurename is None:
            self.cur_figurename = '1'

        self.figures[self.cur_figurename] = self.default_figure.copy()
        self.cur_figure().name = 'figure%s' % self.cur_figurename

    def find_elements(self, name, raise_error=False):
        """ Find elements by name recursively.
        Returns iterable of elements.
        """
        if name == 'figure':
            return [self.cur_figure()]
        elif name.startswith('figure@'):
            try:
                return self.figures[name[7:]]
            except KeyError:
                if raise_error:
                    raise
                else:
                    return []
        else:
            return self.cur_figure().find_elements(name, raise_error)


class FigObject:
    """ Style-modifiable object in the figure.
    """

    def __init__(self, name, style:RestrictDict, attr:RestrictDict):
        """ name -> object idenfier;
            style -> exportable style;
            attr -> unexportable style;

        get_style() and set_style() will modify both attr and style;
        export_style() will export style only;
        """

        self.name = name
        self.style = style.copy()
        self.attr = attr.copy()

    def get_style(self, name):
        try:
            return self.style[name]
        except KeyError:
            return self.attr[name]

    def set_style(self, name, value):
        """ Set style name=value.
        Raise `KeyError` if name is not found, `ValueError` if value is not valid.
        """
        try:
            self.style[name] = value
        except KeyError:
            self.attr[name] = value

    def get_attr(self, name):
        return self.attr[name]

    def set_attr(self, name, value):
        self.attr[name] = value

    def set_style_recur(self, name, value):
        """ If self has the style, set it;
        Otherwise pass the style to children.
        """
        try:
            self.set_style(name, value)
        except (KeyError, ValueError):
            has_style = False
            for e in self.get_children():
                has_style = has_style or e.set_style_recur(name, value)
            return has_style
        else:
            return True
  

    def export_style(self):
        """ Export style to dict {stylename:value}
        """
        return self.style.export()

    def export_style_recur(self):

        style_exp = self.export_style()
        for e in self.get_children():
            style_exp[e.name] = e.export_style()

    def get_children(self):
        return []

    def copy(self):
        return copy.deepcopy(self)


class Figure(FigObject):

    def __init__(self, name, style):
        
        self.subfigures = []        # list of subfigures
        self.cur_subfigure = 0      # index of subfigure
        self.backend = None         # object for plotting

        super().__init__(name, style, defaults.default_figure_attr)

    def find_elements(self, name, raise_error=False):
        if name == 'figure':
            return [self]
        elif name == 'subfigure' or name == 'gca':
            return self.subfigures
        elif name.startswith('subfigure'):
            try:
                return [self.subfigures[int(name[9:])]]
            except (ValueError, IndexError):
                if raise_error:
                    raise
                else:
                    warn('Invalid selection: %s, skipping' % name)
                    return []

        else:
            return self.subfigures[self.cur_subfigure].find_elements(name, raise_error)

    def set_style(self, name, value):
        if name == 'hspacing':
            self.style['spacing'][0] = value
        elif name == 'vspacing':
            self.style['spacing'][1] = value
        elif name.startswith('margin-'):
            axis_index = {'bottom':0, 'left':1, 'right':2, 'top':3}
            self.style['margin'][axis_index[name[7:]]] = value
        else:
            super().set_style(name, value)

    def get_style(self, name):
        if name == 'hspacing':
            return self.style['spacing'][0]
        elif name == 'vspacing':
            return self.style['spacing'][1]
        else:
            return super().get_style(name)

    def get_children(self):
        return self.subfigures


class Subfigure(FigObject):

    def __init__(self, name, style_dict={}):
        
        style = RestrictDict({
            'padding':style_dict['padding'],
            'palatte':style_dict['palatte'],
            'default-dataline':style_dict['default-dataline'],
            'default-drawline':style_dict['default-drawline'],
            'default-text':style_dict['default-text']
        })

        super().__init__(name, style, defaults.default_subfigure_attr)

        self.axes = [
            Axis('xaxis', style_dict['xaxis']),
            Axis('yaxis', style_dict['yaxis']),
            Axis('raxis', style_dict['raxis']),
            Axis('taxis', style_dict['taxis']),
            ]

        self.legend = Legend('legend', style_dict['legend'])

        self.datalines = [] # datalines
        self.drawlines = [] # drawlines
        self.texts = []

        self.dataline_template = []
        self.update_template_palatte()

        self.backend = None

    
    def find_elements(self, name, raise_error):
        
        if name == 'line':
            return self.datalines

        elif name == 'text':
            return self.texts

        elif name.startswith('line@'):
            return list(filter(lambda x:x.label == name[5:], self.datalines))

        elif name.startswith('text@'):
            return list(filter(lambda x:x.text == name[5:], self.texts))

        else:
            _mychildren = self.get_children()
            _ret = list(filter(lambda x:x.name == name, _mychildren))
            if len(_ret) == 0:
                for c in _mychildren:
                    _ret += c.get_children()
            return list(filter(lambda x:x.name == name, _ret))


    def get_children(self):
        return self.axes + [self.legend] + self.datalines + self.drawlines + self.texts 

    def set_style(self, name, value):
        if name.startswith('padding-'):
            axis_index = {'left':0, 'bottom':1, 'right':2, 'top':3}
            self.style['padding'][axis_index[name[8:]]] = value

        elif name.endswith('label'):
            axis_index = {'x':0, 'y':1, 'r':2, 't':3}
            self.axes[axis_index[name[:-5]]].label.set_style('text', value)

        elif name.endswith('range'):
            axis_index = {'x':0, 'y':1, 'r':2, 't':3}
            self.axes[axis_index[name[:-5]]].set_style('range', value)

        else:
            super().set_style(name, value)

    def get_style(self, name):
        if name.startswith('padding-'):
            axis_index = {'left':0, 'bottom':1, 'right':2, 'top':3}
            return self.style['padding'][axis_index[name[8:]]]

        elif name.endswith('label'):
            axis_index = {'x':0, 'y':1, 'r':2, 't':3}
            return self.axes[axis_index[name[:-5]]].label.get_style('text')

        elif name.endswith('range'):
            axis_index = {'x':0, 'y':1, 'r':2, 't':3}
            return self.axes[axis_index[name[:-5]]].get_style('range')

        else:
            return super().get_style(name)

    def add_dataline(self, data, label, xlabel, style_dict:dict):

        if len(self.datalines) == len(self.dataline_template):
            self.dataline_template.append(self.style['default-dataline'].copy())

        idx = len(self.datalines)
        self.datalines.append(
            DataLine(data, label, xlabel, 'line%d'%len(self.datalines), RestrictDict({}))
        )
        # reset style
        self.datalines[-1].style = self.dataline_template[len(self.datalines)-1]
        for s, v in style_dict.items():
            try:
                self.datalines[-1].set_style(s, v)
            except KeyError as e:
                warn(e)
        

    def add_drawline(self, start_pos, end_pos, style_dict:dict):
        new_style = self.style['default-drawline'].copy()
        self.drawlines.append(
            DrawLine(start_pos, end_pos, 'drawline%d'%len(self.drawlines), new_style)
        )
        for s, v in style_dict.items():
            try:
                self.drawlines[-1].set_style(s, v)
            except KeyError as e:
                warn(e)

    def add_text(self, text, pos, style_dict:dict):
        new_style = self.style['default-text'].copy()
        self.texts.append(
            Text(text, pos, 'text%d'%len(self.texts), new_style)
        )
        for s, v in style_dict.items():
            try:
                self.texts[-1].set_style(s, v)
            except KeyError as e:
                warn(e)
    
    def clear(self):
        self.datalines.clear()
        self.drawlines.clear()
        self.texts.clear()

    def get_axes_coord(self, d, axis=0, side='left'):

        if d is not None:
            lo, hi = self.axes[axis].attr['range']
            return (d-lo)/(hi-lo)
        else:
            return 0 if side == 'left' else 1.0

    def update_template_palatte(self):

        colors = PALETTES[self.style['palatte']]
        if not self.dataline_template:
            self.dataline_template = [self.style['default-dataline'].copy() for i in range(len(colors)-1)]

        # TODO LOW point color and style support
        for idx in range(len(colors)-1):
            self.dataline_template[idx]['linecolor'] = colors[idx+1]

        if not self.attr['group']:
            return
        
        prefix, repeator, suffix = self.attr['group']

        for idx, cidx in enumerate(prefix):
            self.dataline_template[idx]['linecolor'] = colors[cidx]

        if suffix:
            for idx in range(max(len(prefix), len(self.datalines)-len(suffix)), len(self.datalines)):
                cidx = suffix[idx - len(self.datalines) + len(suffix)]
                self.dataline_template[idx]['linecolor'] = colors[cidx] 

        if repeator and len(self.datalines) > len(prefix) + len(suffix):
            for idx in range(len(prefix), len(self.datalines) - len(suffix)):
                self.dataline_template[idx]['linecolor'] = colors[repeator[(idx - len(prefix))%len(repeator)]]


class Axis(FigObject):

    def __init__(self, name, style):
        
        c = name[0]

        self.label = Text('', None, c+'label', style[c+'label'])
        self.tick = FigObject(c+'tick', style[c+'tick'], RestrictDict({}))
        self.grid = FigObject(c+'grid', style[c+'grid'], RestrictDict({}))

        super().__init__(name, style['axis'], defaults.default_axis_attr)

    def get_children(self):
        return [self.label, self.tick, self.grid]

    def set_style(self, name, value):
        if name == 'range':
            self.attr['range'] = (value[0], value[1])
            if value[2] is not None:
                self.attr['interval'] = value[2]
        else:
            super().set_style(name, value)


class Legend(FigObject):

    def __init__(self, name, style):

        super().__init__(name, style, defaults.default_legend_attr)


class DataLine(FigObject):

    def __init__(self, data, label, xlabel, name, style:RestrictDict):
        self.x = data[0]
        self.y = data[1]
        attr = RestrictDict({
            'label':label,
            'xlabel':xlabel,
            'skippoint':1,
        })

        super().__init__(name, style, attr)

    def set_style(self, name, value):

        if name == 'color':
            super().set_style('linecolor', value)
            super().set_style('edgecolor', value)
        else:
            super().set_style(name, value)


class DrawLine(FigObject):

    def __init__(self, start_pos, end_pos, name, style:RestrictDict):

        attr = RestrictDict({
            'startpos':start_pos,
            'endpos':end_pos,
        })

        super().__init__(name, style, attr)

    def set_style(self, name, value):

        if name == 'color':
            super().set_style('linecolor', value)
            super().set_style('edgecolor', value)
        else:
            super().set_style(name, value)
    

class Text(FigObject):

    def __init__(self, text, pos, name, style:RestrictDict):
        attr = RestrictDict({
            'text':text,
            'pos':pos,
        })

        super().__init__(name, style, attr)

    def set_style(self, name, value):
        if name == 'font':
            super().set_style('fontfamily', value[0])
            super().set_style('fontsize', value[1])
        else:
            super().set_style(name, value)


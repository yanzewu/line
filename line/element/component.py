
import numpy as np

from .. import scale

from . import style
from . import errors
from . import FigObject


class Axis(FigObject):

    def __init__(self, axis_name):

        self.label = Label(axis_name[0] + 'label')
        self.tick = Tick(axis_name[0] + 'tick')
        self.grid = Grid(axis_name[0] + 'grid')

        self.vmin = 0.0
        self.vmax = 1.0

        super().__init__('axis', axis_name, {
            'range':self._set_range,
            'scale':self._set_scale
        })

    def get_children(self):
        return [self.label, self.tick, self.grid]

    def _set_range(self, m_style, value):
        m_style['range'] = value
        if m_style == self.style[1]:
            self._refresh_ticks(value, self.get_style('scale'))

    def _set_scale(self, m_style, value):
        m_style['scale'] = value
        if m_style == self.style[1]:
            r = self.get_style('range')
            r = (r[0], r[1], None)
            self._refresh_ticks(r, value)

    def _set_datarange(self, vmin, vmax):
        # just set a cache of data range. Different from _set_range.
        self.vmin = vmin
        self.vmax = vmax

    def _refresh_ticks(self, m_range, m_scale):
        get_ticks = scale.get_ticks_log if m_scale == 'log' else scale.get_ticks

        if m_range[0] is None or m_range[1] is None:
            self.update_style({'tickpos': get_ticks(self.vmin, self.vmax)})
        elif m_range[2] is None:
            self.update_style({'tickpos': get_ticks(m_range[0], m_range[1])})
        else:
            if m_scale == 'linear':
                self.update_style({'tickpos': np.arange(m_range[0], m_range[1]+m_range[2]/10, m_range[2])})
            elif m_scale == 'log':
                numticks = int(1.0/m_range[2])
                self.update_style({'tickpos': get_ticks(m_range[0], m_range[1], numticks)})


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
            'color':_set_color
        })
        self.update_style({
            'label':label, 'xlabel':xlabel, 'skippoint':1
        })


class Bar(FigObject):

    def __init__(self, data, label, xlabel, dynamic_bin, name):

        self.dynamic_bin = dynamic_bin
        if dynamic_bin:
            assert not isinstance(data, tuple)
            self.data_raw = data
        else:
            self.x = data[0]
            self.y = data[1]

        super().__init__('bar', name, {
            'edgecolor': lambda s,v: s.update({'linecolor':v}),
            'color':self._set_color,
            'bin':self._set_bin,
            'norm':self._set_norm,
            'width': self._set_width,
        })
        self.update_style({
            'label':label, 'xlabel':xlabel
        })

    def _set_color(self, m_style, value):
        m_style['fillcolor'] = value
        m_style['linecolor'] = style.darken_color(*value)

    def _set_bin(self, m_style, value):
        if not self.dynamic_bin:
            raise LineProcessError("Cannot set bin width since it is static")
        else:
            m_style['bin'] = value
            if m_style == self.style[1]:
                try:
                    self._refresh_data(value, self.get_style('norm'))
                except KeyError:
                    pass

    def _set_norm(self, m_style, value):
        if not self.dynamic_bin:
            raise LineProcessError("Cannot set bin width since it is static")
        else:
            m_style['norm'] = value
            if m_style == self.style[1]:
                try:
                    self._refresh_data(self.get_style('bin'), value)
                except KeyError:
                    pass

    def _refresh_data(self, bins, norm):
        from ..sheet_util import histogram
        _result = histogram(self.data_raw, bins=bins, norm=norm)
        self.x = _result[:, 0]
        self.y = _result[:, 1]
        self.update_style({'barwidth':self.get_style('width')*(self.x[1]-self.x[0])})

    def _set_width(self, m_style, width):
        m_style['width'] = width
        if self.dynamic_bin and 'x' in self.__dict__:
            m_style['barwidth'] = width*(self.x[1] - self.x[0])
        else:
            m_style['barwidth'] = width


class DrawLine(FigObject):

    def __init__(self, start_pos, end_pos, name):

        super().__init__('drawline', name, {
            'color':_set_color
        })
        self.update_style({'startpos':start_pos, 'endpos':end_pos})
    

class Polygon(FigObject):

    def __init__(self, data, name):
        self.x = data[0]
        self.y = data[1]
        super().__init__('polygon', name, {
            'edgecolor': lambda s,v: s.update({'linecolor':v}),
            'color':self._set_color
        })

    def _set_color(self, m_style, value):
        m_style['fillcolor'] = value
        m_style['linecolor'] = value


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


def _set_color(m_style, value):
    m_style['linecolor'] = value
    m_style['edgecolor'] = value


import numpy as np
import re

from ..graphing import scale

from . import style
from . import errors
from . import FigObject


class Axis(FigObject):

    def __init__(self, axis_name):

        self.label = Label(axis_name[:-4] + 'label')
        self.tick = Tick(axis_name[:-4] + 'tick')
        self.grid = Grid(axis_name[:-4] + 'grid')

        self.vmin = 0.0
        self.vmax = 1.0
        self.backend = None

        super().__init__('axis', axis_name, {
            'range':self._set_range,
            'scale':self._set_scale
        })

    def get_children(self):
        return [self.label, self.tick, self.grid]

    def _set_range(self, m_style, value):
        minpos = self.vmin if value[0] is None else value[0]
        maxpos = self.vmax if value[1] is None else value[1]

        m_style['range'] = (minpos, maxpos, value[2])
        if m_style == self.style[1]:
            self._refresh_ticks(m_style['range'], self.get_style('scale'))
        # TODO minpos, maxpos are not always vmin, vmax; they will have some padding around data.

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
        minpos, maxpos, step = m_range

        if m_scale == 'linear':
            self.update_style({'tickpos': scale.get_ticks(minpos, maxpos, step)})
            try:
                if self.tick.get_style('format') == '%mp':
                    self.tick.update_style({'format': r'%.4G'})
            except KeyError:
                pass
        elif m_scale == 'log':
            numticks = int(1.0/step) if step else None
            self.update_style({'tickpos': scale.get_ticks_log(minpos, maxpos, numticks)})
            self.tick.update_style({'format':'%mp'})


class Tick(FigObject):
    def __init__(self, name):
        super().__init__('tick', name, {}, {}, {
            'format': self._update_formatter,
            'fontsize': lambda a, b: self.render_callback(1) if self.render_callback else None,
            'visible': lambda a, b: self.render_callback() if self.render_callback else None,
            })

    def _update_formatter(self, oldval, value):

        if r'%mp' in value:
            self.computed_style['formatter'] = lambda x, pos: value.replace('%mp', ('$10^{%d}$' % np.log10(x)) if x > 0 else '%.4G' % x)
        elif 'm' in value:
            value1 = value.replace('m', 'g')
            self.computed_style['formatter'] = lambda x, pos: '$%s$' % re.sub(r'e\+?(|\-)0*(\d+)', '\\\\times10^{\\1\\2}', (value1 % x))
        else:
            self.computed_style['formatter'] = lambda x, pos:value % x

        if self.render_callback:
            self.render_callback(1)

class Grid(FigObject):
    def __init__(self, name):
        super().__init__('grid', name)

class Legend(FigObject):
    def __init__(self, name):
        super().__init__('legend', name, style_change_handler={
            'fontsize': lambda a, b: self._check_render(),
            'fontfamily': lambda a, b: self._check_render(),
            'visible': lambda a, b: self._check_render(),
            'pos': lambda a, b: self._check_render(),
            'column': lambda a, b: self._check_render(),
        })
        # TODO it is known that add dataline will change legend without auto positioning
    def _check_render(self):
        pos = self.attr('pos')
        if isinstance(pos, style.FloatingPos):
            return
        for p in pos:
            if p in (style.FloatingPos.OUTBOTTOM, style.FloatingPos.OUTLEFT, style.FloatingPos.OUTRIGHT, style.FloatingPos.OUTTOP) or \
                (isinstance(p, (int, float)) and (p > 1 or p < 0)):
                # NOTE of course there are some weird cases that require render without being outside. I'll see if it's necessary to add them.
                if self.render_callback:
                    self.render_callback(2)
                break
            

class DataLine(FigObject):

    def __init__(self, data, label, xlabel, name):
        self.data = data

        super().__init__('line', name, {
            'color':_set_color,
            'label':self._set_label,
        })
        self.update_style({
            'label':label, 'xlabel':xlabel, 'skippoint':1
        })

    def _set_label(self, m_style, label):
        if label.startswith('!'):
            try:
                pattern, repl = label[1:].split('>')
            except ValueError:
                raise errors.LineParseError('Invalid label formattor: %s' % label)
            repl = re.sub(r'\%N', self.name[4:], repl)
            matcher = re.match(pattern, m_style['label'])
            if matcher:
                m_style['label'] = re.sub(r'(?<!\\)\$(\d+)', lambda x:matcher.group(int(x.group(1))), repl)
        else:
            m_style['label'] = label


class SmartDataLine(FigObject):

    def __init__(self, data, label, xlabel, name):
        self.data = data

        super().__init__('line', name, {
            'color':_set_color,
            'range': self._set_range,
        }, {}, {
            'range': self._update_range,
        })
        self.update_style({
            'label':label, 'xlabel':xlabel
        })

    def _set_range(self, m_style, value):
        m_style['range'] = value

    def _update_range(self, oldval, value):
        step_ = value[2] if value[2] else (value[1] - value[0])/100
        self.data.update(np.arange(value[0], value[1] + step_, step_))


class Bar(FigObject):

    def __init__(self, data, label, xlabel, dynamic_bin, name):

        self.dynamic_bin = dynamic_bin
        if dynamic_bin:
            from ..dataview import datapack
            assert isinstance(data, datapack.DistributionDataPack)

        self.data = data

        super().__init__('bar', name, {
            'edgecolor': lambda s,v: s.update({'linecolor':v}),
            'color':self._set_color,
            'bin':self._set_bin,
            'norm':self._set_norm,
            'width': self._set_width,
        })
        self.update_style({
            'label':label, 'xlabel':xlabel, 'width':1.0
        })

    def _set_color(self, m_style, value):
        m_style['fillcolor'] = value
        m_style['linecolor'] = style.darken_color(*value)

    def _set_bin(self, m_style, value):
        if not self.dynamic_bin:
            raise LineProcessError("Cannot set bin width since it is static")
        else:
            m_style['bin'] = value
            self.data.set_bins(value)
            self._update_barwidth()

    def _set_norm(self, m_style, value):
        if not self.dynamic_bin:
            raise LineProcessError("Cannot set bin width since it is static")
        else:
            m_style['norm'] = value
            self.data.set_norm(value)

    def _update_barwidth(self):
        self.update_style({
            'barwidth':self.get_style('width')*(self.data.get_x()[1]-self.data.get_x()[0])
            })

    def _set_width(self, m_style, width):
        m_style['width'] = width
        if self.dynamic_bin:
            self._update_barwidth()
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
        self.data = data
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
            'font':_set_font
        }, {
            'font':lambda x:'%s,%d' % (x['fontfamily'], x['fontsize'])
        }, {
            'fontsize': lambda a, b: self.render_callback(1) if self.render_callback else None,
            'fontfamily': lambda a, b: self.render_callback(1) if self.render_callback else None,
            'visible': lambda a, b: self.render_callback() if self.render_callback else None,
            'text': lambda a, b: self.render_callback(1) if self.render_callback else None,
        })
        self.update_style({'text':text, 'pos':pos})

    def _set_font(self, m_style, value):
        m_style['fontfamily'] = value[0]
        m_style['fontsize'] = value[1]


class Label(FigObject):
    def __init__(self, name):

        super().__init__('label', name, {
            'font':_set_font
        }, {
            'font':lambda x: '%s,%d' % (x['fontfamily'], x['fontsize'])
        }, {
            'text': lambda a, b: self.render_callback(1) if self.render_callback else None,
            'fontsize': lambda a, b: self.render_callback(1) if self.render_callback else None,
            'fontfamily': lambda a, b: self.render_callback(1) if self.render_callback else None,
            'visible': lambda a, b: self.render_callback() if self.render_callback else None,
            'pos': lambda a, b: self.render_callback() if self.render_callback else None, 
        })

    def _set_font(self, m_style, value):
        m_style['fontfamily'] = value[0]
        m_style['fontsize'] = value[1]


def _set_color(m_style, value):
    m_style['linecolor'] = value
    m_style['edgecolor'] = value


def _set_font(m_style, value):
    m_style['fontfamily'] = value[0]
    if value[1] is None:
        m_style['fontsize'] = value[1]

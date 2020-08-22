
import numpy as np
import re

from ..graphing import scale

from . import style
from . import errors
from . import FigObject


class Axis(FigObject):

    def __init__(self, axis_name, extent_callback=None):

        self.label = Label(axis_name[:-4] + 'label')
        self.tick = Tick(axis_name[:-4] + 'tick')
        self.grid = Grid(axis_name[:-4] + 'grid')

        self.extent_callback = extent_callback  # called to get data extent
        self.backend = None

        super().__init__('axis', axis_name, {
            'scale':self._set_scale,
        }, {}, {
            'range': lambda o,n: self._update_ticks(),
            'scale': self._update_scale,
        })

    def get_children(self):
        return [self.label, self.tick, self.grid]

    def _set_scale(self, m_style, value):
        try:
            fmt = self.get_style('format')
        except KeyError:
            fmt = r'%.4G'

        # reset format between log/normal
        if value == 'linear' and fmt in ('%mp', '%mP'):
            self.tick.update_style({'format': style.css.SpecialStyleValue.DEFAULT})
        elif value == 'log' and fmt not in ('%mp', '%mP'):
            self.tick.update_style({'format': r'%mp'})

    def _update_scale(self, oldval, value):
        r = self.computed_style['range']
        self.computed_style['range'] = (r[0], r[1], None)   # clear the step
        self._update_ticks()

    def _update_ticks(self):
        r = self.computed_style['range']
        automatic = False
        if (r[0] is None or r[1] is None) and self.extent_callback:
            automatic = True
            extent = self.extent_callback()
        else:
            extent = (0.0, 1.0)

        minpos = extent[0] if r[0] is None else r[0]
        maxpos = extent[1] if r[1] is None else r[1]
        step = r[2]
        # TODO minpos, maxpos are not always vmin, vmax; they may have some padding around data.

        if self.computed_style['scale'] == 'linear':
            tickpos = scale.get_ticks(minpos, maxpos, step)
            bound = (tickpos[0], tickpos[-1]) if automatic else (minpos, maxpos)
            self.computed_style['tickpos'] = tickpos
            self.computed_style['range'] = (bound[0], bound[-1],
                self.computed_style['tickpos'][1] - self.computed_style['tickpos'][0])
            # This is a trick: If range is None instead of actual value, the updater will be called
            # every time.
            
        elif self.computed_style['scale'] == 'log':
            numticks = int(1.0/step) if step else None
            tickpos = scale.get_ticks_log(minpos, maxpos, numticks)
            bound = (tickpos[0], tickpos[-1]) if automatic else (minpos, maxpos)
            self.computed_style['tickpos'] = tickpos
            self.computed_style['range'] = (minpos, maxpos, 1.0/numticks)


class Tick(FigObject):
    def __init__(self, name):
        super().__init__('tick', name, {}, {}, {
            'format': self._update_formatter,
            'fontsize': lambda a, b: self.render_callback(1) if self.render_callback else None,
            'visible': lambda a, b: self.render_callback() if self.render_callback else None,
            })

    def _update_formatter(self, oldval, value):

        # special formatter for log
        if r'%mp' in value:
            self.computed_style['formatter'] = lambda x, pos: value.replace('%mp', ('$10^{%d}$' % np.log10(x)) if (x > 0 and x < 0.01 or x > 100) else '%.4G' % x)
        elif r'%mP' in value:
            self.computed_style['formatter'] = lambda x, pos: value.replace('%mP', ('$10^{%d}$' % np.log10(x)) if x > 0 else '%.4G' % x)
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
        }, {}, {
            'side': lambda o,n: self._update_ext()
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

    def _update_ext(self):
        self._ext_cache = (np.min(self.data.get_x()), np.max(self.data.get_x()), 
            np.min(self.data.get_y()), np.max(self.data.get_y()))


class SmartDataLine(FigObject):

    def __init__(self, data, label, xlabel, name):
        self.data = data

        super().__init__('line', name, {
            'color':_set_color,
            'range': self._set_range,
        }, {}, {
            'range': self._update_ext,
            'side': lambda o,n: self._update_ext(None, self.computed_style['range']),
        })
        self.update_style({
            'label':label, 'xlabel':xlabel
        })

    def _set_range(self, m_style, value):
        m_style['range'] = value

    def _update_ext(self, oldval, value):
        step_ = value[2] if value[2] else (value[1] - value[0])/100
        self.data.update(np.arange(value[0], value[1] + step_, step_))
        self._ext_cache = (value[0], value[1] + step_, 
            np.min(self.data.get_y()), np.max(self.data.get_y()))


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
        }, {}, {
            'bin': self._update_bin,
            'norm': self._update_norm,
            'width': self._update_width,
            'side': lambda o,n: self._update_ext,
        })
        self.update_style({
            'label':label, 'xlabel':xlabel,
        })

    def _set_color(self, m_style, value):
        m_style['fillcolor'] = value
        m_style['linecolor'] = style.darken_color(*value)

    def _set_bin(self, m_style, value):
        if not self.dynamic_bin:
            raise LineProcessError("Cannot set bin width since it is static")
        else:
            m_style['bin'] = value

    def _set_norm(self, m_style, value):
        if not self.dynamic_bin:
            raise LineProcessError("Cannot set bin width since it is static")
        else:
            m_style['norm'] = value

    def _update_bin(self, oldval, value):
        if self.dynamic_bin:
            self.data.set_bins(value)
            self.computed_style['barwidth'] = self.computed_style['width'] * (self.data.get_x()[1]-self.data.get_x()[0])
            self._update_ext()

    def _update_norm(self, oldval, value):
        if self.dynamic_bin:
            self.data.set_norm(value)
            self._update_ext()

    def _update_width(self, oldval, value):
        if self.dynamic_bin:
            self.computed_style['barwidth'] = value * (self.data.get_x()[1]-self.data.get_x()[0])
        else:
            self.computed_style['barwidth'] = value
        self._update_ext()

    def _update_ext(self):
        x, y = self.data.get_x(), self.data.get_y()
        self._ext_cache = (np.min(x) - self.computed_style['barwidth']/2,
            np.max(x) + self.computed_style['barwidth']/2,
            np.min(y), np.max(y))


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

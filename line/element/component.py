
import numpy as np
import re

from ..graphing import scale
from .. import defaults

from . import style
from . import errors
from .figobject import FigObject
from ._aux import _set_color, _set_data, _gen_fontprops_setter, _gen_fontprops_getter


class Axis(FigObject):

    def __init__(self, name, extent_callback=None, **kwargs):

        self.label = Label(name[:-4] + 'label')
        self.tick = Tick(name[:-4] + 'tick')
        self.grid = Grid(name[:-4] + 'grid')

        self.extent_callback = extent_callback  # called to get data extent
        self.backend = None

        super().__init__('axis', name, {
            'scale':self._set_scale,
            **_gen_fontprops_setter(self, defaults.default_style_sheet.find_type('axis')),
        }, {
            **_gen_fontprops_getter(self),
        }, {
            'range': lambda o,n: self._update_ticks(),
            'scale': self._update_scale,
        }, **kwargs)

    def get_children(self):
        return [self.label, self.tick, self.grid]

    def _set_scale(self, m_style, value):
        try:
            fmt = self.get_style('format')
        except KeyError:
            fmt = r'%.4G'

        m_style['scale'] = value
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
        
        if (r[0] is None or r[1] is None) and self.extent_callback: # none -> seek data for value.
            extent = self.extent_callback()
        else:
            extent = (0.0, 1.0)

        minpos = extent[0] if r[0] is None else r[0]
        maxpos = extent[1] if r[1] is None else r[1]

        if maxpos < minpos:
            maxpos = minpos
        step = r[2]
        # TODO minpos, maxpos are not always vmin, vmax; they may have some padding around data.
        bound = [None, None]

        if self.computed_style['scale'] == 'linear':
            tickpos = scale.get_ticks(minpos, maxpos, step)
            bound[0] = tickpos[0] if r[0] is None else minpos
            bound[1] = tickpos[-1] if r[1] is None else maxpos
            
            self.computed_style['tickpos'] = tickpos
            self.computed_style['range'] = (bound[0], bound[1],
                self.computed_style['tickpos'][1] - self.computed_style['tickpos'][0])
            # This is a trick: If range is None instead of actual value, the updater will be called
            # every time.
            
        elif self.computed_style['scale'] == 'log':
            numticks = int(1.0/step) if step else None
            tickpos = scale.get_ticks_log(minpos, maxpos, numticks)
            bound[0] = tickpos[0] if r[0] is None else minpos
            bound[1] = tickpos[-1] if r[1] is None else maxpos

            self.computed_style['tickpos'] = tickpos
            self.computed_style['range'] = (bound[0], bound[1], 1.0/numticks if numticks else None)


class Tick(FigObject):
    def __init__(self, name, **kwargs):
        super().__init__('tick', name, {
            **_gen_fontprops_setter(self, defaults.default_style_sheet.find_type('tick')),}, {
            **_gen_fontprops_getter(self)}, {
            'format': self._update_formatter,
            'fontfamily': lambda a, b: self.render_callback(1) if self.render_callback else None,
            'fontprops': lambda a, b: self.render_callback(1) if self.render_callback else None,
            'visible': lambda a, b: self.render_callback() if self.render_callback else None,
            }, 
            **kwargs
            )

    def _update_formatter(self, oldval, value):

        # special formatter for log
        if r'%mp' in value:
            self.computed_style['formatter'] = lambda x, pos: value.replace('%mp', ('$\mathregular{10^{%d}}$' % np.log10(x)) if (x > 0 and x < 0.01 or x > 100) else '%.4G' % x)
        elif r'%mP' in value:
            self.computed_style['formatter'] = lambda x, pos: value.replace('%mP', ('$\mathregular{10^{%d}}$' % np.log10(x)) if x > 0 else '%.4G' % x)
        elif 'm' in value:
            value1 = value.replace('m', 'g')
            self.computed_style['formatter'] = lambda x, pos: '$\mathregular{%s}$' % re.sub(r'e\+?(|\-)0*(\d+)', '\\\\times10^{\\1\\2}', (value1 % x))
        else:
            self.computed_style['formatter'] = lambda x, pos:value % x

        if self.render_callback:
            self.render_callback(1)

class Grid(FigObject):
    def __init__(self, name, **kwargs):
        super().__init__('grid', name, **kwargs)

class Legend(FigObject):
    def __init__(self, name, **kwargs):
        super().__init__('legend', name, {
            **_gen_fontprops_setter(self, defaults.default_style_sheet.find_type('legend')),}, {
            **_gen_fontprops_getter(self)}, {
            'fontprops': lambda a, b: self._check_render(),
            'fontfamily': lambda a, b: self._check_render(),
            'visible': lambda a, b: self._check_render(),
            'pos': lambda a, b: self._check_render(),
            'column': lambda a, b: self._check_render(),
            }, 
            **kwargs
        )
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
            
class SupLegend(FigObject):
    def __init__(self, name, **kwargs):
        super().__init__('legend', name, {
            **_gen_fontprops_setter(self, defaults.default_style_sheet.find_type('legend')),}, {
            **_gen_fontprops_getter(self)}, {
            'fontprops': lambda a, b: self.render_callback(2) if self.render_callback else None,
            'fontfamily': lambda a, b: self.render_callback(2) if self.render_callback else None,
            'visible': lambda a, b: self.render_callback(2) if self.render_callback else None,
            'pos': lambda a, b: self.render_callback(2) if self.render_callback else None,
            'column': lambda a, b: self.render_callback(2) if self.render_callback else None,
            'source': lambda a, b: self.render_callback(2) if self.render_callback else None,
            }, 
            **kwargs)
    

class DataLine(FigObject):

    def __init__(self, name, data, **kwargs):

        super().__init__('line', name, {
            'color':_set_color,
            'label':self._set_label,
            'data': lambda s,v: _set_data(self, v),
        }, {}, {
            'side': lambda o,n: self._update_ext()
        },
        **kwargs
        )
        _set_data(self, data)

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
        self._ext_cache = (np.nanmin(self.data.get_x()), np.nanmax(self.data.get_x()), 
            np.nanmin(self.data.get_y()), np.nanmax(self.data.get_y()))


class SmartDataLine(FigObject):

    def __init__(self, name, data, **kwargs):

        super().__init__('line', name, {
            'color':_set_color,
            'range': self._set_range,
            'data': lambda s,v: _set_data(self, v),
        }, {}, {
            'range': self._update_ext,
            'side': lambda o,n: self._update_ext(None, self.computed_style['range']),
        }, 
        **kwargs
        )
        self.data = data

    def _set_range(self, m_style, value):
        m_style['range'] = value

    def _update_ext(self, oldval, value):
        step_ = value[2] if value[2] else (value[1] - value[0])/100
        self.data.update(np.arange(value[0], value[1] + step_, step_))
        self._ext_cache = (value[0], value[1] + step_, 
            np.nanmin(self.data.get_y()), np.nanmax(self.data.get_y()))


class Bar(FigObject):

    def __init__(self, name, data, dynamic_bin:bool=False, **kwargs):

        self.dynamic_bin = dynamic_bin
        if dynamic_bin:
            from ..dataview import datapack
            assert isinstance(data, datapack.DistributionDataPack), "Distribution datapack required"

        super().__init__('bar', name, {
            'edgecolor': lambda s,v: s.update({'linecolor':v}),
            'color':self._set_color,
            'bin':self._set_bin,
            'norm':self._set_norm,
            'data': lambda s,v: _set_data(self, v),
        }, {}, {
            'bin': self._update_bin,
            'norm': self._update_norm,
            'width': self._update_width,
            'side': lambda o,n: self._update_ext,
        },
        **kwargs,
        )

        self.data = data    # cannot _update_ext since computed_values are not available.

    def _set_color(self, m_style, value):
        m_style['fillcolor'] = value
        m_style['linecolor'] = style.darken_color(*value)

    def _set_bin(self, m_style, value):
        if not self.dynamic_bin:
            raise errors.LineProcessError("Cannot set bin width since it is static")
        else:
            m_style['bin'] = value

    def _set_norm(self, m_style, value):
        if not self.dynamic_bin:
            raise errors.LineProcessError("Cannot set bin width since it is static")
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
        self._ext_cache = (np.nanmin(x) - self.computed_style['barwidth']/2,
            np.nanmax(x) + self.computed_style['barwidth']/2,
            np.nanmin(y), np.nanmax(y))


class DrawLine(FigObject):

    def __init__(self, name, startpos=(0,0), endpos=(1,1), **kwargs):

        super().__init__('drawline', name, {
            'color':_set_color
            }, 
            startpos=startpos,
            endpos=endpos,
            **kwargs
        )
    

class Polygon(FigObject):

    def __init__(self, name, data, **kwargs):
        super().__init__('polygon', name, {
            'edgecolor': lambda s,v: s.update({'linecolor':v}),
            'color':self._set_color,
            'data': lambda s,v: setattr(self, 'data', v),
        },
        **kwargs
        )
        self.data = data

    def _set_color(self, m_style, value):
        # Note this is different from _set_color.
        m_style['fillcolor'] = value
        m_style['linecolor'] = value


class Text(FigObject):

    def __init__(self, name, **kwargs):

        super().__init__('text', name, {
            **_gen_fontprops_setter(self, defaults.default_style_sheet.find_type('text')),}, {
            **_gen_fontprops_getter(self)}, {
            'fontfamily': lambda a, b: self.render_callback(1) if self.render_callback else None,
            'fontprops': lambda a, b: self.render_callback(1) if self.render_callback else None,
            'pos': lambda a, b: self.render_callback() if self.render_callback else None, 
            'text': lambda a, b: self.render_callback(1) if self.render_callback else None,
            'visible': lambda a, b: self.render_callback() if self.render_callback else None,
            },
            **kwargs
        )


class Label(FigObject):
    def __init__(self, name, **kwargs):

        super().__init__('label', name, {
            **_gen_fontprops_setter(self, defaults.default_style_sheet.find_type('label')),}, {
            **_gen_fontprops_getter(self)}, {
            'fontfamily': lambda a, b: self.render_callback(1) if self.render_callback else None,
            'fontprops': lambda a, b: self.render_callback(1) if self.render_callback else None,
            'pos': lambda a, b: self.render_callback() if self.render_callback else None, 
            'text': lambda a, b: self.render_callback(1) if self.render_callback else None,
            'visible': lambda a, b: self.render_callback() if self.render_callback else None,
            },
            **kwargs
            )

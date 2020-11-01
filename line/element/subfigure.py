
from . import FigObject
from . import errors

from .component import *
from .. import defaults
from ._aux import _gen_fontprops_getter, _gen_fontprops_setter, _gen_padding_getter, _gen_padding_setter

class Subfigure(FigObject):

    def __init__(self, subfigure_name):

        super().__init__('subfigure', subfigure_name, {
            'xlabel': lambda s,v:self.axes[0].label.update_style({'text': v}, priority=self._style_priority(s)),
            'ylabel': lambda s,v:self.axes[1].label.update_style({'text': v}, priority=self._style_priority(s)),
            'y2label': lambda s,v:self.axes[2].label.update_style({'text': v}, priority=self._style_priority(s)),
            'x2label': lambda s,v:self.axes[3].label.update_style({'text': v}, priority=self._style_priority(s)),
            'xrange': lambda s,v:self.axes[0].update_style({'range': v}, priority=self._style_priority(s)),
            'yrange': lambda s,v:self.axes[1].update_style({'range': v}, priority=self._style_priority(s)),
            'y2range': lambda s,v:self.axes[2].update_style({'range': v}, priority=self._style_priority(s)),
            'x2range': lambda s,v:self.axes[3].update_style({'range': v}, priority=self._style_priority(s)),
            'xscale': lambda s,v:self.axes[0].update_style({'scale': v}, priority=self._style_priority(s)),
            'yscale': lambda s,v:self.axes[1].update_style({'scale': v}, priority=self._style_priority(s)),
            'y2scale': lambda s,v:self.axes[2].update_style({'scale': v}, priority=self._style_priority(s)),
            'x2scale': lambda s,v:self.axes[3].update_style({'scale': v}, priority=self._style_priority(s)),
            'title': lambda s,v: self.title.update_style({'text': v}),
            'legend': self._set_legend,
            **_gen_padding_setter(self, defaults.default_style_sheet.find_type('subfigure')),
            **_gen_fontprops_setter(self, defaults.default_style_sheet.find_type('subfigure')),
        }, {
            'xlabel': lambda x:self.axes[0].get_style('text'),
            'ylabel': lambda x:self.axes[1].get_style('text'),
            'y2label': lambda x:self.axes[2].get_style('text'),
            'x2label': lambda x:self.axes[3].get_style('text'),
            'xrange': lambda x:self.axes[0].get_style('range'),
            'yrange': lambda x:self.axes[1].get_style('range'),
            'y2range': lambda x:self.axes[2].get_style('range'),
            'x2range': lambda x:self.axes[3].get_style('range'),
            **_gen_padding_getter(self),
            **_gen_fontprops_getter(self),
        }, {
            'group': lambda oldst, newst: self.update_colorid() if newst else None,
        })

        self.axes = [Axis('xaxis', extent_callback = lambda: self.update_extents(0)), 
            Axis('yaxis', extent_callback = lambda: self.update_extents(1)), 
            Axis('y2axis', extent_callback = lambda: self.update_extents(2)), 
            Axis('x2axis', extent_callback = lambda: self.update_extents(3))]
        self.legend = Legend('legend')
        self.title = Text('', (style.FloatingPos.CENTER, style.FloatingPos.OUTTOP), 'title')

        self.datalines = [] # datalines
        self.bars = []
        self.drawlines = [] # drawlines
        self.polygons = []
        self.texts = []

        self.is_changed = True
        self.backend = None
        self.on_size_changed = None

        self._legend_candidates = []


    def has_name(self, name):
        return name == 'gca' or self.name == name

    def get_children(self):
        return [self.legend] + [self.title] + self.datalines + self.bars + self.drawlines + self.polygons + self.texts + self.axes

    def update_render_callback(self):

        for a in self.axes:
            a.render_callback = self.render_callback
            a.tick.render_callback = self.render_callback
            a.label.render_callback = self.render_callback

        self.title.render_callback = self.render_callback
        self.legend.render_callback = self.render_callback
        # NOTE: adjusting subfigure itself (size/pos) won't trigger render. I'll see if it is necessary in the future.

    def _add_element(self, class_, typename, element_queue, auto_colorid, styles, *args):
        
        newidx = 1 if not element_queue else int(element_queue[-1].name[len(typename):])+1
        element_queue.append(
            class_(
                *args, name=typename + str(newidx)
            )
        )
        if auto_colorid:
            element_queue[-1].update_style({'colorid': newidx})
        if styles:
            element_queue[-1].update_style(styles)
        self.is_changed = True
        return element_queue[-1]

    def _refresh_colorid(self):
        if not self.computed_style or not self.attr('group'):
            self.datalines[-1].update_style({'colorid':len(self.datalines), 'groupid':1})
        else:
            self.update_colorid()

    def add_dataline(self, data, label, xlabel, style_dict):
        r = self._add_element(DataLine, 'line', self.datalines, False, {},
            data, label, xlabel)
        self._refresh_colorid()
        r.update_style(style_dict)
        self._activate_axis(r)
        return r

    def add_smartdataline(self, data, label, xlabel, style_dict):
        r = self._add_element(SmartDataLine, 'line', self.datalines, False, {},
            data, label, xlabel)
        self._refresh_colorid()
        r.update_style(style_dict)
        self._activate_axis(r)
        return r            

    def add_bar(self, data, label, xlabel, dynamic_bin, style_dict):

        r = self._add_element(Bar, 'bar', self.bars, True, style_dict,
            data, label, xlabel, dynamic_bin)
        self._activate_axis(r)
        return r

    def add_drawline(self, start_pos, end_pos, style_dict):
        
        return self._add_element(DrawLine, 'drawline', self.drawlines, False, style_dict,
            start_pos, end_pos)

    def add_polygon(self, data, style_dict):

        return self._add_element(Polygon, 'polygon', self.polygons, True, style_dict,
            data)

    def add_text(self, text, pos, style_dict):
        
        return self._add_element(Text, 'text', self.texts, False, style_dict, 
            text, pos)
    
    def remove_element(self, element):
        """ Remove an dynamical element (i.e. datalines, texts, polygons, ...)
        For data elements (dataline, bar), the rest indices will be recalculated.

        element: The element instance.
        Raises exception if element is not dynamical.
        """
        
        try:
            elem_queue = {DataLine:self.datalines, Bar:self.bars, DrawLine:self.drawlines, 
                Polygon: self.polygons, Text:self.texts}[type(element)]
            idx = elem_queue.index(element)
        except (KeyError, ValueError) as e:
            raise errors.LineProcessError('Cannot remove element: "%s"' % element.name)
        else:
            elem_queue.pop(idx)
            if elem_queue is self.datalines or elem_queue is self.drawlines:
                prefix = 'line' if elem_queue is self.datalines else 'bar'
                for i in range(idx, len(elem_queue)):
                    elem_queue[i].name = '%s%d' % (prefix, i+1)
            self.is_changed = True

    def clear(self, remove_label=False):
        """ Clear lines and texts but keep style.
        If `remove_label`, will remove the axis labels.
        """
        self.datalines.clear()
        self.bars.clear()
        self.drawlines.clear()
        self.polygons.clear()
        self.texts.clear()
        if remove_label:
            for i in range(4):
                self.axes[i].label.update_style({'text': style.css.SpecialStyleValue.DEFAULT})
        self.is_changed = True

    def get_axes_coord(self, pos, axis_id):
        """ Transform axis coord to data coord.
        pos: Either a number, or 'left'/'right'.
        """
        if pos == 'left':
            return 0.0
        elif pos == 'right':
            return 1.0
        else:
            lo, hi = self.axes[axis_id].attr['range']
            return (pos-lo)/(hi-lo)

    def update_colorid(self):
        """ refresh colorid and groupid for each line.
        """
        colorids, groupids = self.attr('group').generate_ids(len(self.datalines))

        for l, cidx, gidx in zip(self.datalines, colorids, groupids):
            l.update_style({'colorid':cidx, 'groupid':gidx})
        self.is_changed = True

    def _style_priority(self, m_style):
        return 0 if m_style is self.style[0] else 1

    def _set_legend(self, m_style, value):
        if isinstance(value, str):
            value = value.split()
        for d, v in zip(self.datalines + self.bars, value):
            d.update_style({'label': str(v)}, priority=self._style_priority(m_style))

    def set_automatic_labels(self):
        """ Try set automatic axis labels based on data label. If cannot
        create a unified label, will not do anything.
        """
        side_identifiers = (style.FloatingPos.BOTTOM, style.FloatingPos.LEFT, style.FloatingPos.RIGHT, style.FloatingPos.TOP)
        for i in range(4):
            if 'text' in self.axes[i].label.style[1] and self.axes[i].label.style[1]['text'] != style.css.SpecialStyleValue.DEFAULT:
                continue
            _update_axis_label(
                [d for d in self.datalines if side_identifiers[i] in d.get_style('side', raise_error=False, default=(style.FloatingPos.LEFT, style.FloatingPos.BOTTOM))],
                [d for d in self.bars if side_identifiers[i] in d.get_style('side', raise_error=False, default=(style.FloatingPos.LEFT, style.FloatingPos.BOTTOM))],
                self.axes[i],
                i == 0 or i == 3,
            )

    def update_extents(self, axis_id):
        """ Return the overall data range of corresponding axes (axis_id = 0,1,2,3).
        Must called after the style computation of all lines and bars.
        """
        _datalist = self.datalines + self.bars
        side_identifiers = (style.FloatingPos.BOTTOM, style.FloatingPos.LEFT, style.FloatingPos.RIGHT, style.FloatingPos.TOP)
        bound_identifiers = [(0,1), (2,3), (2,3), (0,1)]

        
        dl = [d for d in _datalist if side_identifiers[axis_id] in d.attr('side')]
        bi = bound_identifiers[axis_id]

        if dl:
            return min((d._ext_cache[bi[0]] for d in dl)), max((d._ext_cache[bi[1]] for d in dl))
        else:
            return 0.0, 1.0

    def _activate_axis(self, b):
        """ Activate corresponding axis
        """
        for i in range(4):
            s = b.get_style('side', raise_error=False, default=(style.FloatingPos.LEFT, style.FloatingPos.BOTTOM))
            self.axes[{style.FloatingPos.LEFT:1, style.FloatingPos.RIGHT:2}[s[0]]].update_style({'enabled': True})
            self.axes[{style.FloatingPos.BOTTOM:0, style.FloatingPos.TOP:3}[s[1]]].update_style({'enabled': True})

        
def _update_axis_label(datalines, bars, axis, horizontal):
    # subrotine called by subfigure.set_automatic_labels

    # TODO: clear label if necessary

    def _set_label(labels):
        if all((':' in x for x in labels)):    # Special Handler for File:column (usually in SheetCollection)
            suffix = labels[0][labels[0].index(':')+1:]
            if all((x[x.index(':')+1:] == suffix for x in labels)):
                return axis.label.update_style({'text': suffix})
        elif len(set(labels)) == 1:
            return axis.label.update_style({'text': labels.pop()})

    if not datalines and not bars:
        return

    if horizontal:
        return _set_label([d.get_style('xlabel') for d in datalines + bars])
    
    histogram_counts = len([b for b in bars if b.dynamic_bin])
    if histogram_counts == 0 and datalines:     # all datalines
        return _set_label([d.get_style('label') for d in datalines])
    elif histogram_counts == len(bars) and not datalines:   # all bars
        return axis.label.update_style({'text':'Distribution'})
    else:
        return

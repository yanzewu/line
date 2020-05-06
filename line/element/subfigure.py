
from . import FigObject
from . import errors

from .component import *
from .component import _set_font

class Subfigure(FigObject):

    def __init__(self, subfigure_name):

        super().__init__('subfigure', subfigure_name, {
            'padding-bottom': lambda s,v:self._set_padding(s, 1, v),
            'padding-left': lambda s,v: self._set_padding(s, 0, v),
            'padding-right': lambda s,v:self._set_padding(s, 2, v),
            'padding-top': lambda s,v:  self._set_padding(s, 3, v),
            'xlabel': lambda s,v:self.axes[0].label.update_style({'text': v}, priority=self._style_priority(s)),
            'ylabel': lambda s,v:self.axes[1].label.update_style({'text': v}, priority=self._style_priority(s)),
            'rlabel': lambda s,v:self.axes[2].label.update_style({'text': v}, priority=self._style_priority(s)),
            'tlabel': lambda s,v:self.axes[3].label.update_style({'text': v}, priority=self._style_priority(s)),
            'xrange': self._set_xrange,
            'yrange': self._set_yrange,
            'rrange': lambda s,v:self.axes[2].update_style({'range': v}, priority=self._style_priority(s)),
            'trange': lambda s,v:self.axes[3].update_style({'range': v}, priority=self._style_priority(s)),
            'xscale': lambda s,v:self.axes[0].update_style({'scale': v}, priority=self._style_priority(s)),
            'yscale': lambda s,v:self.axes[1].update_style({'scale': v}, priority=self._style_priority(s)),
            'font': _set_font,
            'legend': self._set_legend,
        }, {
            'xlabel': lambda x:self.axes[0].get_style('text'),
            'ylabel': lambda x:self.axes[1].get_style('text'),
            'rlabel': lambda x:self.axes[2].get_style('text'),
            'tlabel': lambda x:self.axes[3].get_style('text'),
            'xrange': lambda x:self.axes[0].get_style('range'),
            'yrange': lambda x:self.axes[1].get_style('range'),
            'rrange': lambda x:self.axes[2].get_style('range'),
            'trange': lambda x:self.axes[3].get_style('range'),
            'font': lambda x:'%s,%d' % (x['fontfamily'], x['fontsize'])
        }, {
            'group': lambda oldst, newst: self.update_colorid() if newst else None,
        })

        self.axes = [Axis('xaxis'), Axis('yaxis'), Axis('raxis'), Axis('taxis')]
        self.legend = Legend('legend')

        self.datalines = [] # datalines
        self.bars = []
        self.drawlines = [] # drawlines
        self.polygons = []
        self.texts = []

        self.is_changed = True
        self.backend = None

    def _set_padding(self, m_style, idx, val):
        
        if 'padding' not in m_style:
            m_style['padding'] = list(self.get_style('padding'))
        m_style['padding'][idx] = val

    def has_name(self, name):
        return name == 'gca' or self.name == name

    def get_children(self):
        return self.axes + [self.legend] + self.datalines + self.bars + self.drawlines + self.polygons + self.texts 

    def _add_element(self, class_, typename, element_queue, auto_colorid, styles, *args):
        
        newidx = 1 if not element_queue else int(element_queue[-1].name[len(typename):])+1
        element_queue.append(
            class_(
                *args, typename + str(newidx)
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
        self.datalines[-1].update_style(style_dict)
        self._refresh_label()
        return r

    def add_smartdataline(self, data, label, xlabel, style_dict):
        r = self._add_element(SmartDataLine, 'line', self.datalines, False, {},
            data, label, xlabel)
        self._refresh_colorid()
        self.datalines[-1].update_style(style_dict)
        self._refresh_label()
        return r            

    def add_bar(self, data, label, xlabel, dynamic_bin, style_dict):

        r = self._add_element(Bar, 'bar', self.bars, True, style_dict,
            data, label, xlabel, dynamic_bin)
        self._refresh_label()
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
        """ Remove an element and recalculate indices
        raises ValueError if element does not exist in queue
        """
        if isinstance(element, DataLine):
            idx = self.datalines.index(element)
            self.datalines.pop(idx)
            for i in range(idx, len(self.datalines)):
                self.datalines[i].name = 'line%d' % (i+1)

        elif isinstance(element, DrawLine):
            idx = self.drawlines.index(element)
            self.drawlines.pop(idx)

        elif isinstance(element, Polygon):
            idx = self.polygons.index(element)
            self.polygons.pop(idx)
            
        elif isinstance(element, Text):
            idx = self.texts.index(element)
            self.texts.pop(idx)
            
        else:
            raise errors.LineProcessError('Cannot remove element: "%s"' % element.name)

        self.is_changed = True

    def clear(self):
        """ Clear lines and texts but keep style.
        """
        self.datalines.clear()
        self.bars.clear()
        self.drawlines.clear()
        self.polygons.clear()
        self.texts.clear()
        for i in range(4):
            self.axes[i].label.update_style({'text': ''})
        self.is_changed = True

    def get_axes_coord(self, d, axis=0, side='left'):

        if d is not None:
            lo, hi = self.axes[axis].attr['range']
            return (d-lo)/(hi-lo)
        else:
            return 0 if side == 'left' else 1.0

    def update_colorid(self):
        """ refresh colorid and groupid for each line.
        """
        colorids, groupids = self.attr('group').generate_ids(len(self.datalines))

        for l, cidx, gidx in zip(self.datalines, colorids, groupids):
            l.update_style({'colorid':cidx, 'groupid':gidx})
        self.is_changed = True

    def update_range_param(self):
        datalist = self.datalines + self.bars
    
        if not datalist:
            min_x, min_y, max_x, max_y = 0, 0, 1, 1
        else:
            min_x, min_y, max_x, max_y = np.inf, np.inf, -np.inf, -np.inf

        for d in datalist:
            x, y = d.data.get_x(), d.data.get_y()
            if isinstance(d, Bar):
                min_x = min(min_x, np.min(x) - d.get_style('barwidth')/2)
                max_x = max(max_x, np.max(x) + d.get_style('barwidth')/2)
                min_y = min(min_y, np.min(y), 0)
                max_y = max(max_y, np.max(y))
            else:
                min_x, max_x = min(min_x, np.min(x)), max(max_x, np.max(x))
                min_y, max_y = min(min_y, np.min(y)), max(max_y, np.max(y))

        self.axes[0]._set_datarange(min_x, max_x)
        self.axes[1]._set_datarange(min_y, max_y)

    def _style_priority(self, m_style):
        return 0 if m_style is self.style[0] else 1

    def _set_xrange(self, m_style, value):
        p = self._style_priority(m_style)
        if value == 'auto':
            self.update_range_param()
            self.axes[0].update_style({'range':(None,None,None)}, priority=p)
        else:
            self.axes[0].update_style({'range':value}, priority=p)
    
    def _set_yrange(self, m_style, value):
        p = self._style_priority(m_style)
        if value == 'auto':
            self.update_range_param()
            self.axes[1].update_style({'range':(None,None,None)}, priority=p)
        else:
            self.axes[1].update_style({'range':value}, priority=p)

    def _set_legend(self, m_style, value):
        if isinstance(value, str):
            value = value.split()
        for d, v in zip(self.datalines + self.bars, value):
            d.update_style({'label': str(v)}, priority=self._style_priority(m_style))

    def _refresh_label(self):
        """ Set automatic x/y label for gca.
        """
        if not self.datalines and not self.bars:
            return

        xlabels = set((d.get_style('xlabel') for d in self.datalines + self.bars))
        histogram_counts = len([b for b in self.bars if b.dynamic_bin])

        if len(xlabels) == 1:
            self.axes[0].label.update_style({'text': xlabels.pop()})
        # TODO: clear label if necessary

        if histogram_counts == 0:
            ylabels = set((d.get_style('label') for d in self.datalines))
        elif histogram_counts == len(self.bars) and not self.datalines:
            ylabels = {'Distribution'}  # The label "Distribution" is set only when all plots are histogram
        else:
            return

        if len(ylabels) == 1:
            self.axes[1].label.update_style({'text': ylabels.pop()})
        
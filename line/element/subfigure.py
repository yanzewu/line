
from . import FigObject
from . import errors

from .component import *

class Subfigure(FigObject):

    def __init__(self, subfigure_name):

        super().__init__('subfigure', subfigure_name, {
            'padding-bottom': lambda s,v:self._set_padding(s, 1, v),
            'padding-left': lambda s,v: self._set_padding(s, 0, v),
            'padding-right': lambda s,v:self._set_padding(s, 2, v),
            'padding-top': lambda s,v:  self._set_padding(s, 3, v),
            'xlabel': lambda s,v:self.axes[0].label.update_style({'text': v}),
            'ylabel': lambda s,v:self.axes[1].label.update_style({'text': v}),
            'rlabel': lambda s,v:self.axes[2].label.update_style({'text': v}),
            'tlabel': lambda s,v:self.axes[3].label.update_style({'text': v}),
            'xrange': self._set_xrange,
            'yrange': self._set_yrange,
            'rrange': lambda s,v:self.axes[2].update_style({'range': v}),
            'trange': lambda s,v:self.axes[3].update_style({'range': v}),
            'xscale': lambda s,v:self.axes[0].update_style({'scale': v}),
            'yscale': lambda s,v:self.axes[1].update_style({'scale': v})
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
        element_queue[-1].update_style(styles)

    def add_dataline(self, data, label, xlabel, style_dict):

        self._add_element(DataLine, 'line', self.datalines, False, {},
            data, label, xlabel)
        if not self.computed_style or not self.attr('group'):
            self.datalines[-1].update_style({'colorid':len(self.datalines), 'groupid':1})
        else:
            self.update_colorid()
        self.datalines[-1].update_style(style_dict)

    def add_bar(self, data, label, xlabel, dynamic_bin, style_dict):

        self._add_element(Bar, 'bar', self.bars, True, style_dict,
            data, label, xlabel, dynamic_bin)

    def add_drawline(self, start_pos, end_pos, style_dict):
        
        self._add_element(DrawLine, 'drawline', self.drawlines, False, style_dict,
            start_pos, end_pos)

    def add_polygon(self, data, style_dict):

        self._add_element(Polygon, 'polygon', self.polygons, True, style_dict,
            data)

    def add_text(self, text, pos, style_dict):
        
        self._add_element(Text, 'text', self.texts, False, style_dict, 
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
            idx = self.drawlines.index(element)
            self.texts.pop(idx)
            
        else:
            raise errors.LineProcessError('Cannot remove element: "%s"' % element.name)

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

    def update_range_param(self):
        datalist = self.datalines + self.bars
        max_x = max([np.max(d.x) for d in datalist])
        min_x = min([np.min(d.x) for d in datalist])
        max_y = max([np.max(d.y) for d in datalist])
        min_y = min([np.min(d.y) for d in datalist])
        if self.bars and min_y > 0:
            min_y = 0.0

        self.axes[0]._set_datarange(min_x, max_x)
        self.axes[1]._set_datarange(min_y, max_y)

    def _set_xrange(self, m_style, value):
        if value == 'auto':
            self.update_range_param()
            self.axes[0].update_style({'range':(None,None,None)})
        else:
            self.axes[0].update_style({'range':value})
    
    def _set_yrange(self, m_style, value):
        if value == 'auto':
            self.update_range_param()
            self.axes[1].update_style({'range':(None,None,None)})
        else:
            self.axes[1].update_style({'range':value})

            
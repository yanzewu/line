
from . import FigObject
from . import Subfigure
from . import defaults

class Figure(FigObject):


    def __init__(self, figure_name):
        
        self.subfigures = [Subfigure('subfigure0')]        # list of subfigures
        self.cur_subfigure = 0      # index of subfigure
        self.is_changed = True      # changed
        self.set_dynamical = True
        self.backend = None         # object for plotting

        super().__init__('figure', figure_name, {
            'dpi':self._set_dpi,
            'hspacing':lambda s, v: self._set_spacing_and_margin(s, 'spacing', 0, v),
            'vspacing': lambda s, v: self._set_spacing_and_margin(s, 'spacing', 1, v),
            'margin-bottom': lambda s,v: self._set_spacing_and_margin(s, 'margin', 1, v),
            'margin-left': lambda s,v: self._set_spacing_and_margin(s, 'margin', 0, v),
            'margin-right': lambda s,v:self._set_spacing_and_margin(s, 'margin', 2, v),
            'margin-top': lambda s,v:  self._set_spacing_and_margin(s, 'margin', 3, v),
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

    def _set_spacing_and_margin(self, m_style, key, idx, val):

        if key not in m_style:
            m_style[key] = list(self.get_style(key))

        m_style[key][idx] = val

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

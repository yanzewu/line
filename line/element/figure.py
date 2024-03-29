
from . import FigObject
from . import Subfigure
from . import defaults
from .component import Text, SupLegend
from ._aux import _gen_fontprops_setter, _gen_fontprops_getter, _gen_margin_setter, \
    _gen_margin_getter, _gen_spacing_setter, _gen_spacing_getter, _gen_size_setter, _gen_size_getter
from ..style import FloatingPos

class Figure(FigObject):


    def __init__(self, figure_name):
        
        self.subfigures = [Subfigure('subfigure1')]        # list of subfigures
        self.title = Text('', (FloatingPos.CENTER, FloatingPos.TOP), 'suptitle')
        self.legend = SupLegend('suplegend')

        self.cur_subfigure = 0      # index of subfigure
        self.is_changed = True      # changed
        self.needs_rerender = 0     # 0 -- nothing; 1 -- compact only; 2 -- compact + render
        self.set_dynamical = True
        self.backend = None         # object for plotting

        super().__init__('figure', figure_name, {
            'dpi':self._set_dpi,
            'title': lambda s,v: self.title.update_style({'text': v}),
            **_gen_size_setter(self, defaults.default_style_sheet.find_type('figure')),
            **_gen_margin_setter(self, defaults.default_style_sheet.find_type('figure')),
            **_gen_spacing_setter(self, defaults.default_style_sheet.find_type('figure')),
            **_gen_fontprops_setter(self, defaults.default_style_sheet.find_type('figure')),
        }, {
            **_gen_size_getter(self),
            **_gen_margin_getter(self),
            **_gen_spacing_getter(self),
            **_gen_fontprops_getter(self),
        }, {
            'size': lambda a, b: self.render_callback() if self.render_callback else None,
            'margin': lambda a, b: self.render_callback() if self.render_callback else None,
        })

        self.update_render_callback()

    def _set_dpi(self, m_style, value):
        if value == 'high': # 4k resolution
            m_style['dpi'] = 200
        elif value == 'mid':    # 2k resolution
            m_style['dpi'] = 150
        elif value == 'low':    # <= 1k
            m_style['dpi'] = 100
        else:
            m_style['dpi'] = value
            return
        m_style['size'] = [
            defaults.default_options['physical-figure-size'][0]*m_style['dpi'],
            defaults.default_options['physical-figure-size'][1]*m_style['dpi']]

    def has_name(self, name):
        return name == 'gcf' or name == self.name

    def get_children(self):
        if self.set_dynamical:
            return [self.subfigures[self.cur_subfigure], self.title, self.legend]
        else:
            return self.subfigures + [self.title, self.legend]

    def clear_backend(self):
        self.backend = None
        for m_subfig in self.subfigures:
            m_subfig.backend = None

    def update_render_callback(self):
        self.render_callback = self._render_callback
        self.legend.render_callback = self._render_callback
        self.title.render_callback = self._render_callback
        for s in self.subfigures:
            s.render_callback = self.render_callback
            s.update_render_callback()

    def _render_callback(self, ex_render_times=0):
        """ Send an extra render request. All requests are combined in one rendering session.
        ex_render_times:
            0 -> take the previous render data (not implemented, treated as 1);
            1 -> the element needs to be rerendered once;
            2 -> the element needs to be rerendered twice (only for multiple subfigures);
        """
        self.is_changed = True
        self.needs_rerender = max(self.needs_rerender, max(ex_render_times + 1, 1 if self.backend else 2))




from .style import css
from .element import Figure, Subfigure
from .errors import LineProcessError


class GlobalState:
    """ The program state.
    """
    
    def __init__(self):
        
        self.figures = dict()               # name:Figure
        self.cur_figurename = None          # Name of current figure
        self.default_stylesheet = css.StyleSheet()
        self.custom_stylesheet = css.StyleSheet()
        self.class_stylesheet = css.StyleSheet()

        self.cur_open_filename = None
        self.cur_save_filename = None
        self.is_interactive = None

        self.file_caches = {}
        
        self.options = {}   # Additional program options
        self._vmhost = None
        self._history = None
        self._gui_backend = None

    def cur_figure(self, create_if_empty:bool=False) -> Figure:
        """ Get current figure object. 
        create_if_empty: create one if no figure exists.
        """
        
        if self.cur_figurename is None:
            if create_if_empty:
                self.create_figure()
            else:
                raise LineProcessError("No figure is created yet")

        return self.figures[self.cur_figurename]

    gcf = cur_figure

    def cur_subfigure(self, create_if_empty:bool=False) -> Subfigure:
        """ Get current subfigure object.
        create_if_empty: create one if no figure exists.
        """
        m_fig = self.cur_figure(create_if_empty=create_if_empty)

        return m_fig.subfigures[m_fig.cur_subfigure]

    gca = cur_subfigure

    def create_figure(self, name='1', **kwargs) -> Figure:
        """ Create a new figure with subfigure initialized.
        """

        if self.cur_figurename is None:
            self.cur_figurename = name
        self.figures[self.cur_figurename] = Figure('figure%s' % self.cur_figurename, **kwargs)
        self.custom_stylesheet.apply_to(self.cur_figure(), 0)
        return self.cur_figure()

    def create_subfigure(self, name:str, **kwargs) -> Subfigure:
        """ Return a new Subfigure instance with basic setup and default style applied.
        Will NOT attach the subfigure to current figure.
        """
        subfig = Subfigure(name, **kwargs)
        self.custom_stylesheet.apply_to(subfig, 0)
        return subfig

    def remove_figure(self, name):
        """ Remove a figure with certain name.
        """
        self.figures.pop(str(name))
        if name == self.cur_figurename:
            if len(self.figures) == 0:
                self.cur_figurename = None
            else:
                self.cur_figurename = list(self.figures.keys())[0]

    def has_figure(self):
        """ Check if any figure exists.
        """
        return len(self.figures) > 0

    def update_default_stylesheet(self, ss:css.StyleSheet):
        """ Update the default stylesheet. Only element selectors are allowed.
        """
        for s in ss.data.keys():
            if not isinstance(s, css.TypeSelector):
                raise LineProcessError('Only element selectors are allowed')
        self.default_stylesheet.update(ss)

    def update_local_stylesheet(self, ss:css.StyleSheet):
        """ Load a new stylesheet. Distributes the selectors into
            custom_stylesheet and class_stylesheet.
        """
        self.custom_stylesheet.update(ss)
        for d, v in self.custom_stylesheet.data.items():
            if isinstance(d, (css.ClassNameSelector, css.ClassSelector, css.ClassStyleSelector, css.ClassTypeSelector)):
                self.class_stylesheet.data[d] = v
                

    def refresh_style(self, refresh_all_subfigure=False):
        """ Recompute style of children
        """
        if len(self.figures) > 0:
            self.cur_figure().set_dynamical = not refresh_all_subfigure

            # clear sys-set styles first, then apply
            ss = css.StyleSheet(css.AllSelector(), css.ResetStyle())
            ss.apply_to(self.cur_figure(), priority=0)
            self.custom_stylesheet.apply_to(self.cur_figure(), priority=0)
            self.class_stylesheet.apply_to(self.cur_figure(), priority=0)
            css.compute_style(self.cur_figure(), self.default_stylesheet)
            self.cur_figure().set_dynamical = True

    def figure(self, name=None, **kwargs):
        """ Set current figure. Create one if necessary.
        """

        if not name:
            i = 1
            while str(i) in self.figures:
                i += 1
            fig_name = str(i)
        else:
            fig_name = str(name)

        self.cur_figurename = name
        if fig_name not in self.figures:
            self.create_figure(name=fig_name, **kwargs)
            self.cur_figure().is_changed = True
        return self.cur_figure()

    def apply_styles(self, style_sheet:css.StyleSheet, adding_classes=[], removing_classes=[], set_all_figures=False, set_all_subfigures=False):
        """ Apply style_sheet to figures.
        Args:
            style_sheet: `css.StyleSheet` instance;
            adding_classes: List of str; The style class names to be added;
            removing_classes: List of str; The style class names to be removed;
            set_all_figures: If `False`, only current figure will be set. Otherwise the stylesheet will be apply
                to all figures and subfigures.
            set_all_subfigures: If `False`, only the current subfigure will be set. Not used if `set_all_figures' are set.
        Returns:
            Return `True` if the figure has been updated.
        """
        fig_list = [self.cur_figure()] if not set_all_figures else self.figures
        has_updated = False

        if set_all_figures or set_all_subfigures:
            for fig in fig_list:
                fig.set_dynamical = False

        for fig in fig_list:
            has_updated = style_sheet.apply_to(fig) or has_updated

        if len(adding_classes) > 0 or len(removing_classes) > 0:
            for fig in fig_list:
                selection = style_sheet.select(fig)
                if selection:
                    for s in selection:
                        for c in adding_classes:
                            s.add_class(c)
                        for c in removing_classes:
                            s.remove_class(c)
                has_updated = self.class_stylesheet.apply_to(fig) or has_updated

        if set_all_figures or set_all_subfigures:
            for fig in fig_list:
                fig.set_dynamical = True

        return has_updated


    def get_element_by_name(self, name, multiple:bool=False):
        """ Get element(s) by name.
        multiple: return all element that matches. Otherwise only return the first one.
        """
        if not self.cur_figurename:
            return None if not multiple else []
        elements = css.StyleSheet(css.NameSelector(name)).select(self.cur_figure())
        return elements if multiple else (elements.pop() if len(elements) > 0 else None)

    getelem = get_element_by_name
    get_elements_by_name = lambda x: get_element_by_name(True)

    def set_option(self, name:str, value):
        # TODO readonly options
        self.options.update({name: value})

    def get_option(self, name:str):
        return self.options[name]

    def is_remote(self) -> bool:
        return self.options['remote']
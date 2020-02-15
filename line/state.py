

import numpy as np

from .style import css
from .element import Figure, Subfigure
from .errors import LineProcessError


class GlobalState:
    """ State of program.
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

        self.variables = {'__varx': np.arange(-5, 5, 1)}
        self.file_caches = {}

        self.options = {}   # Additional program options

    def cur_figure(self, create_if_empty=False):
        """ Get current figure state
        """
        
        if self.cur_figurename is None:
            if create_if_empty:
                self.create_figure()
            else:
                raise LineProcessError("No figure is created yet")

        return self.figures[self.cur_figurename]


    def cur_subfigure(self, create_if_empty=False):
        """ Get current subfigure state
        """
        m_fig = self.cur_figure(create_if_empty=create_if_empty)

        return m_fig.subfigures[m_fig.cur_subfigure]

    def create_figure(self):
        """ Create a new figure with subfigure initialized.
        Used at the beginning or `figure` command.
        """

        if self.cur_figurename is None:
            self.cur_figurename = '1'
        self.figures[self.cur_figurename] = Figure('figure%s' % self.cur_figurename)
        self.custom_stylesheet.apply_to(self.cur_figure(), 0)

    def create_subfigure(self, name):
        """ Return a new Subfigure instance with basic setup and default style applied.
        Will NOT put attach the subfigure to current figure.
        """
        subfig = Subfigure(name)
        self.custom_stylesheet.apply_to(subfig, 0)
        return subfig

    def refresh_style(self, refresh_all_subfigure=False):
        """ Recompute style of children
        """
        if len(self.figures) > 0:
            self.cur_figure().set_dynamical = not refresh_all_subfigure

            # clear sys-set styles first, then apply
            ss = css.StyleSheet(css.AllSelector(), css.ResetStyle())
            ss.apply_to(self.cur_figure(), 0)
            self.custom_stylesheet.apply_to(self.cur_figure(), 0)
            self.class_stylesheet.apply_to(self.cur_figure(), 0)
            css.compute_style(self.cur_figure(), self.default_stylesheet)
            self.cur_figure().set_dynamical = True

    def figure(self, fig_name=None):
        """ Set current figure. Create one if necessary.
        """

        if not fig_name:
            i = 1
            while str(i) in self.figures:
                i += 1
            fig_name = str(i)
        else:
            fig_name = str(fig_name)

        self.cur_figurename = fig_name
        if fig_name not in self.figures:
            self.create_figure()
            self.cur_figure().is_changed = True


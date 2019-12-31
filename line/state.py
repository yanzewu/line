

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

    def cur_figure(self):
        """ Get current figure state
        """
        
        if self.cur_figurename is None:
            raise LineProcessError("No figure is created yet")

        return self.figures[self.cur_figurename]


    def cur_subfigure(self):
        """ Get current subfigure state
        """
        if self.cur_figurename is None:
            raise LineProcessError("No figure is created yet")

        return self.figures[self.cur_figurename].subfigures[
            self.figures[self.cur_figurename].cur_subfigure
        ]

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

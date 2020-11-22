
import copy
import warnings

from . import css
from . import defaults
from . import errors


class FigObject:
    """ Style-modifiable object in the figure.
    """

    def __init__(self, typename, name, custom_style_setter={}, custom_style_getter={}, style_change_handler={}):
        """ typename -> object idenfier;
            name -> object name;
            custom_style_setter: lambda accepts style, value, priority;
            custom_style_getter: lambda accepts name;
            style_change_handler: lambda accepts oldstyle, newstyle;
        """

        self.typename = typename
        self.name = name
        self.classnames = []
        self.style = [css.Style(), css.Style()]        # style stack
        self.computed_style = None
        self.custom_style_setter = custom_style_setter   # dict of lambda exprs.
        self.custom_style_getter = custom_style_getter
        self.style_change_handler = style_change_handler
        self.render_callback = None

    def update_style(self, style_dict={}, priority=1, **ex_styles):
        """ Update style from style_dict (and ex_styles).
        If a name is in custom_style_setter, it will be called to get real value;
        Otherwise will call default setter.

        Will not raise expression if a style is not found.
        """

        has_updated = False

        target = self.style[priority]
        ex_styles.update(style_dict)
        for d, v in ex_styles.items():
            if d in self.custom_style_setter:
                self.custom_style_setter[d](target, v)
                has_updated = True
            elif d in defaults.default_style_entries[self.typename]:
                target[d] = v
                has_updated = True
            else:
                warnings.warn('Skipping invalid style: "%s"' % d)

        return has_updated

    def remove_style(self, name, priority=1):
        """ Remove certain value in styles. Won't raise error if failed.
        """
        self.style[priority].pop(name, None)

    def clear_style(self, priority=1):
        """ Remove value in styles
        """
        if priority == 'all':
            for s in self.style:
                s.clear()
        else:
            self.style[priority].clear()

    def get_style(self, name, raise_error=True, default=None):
        """ Get value of style.
        The query is processed by priority - if highest priority style
        has entry, return the value; otherwise look for lower priority.
        Finally look at computed_style.

        raise KeyError if value not found.
        """
        for s in reversed(self.style):
            if name in self.custom_style_getter:
                return self.custom_style_getter[name](s)
            try:
                return s[name]
            except KeyError:
                pass
        if self.computed_style is None:
            if raise_error:
                raise KeyError(name)
            else:
                return default
        else:
            try:
                return self.computed_style[name]
            except KeyError:
                if raise_error:
                    raise
                else:
                    return default

    def attr(self, name):
        """ Alias for get_computed_style
        """
        return self.computed_style[name]

    def export_style(self):
        """ Export style to Style object
        Not include computed_style
        """
        ret = self.style[0].copy()
        ret.update(self.style[1])
        return ret

    def get_computed_style(self, name):
        """ Lower level get style for backend.
        """
        return self.computed_style[name]

    def on_style_updated(self, old_style, new_style):
        for s, v in self.style_change_handler.items():
            oldst = old_style.get(s, None)
            newst = new_style[s]
            if oldst != newst:
                v(oldst, newst)

    def add_class(self, name):
        """ Add a name to class
        """
        if name not in self.classnames:
            self.classnames.append(name)

    def remove_class(self, name):
        """ Remove style class without error
        """
        try:
            self.classnames.pop(self.classnames.index(name))
        except ValueError:
            pass

    def has_name(self, name):
        return name == self.name

    def get_children(self):
        return []
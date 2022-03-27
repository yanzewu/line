
import warnings

from . import css
from . import style
from . import keywords
from . import defaults
from . import errors


class FigObject:
    """ Style-modifiable object in the figure.
    """

    def __init__(self, typename:str, name:str, custom_style_setter:dict={}, custom_style_getter:dict={}, style_change_handler:dict={}, **init_styles):
        """ typename: object idenfier;
            name: object name;
            custom_style_setter: dict[name:str, (style:css.Style, value:Any)->Any] overrides the update_style() behavior;
            custom_style_getter: dict[name:str, style:css.Style->value:Any] overrides the get_style() behavior;
            style_change_handler: dict[name:str, (old_val, new_val)->Any] invoked when compute_style() finds a update;
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
        self.update_style(init_styles)

    def __str__(self):
        return '%s[%s]' % (self.typename, self.name)

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
        # TODO for 'clustered' styles, the merge is taken element-wise. (but this only affects display, not real calculation)
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

        # special care about 'clusted styles'
        for s in keywords.clustered_styles.intersection(ret):
            if s in self.style[0] and s in self.style[1]:
                v1 = style.merge_cluster_styles(self.style[0][s], self.style[1][s]) # 1 has a higher priority.
            elif s in self.style[0]:
                v1 = self.style[0][s]
            elif s in self.style[1]:
                v1 = self.style[1][s]

            if self.computed_style and s in self.computed_style:
                ret[s] = style.merge_cluster_styles(self.computed_style[s], v1)
            else:
                ret[s] = style.merge_cluster_styles(defaults.default_style_sheet.find_type(self.typename)[s], v1)
        return ret

    def get_computed_style(self, name):
        """ Lower level get style for backend.
        """
        return self.computed_style[name]

    def on_style_updated(self, old_style, new_style):
        for s, v in self.style_change_handler.items():
            oldst = old_style.get(s, None)
            newst = new_style.get(s, None)
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

    def get_all_children(self, pred=None):
        """ Returns all child and self, if pred is None
        or pred(self) == True
        """
        if pred is None or pred(self):
            yield self
        for c in self.get_children():
            yield from c.get_all_children(pred)

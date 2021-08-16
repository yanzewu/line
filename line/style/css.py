
import enum
import re

from . import errors
from .literal import is_inheritable_style, is_copyable_style, translate_style_val

_selector_matcher = re.compile(r'(?P<a>[\.\#\s]?[^\.#{\s\[]+)\s*((?P<b>[\#]?[^\.#{\s\[]+)|(?P<c>\[\w+\=[\w\,]+\]))?')


class SpecialStyleValue(enum.Enum):
    INHERIT = 1
    DEFAULT = 2


class Style(dict):
    """ A dict-like class supporting inherit and selective copy.
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def copy_from(self, other):
        self.update({
            (d, v) for (d, v) in other.items() if is_copyable_style(d)
        })

    def inherit_from(self, other):
        self.update({
            (d, v) for (d, v) in other.items() if is_inheritable_style(d)
        })

    def export(self):
        return self.copy()
        

class ResetStyle:
    pass


class Stylable:
    """ Not actually used. Describe the interfaces of element used by CSS.
    """
    def __init__(self):
        self.typename = ""              # str
        self.classnames = []            # list of str
        self.computed_style = None      # dict

    def has_name(self, name:str)->bool:
        """ Whether having the `name`
        """
        return False            # return bool

    def get_children(self)->list:
        """ Return all children elements
        """
        return []               # return list of Stylable

    def get_style(self, key:str, raise_error:bool):
        """ Return corresponding style value. 
        If `raise_error` is set, raises `KeyError` if key not found.
        """
        return None

    def export_style(self)->dict:
        """ Return the style calculated.
        """
        return {}

    def on_style_updated(self, old_style:dict, new_style:dict):
        """ Called after style is calculated.
        """
        pass


class Selector:
    """ Base class of selector
    """ 
    def select(self, stylable):
        """ Return elements and specificity
        """
        ret = []
        self._select(stylable, ret)
        return ret

    def __hash__(self):
        return hash(self.__str__())

    def __eq__(self, other):
        return isinstance(other, Selector) and self.__str__() == other.__str__()
        

class AllSelector(Selector):
    """ Select all
    """

    WEIGHT = -1

    def _select(self, stylable, ret):
        ret.append((stylable, -1))
        for child in stylable.get_children():
            self._select(child, ret)


class TypeSelector(Selector):
    """ Select element by element.typename
    """
    WEIGHT = 0

    def __init__(self, typename):
        self.typename = typename

    def _select(self, stylable, ret):
        if stylable.typename == self.typename:
            ret.append((stylable, self.WEIGHT))
        for child in stylable.get_children():
            self._select(child, ret)

    def __str__(self):
        return self.typename


class ClassSelector(Selector):
    """ Select element by element.classnames
    """
    WEIGHT = 10

    def __init__(self, classname):
        self.classname = classname

    def _select(self, stylable, ret):
        if self.classname in stylable.classnames:  # this does not consider the order of class
            ret.append((stylable, self.WEIGHT + stylable.classnames.index(self.classname)))
        for child in stylable.get_children():
            self._select(child, ret)

    def __str__(self):
        return '.' + self.classname


class ClassTypeSelector(Selector):

    WEIGHT = 20

    def __init__(self, classname, typename):
        self.classname = classname
        self.typename = typename

    def _select(self, stylable, ret):
        if self.classname in stylable.classnames:
            for child in stylable.get_children():
                self._select2(child, ret, stylable.classnames.index(self.classname))
        else:
            for child in stylable.get_children():
                self._select(child, ret)

    def _select2(self, stylable, ret, order):
        if self.typename == stylable.typename:
            ret.append((stylable, self.WEIGHT + order))
        for child in stylable.get_children():
            self._select2(child, ret, order) 

    def __str__(self):
        return '.%s %s' % (self.classname, self.typename)


class StyleSelector(Selector):

    WEIGHT = 30

    def __init__(self, stylename, styleval):
        self.stylename = stylename
        self.styleval = styleval

    def _select(self, stylable, ret):
        if stylable.get_style(self.stylename, raise_error=False) == self.styleval:
            ret.append((stylable, self.WEIGHT))
        for child in stylable.get_children():
            self._select(child, ret)        

    def __str__(self):
        return '[%s=%s]' % (self.stylename, self.styleval)


class TypeStyleSelector(Selector):

    WEIGHT = 40

    def __init__(self, typename, stylename, styleval):
        self.typename = typename
        self.stylename = stylename
        self.styleval = styleval

    def _select(self, stylable, ret):
        if self.typename == stylable.typename and\
            stylable.get_style(self.stylename, raise_error=False) == self.styleval:
            ret.append((stylable, self.WEIGHT))
        for child in stylable.get_children():
            self._select(child, ret)   

    def __str__(self):
        return '%s[%s=%s]' % (self.typename, self.stylename, self.styleval)


class ClassStyleSelector(Selector):

    WEIGHT = 50

    def __init__(self, classname, stylename, styleval):
        self.classname = classname
        self.stylename = stylename
        self.styleval = styleval

    def _select(self, stylable, ret):
        if self.classname in stylable.classnames and stylable.get_style(self.stylename, raise_error=False) == self.styleval:
            ret.append((stylable, self.WEIGHT))

        for child in stylable.get_children():
            self._select(child, ret)

    def __str__(self):
        return '.%s [%s=%s]' % (self.classname, self.stylename, self.styleval)


class NameSelector(Selector):
    
    WEIGHT = 60

    def __init__(self, name):
        self.name = name

    def _select(self, stylable, ret):
        if stylable.has_name(self.name):
            ret.append((stylable, self.WEIGHT))
        for child in stylable.get_children():
            self._select(child, ret)

    def __str__(self):
        return '#' + self.name


class ClassNameSelector(Selector):
    """ Select child elements by style class
    """
    WEIGHT = 70

    def __init__(self, classname, name):
        self.classname = classname
        self.name = name

    def _select(self, stylable, ret):
        if self.classname in stylable.classnames:
            for child in stylable.get_children():
                self._select2(child, ret, stylable.classnames.index(self.classname))
        else:
            for child in stylable.get_children():
                self._select(child, ret)

    def _select2(self, stylable, ret, order):
        if stylable.has_name(self.name):
            ret.append((stylable, self.WEIGHT + order))
        for child in stylable.get_children():
            self._select2(child, ret, order) 

    def __str__(self):
        return '.%s #%s' % (self.classname, self.name)


class StyleSheet:
    
    def __init__(self, selectors=[], style=None):
        
        if isinstance(selectors, list):
            self.data = dict((s, style) for s in selectors)  # selector:style dict
        else:
            self.data = {selectors:style}

    def apply_to(self, stylable, *args, **kwargs) -> bool:
        """ Calculate used value of stylable (and its children)
        Additional args and kwargs are passed to stylable.update_style().
        Return True/False depending if anything is updated.
        """
        apply_queue = {}
        has_updated = False

        for selector, style in self.data.items():
            for element, priority in selector.select(stylable):
                if element not in apply_queue:
                    apply_queue[element] = []
                apply_queue[element].append((priority, style))

        for element, data in apply_queue.items():
            data.sort(key=lambda x:x[0])
            for priority, style in data:
                if isinstance(style, ResetStyle):
                    has_updated = True
                    element.clear_style(*args, **kwargs)
                else:
                    has_updated = element.update_style(style, *args, **kwargs) or has_updated

        return has_updated

    def set_as_default(self, stylable):
        """ Apply the stylesheet to default values;
        Restrictions:
        - Only TypeSelector will be allowed;
        - Must provide value for all style properties;
        - Priority does not apply here;
        """
        for selector, style in self.data.items():
            if isinstance(selector, TypeSelector):
                for element, priority in selector.select(stylable):
                    if not element.computed_style:
                        element.computed_style = style.copy()
                    else:
                        element.computed_style = dict(((d, v) for d, v in element.computed_style.items() if not is_copyable_style(d)))
                        element.computed_style.update(style)

    def select(self, stylable):
        """ Selecting element. Return a collection of selected elements.
        """

        selected = set()

        for selector, style in self.data.items():
            for element, priority in selector.select(stylable):
                selected.add(element)
        return selected

    def update(self, other, overwrite_exist:bool=False):
        """ Update style from other stylesheet.
        If `overwrite_exist', replaces the exisiting selector.
        """

        for selector, style in other.data.items():
            if selector not in self.data:
                self.data[selector] = style
            else:
                if overwrite_exist:
                    self.data[selector] = style
                else:
                    self.data[selector].update(style)

    def find(self, key:Selector) -> Style:
        """ Find in the stylesheet. Key is a selector.
        """
        return self.data[key]

    def find_type(self, key:str) -> Style:
        """ Equivalent to find(TypeSelector(key))
        """
        return self.data[TypeSelector(key)]


def compute_inheritance(stylable, parent_style, default_stylesheet):
    """ Compute inheritance and write into computed_style
    """

    default_style = default_stylesheet.find(TypeSelector(stylable.typename))
    old_computed_style = {} if not stylable.computed_style else stylable.computed_style.copy()

    if not stylable.computed_style:
        stylable.computed_style = default_style.copy()
    else:
        stylable.computed_style = dict(((d, v) for d, v in stylable.computed_style.items() if not is_copyable_style(d)))
        stylable.computed_style.update(default_style)

    for d, v in stylable.export_style().items():
        if v is SpecialStyleValue.INHERIT:
            if is_inheritable_style(d):
                try:
                    stylable.computed_style[d] = parent_style[d]
                except KeyError:
                    raise errors.LineProcessError('Cannot inherit style: "%s"' % d)
            else:
                raise errors.LineProcessError('Style %s is not inheritable' % d)
        elif v is SpecialStyleValue.DEFAULT:
            if not is_copyable_style(d):
                raise errors.LineProcessError('There is no default value for %s' % d)
        else:
            stylable.computed_style[d] = v

    stylable.on_style_updated(old_computed_style, stylable.computed_style)

    for c in stylable.get_children():
        compute_inheritance(c, stylable.computed_style, default_stylesheet)
        

def compute_style(stylable, default_stylesheet):
    """ Compute default and inherit for computed_style for stylable.
    """

    #default_stylesheet.set_as_default(stylable)
    compute_inheritance(stylable, {}, default_stylesheet)

    
def parse_selector(selector):
    m_selector = _selector_matcher.match(selector)
    if m_selector is None:
        raise errors.LineParseError('Invalid selection: %s' % selector)
    else:
        try:
            return _parse_selector_with_match(m_selector)
        except (RuntimeError, AssertionError):
            raise errors.LineParseError('Invalid selection: %s' % selector)


def _parse_selector_with_match(seletor_match):

    if seletor_match.group('a'):
        _token1 = seletor_match.group('a')
        if seletor_match.group('b'):
            _token2 = seletor_match.group('b')
            assert _token1[0] == '.'
            if _token2[0] == '#':
                return ClassNameSelector(_token1[1:], _token2[1:])
            else:
                return ClassTypeSelector(_token1[1:], _token2)

        elif seletor_match.group('c'):
            assert _token1[0] != '#'
            name, value = seletor_match.group('c')[1:-1].split('=', 1)
            name = name.strip()
            value = translate_style_val(name, value)
            if _token1[0] == '.':
                return ClassStyleSelector(_token1[1:], name, value)
            else:
                return TypeStyleSelector(_token1, name, value)

        else:
            if _token1[0] == '.':
                return ClassSelector(_token1[1:])
            elif _token1[0] == '#':
                return NameSelector(_token1[1:])
            else:
                return TypeSelector(_token1)

    elif seletor_match.group('c'):
        name, value = seletor_match.group('c')[1:-1].split('=', 1)
        name = name.strip()
        value = translate_style_val(name, value)
        return StyleSelector(name, value)

    else:
        raise RuntimeError('Error in parsing selector')


def load_css(fp):
    text = (''.join((line.strip('\n') for line in fp.readlines()))).rstrip()

    comment_matcher = re.compile(r'\/([^\/]|\/[^\*])*\*\/')
    selector_matcher = _selector_matcher
    parentheses_matcher = re.compile(r'\{([^\}]*)\}')
    value_matcher = re.compile(r'([^:;]+)\:([^;]+)\;\s*')

    text = comment_matcher.sub('', text)

    def fail_parse(t):
        raise RuntimeError('Failed to load CSS near %s' % t[:5])

    clean_str = lambda x: x.strip(' \t\'\"')
    ss = StyleSheet()

    while len(text) > 0:
        text = text.strip()
        m_selector = selector_matcher.match(text)
        if m_selector is None:
            fail_parse(text)
        selector = _parse_selector_with_match(m_selector)

        text = text[m_selector.end():].strip()
        m_parentheses = parentheses_matcher.match(text)
        if m_parentheses is None:
            fail_parse(text)
        text = text[m_parentheses.end():].strip()

        content = m_parentheses.group(1).rstrip()
        style = {}
        while len(content) > 0:
            m_value = value_matcher.match(content)
            if m_value is None:
                fail_parse(content)
            name, val = clean_str(m_value.group(1)), clean_str(m_value.group(2))
            style[name] = translate_style_val(name, val)
            content = content[m_value.end():]
        ss.data[selector] = style

    return ss
    

def save_css(fp, stylesheet:StyleSheet):
    
    for selector, style in stylesheet.data:
        fp.write(str(selector) + '{\n')
        for d, v in style:
            fp.write('\t%s:%s\n' % (d, v))
        fp.write('}\n')
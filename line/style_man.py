
import enum
import re

from .keywords import is_inheritable, is_copyable
from .collection_util import RestrictDict
from .errors import LineProcessError, LineParseError
from .parse import translate_style_val

_selector_matcher = re.compile(r'(?P<a>[\.\#\s]?[^\.#{\s\[]+)\s*(?P<b>[\#]?[^\.#{\s\[]+)?|(?P<c>\[\w+\=[\w\,]+\])')


class SpecialStyleValue(enum.Enum):
    INHERIT = 1
    DEFAULT = 2


class Style(dict):
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def copy_from(self, other):
        self.update({
            (d, v) for (d, v) in other.items() if is_copyable(d)
        })

    def inherit_from(self, other):
        self.update({
            (d, v) for (d, v) in other.items() if is_inheritable(d)
        })

    def clear(self):
        for d in self.data:
            if is_inheritable(d):
                d = SpecialStyleValue.INHERIT
            elif is_copyable(d):
                d = SpecialStyleValue.DEFAULT

    def export(self):
        return self.copy()
        

class ResetStyle:
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
        if stylable.style.get(self.stylename, None) == self.styleval:
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
        if self.typename == styable.typename and\
            stylable.style.get(self.stylename, None) == self.styleval:
            ret.append((stylable, self.WEIGHT))
        for child in stylable.get_children():
            self._select(child, ret)   

    def __str__(self):
        return '%s[%s=%s]' % (self.typename, self.stylename, self.styleval)


class NameSelector(Selector):
    
    WEIGHT = 50

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
    WEIGHT = 60

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

    def apply_to(self, stylable):
        """ Calculate used value of stylable (and its children)
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
                    element.style.clear()
                else:
                    has_updated = element.update_style(style) or has_updated

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
                    element.computed_style = style.copy()

    def select(self, stylable):
        """ Selecting element
        """

        selected = set()

        for selector, style in self.data.items():
            for element, priority in selector.select(stylable):
                selected.add(element)
        return selected

    def update(self, other):
        """ Update style from other stylesheet.
        """

        has_updated = False

        for selector, style in other.data.items():
            if selector not in self.data:
                self.data[selector] = style
                has_updated = True
            else:
                has_updated = self.data[selector].update(style) or has_updated

        return has_updated


def compute_inheritance(stylable, parent_style={}):
    """ Compute inheritance and write into computed_style
    """

    for d, v in stylable.style.items():
        if v == SpecialStyleValue.INHERIT:
            if is_inheritable(d):
                try:
                    stylable.computed_style[d] = parent_style[d]
                except KeyError:
                    raise LineProcessError('Cannot inherit style: "%s"' % d)
            else:
                raise LineProcessError('Style %s is not inheritable' % d)
        elif v ==  SpecialStyleValue.DEFAULT:
            if not is_copyable(d):
                raise LineProcessError('There is no default value for %s' % d)
        else:
            stylable.computed_style[d] = stylable.style[d]

    for c in stylable.get_children():
        compute_inheritance(c, stylable.computed_style)
        

def compute_style(stylable, default_stylesheet):
    """ Compute default and inherit for computed_style for stylable.
    """

    default_stylesheet.set_as_default(stylable)
    compute_inheritance(stylable)

    
def parse_selector(selector):
    m_selector = _selector_matcher.match(selector)
    if m_selector is None:
        raise LineParseError('Invalid selection: %s' % selector)
    else:
        try:
            return _parse_selector_with_match(m_selector)
        except (RuntimeError, AssertionError):
            raise LineParseError('Invalid selection: %s' % selector)


def _parse_selector_with_match(seletor_match):

    if seletor_match.group('a'):
        _token1 = seletor_match.group('a')
        if seletor_match.group('b'):
            _token2 = seletor_match.group('b')
            assert _token1[0] == '.'
            if _token2[0] == '#':
                return ClassNameSelector(_token1[1:], _token2[1:])
            else:
                return ClassTypeSelector(_token1[1:], _token2[1:])

        elif seletor_match.group('c'):
            assert _token1[0] not in '.#'
            name, value = seletor_match.group('c').split('=', 1)
            value = parse_general(value.strip().rstrip())
            return TypeStyleSelector(_token1, name.strip().rstrip(), value)

        else:
            if _token1[0] == '.':
                return ClassSelector(_token1[1:])
            elif _token1[0] == '#':
                return NameSelector(_token1[1:])
            else:
                return TypeSelector(_token1)

    elif seletor_match.group('c'):
        name, value = seletor_match.group('c').split('=', 1)
        value = parse_general(value.strip().rstrip())
        return StyleSelector(name.strip().rstrip(), value)

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
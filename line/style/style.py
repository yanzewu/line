
import enum
import colorsys
from collections import namedtuple

PositionStyle = enum.Enum('PositionStyle', 'TOPLEFT TOPMID TOPRIGHT BOTTOMLEFT BOTTOMMID BOTTOMRIGHT')

class LineType(enum.Enum):
    SOLID = 0
    DASH = 1
    DOT = 2
    DASHDOT = 3 
    NONE = 4

    def to_str(self):
        return LineTypeStr[self.value]

LineTypeStr = ('-', '--', ':', '-.', '')

class PointType(enum.Enum):
    CIRCLE = 0 
    PLUS = 1
    ASTERISK = 2
    POINT = 3
    CROSS = 4
    SQUARE = 5
    DIAMOND = 6
    TRIANGLEUP = 7
    TRIANGLEDOWN = 8
    TRIANGLERIGHT = 9
    TRANGLELEFT = 10
    PENTAGRAM = 11
    HEXAGRAM = 12
    NONE = 13

    def to_str(self):
        return PointTypeStr[self.value]

PointTypeStr = ('o','+','*', '.', 'x', 's', 'd', '^', 'v', '>', '<', 'p', 'h', '')

class Color:

    RED = (1, 0, 0)
    YELLOW = (1, 1, 0)
    GREEN = (0, 1, 0)
    BLUE = (0, 0, 1)
    CYAN = (0, 1, 1)
    MAGENTA = (1, 0, 1)
    WHITE = (1, 1, 1)
    BLACK = (0, 0, 0)
    GREY = (0.5, 0.5, 0.5)

    def __init__(self, r, g, b):
        self.data = (r, g, b)

    def __index__(self, i):
        return self.data[i]

    def __iter__(self):
        return iter(self.data)

    def __len__(self):
        return 3

    def __str__(self):
        rawstr = hex(int(self.data[0]*255)*65536+int(self.data[1]*255)*256+int(self.data[2]*255))[2:]
        return '#' + '0'*(6-len(rawstr)) + rawstr


ShortColorStr = 'rygbcmwk'
ShortColorAlias = {
    'r':'RED',
    'y':'YELLOW',
    'g':'GREEN',
    'b':'BLUE',
    'c':'CYAN',
    'm':'MAGENTA',
    'w':'WHITE',
    'k':'BLACK'
}

# mapping color to nice-looking colors
VisualColors = {
    'RED':'e71a1a',
    'YELLOW':'DARKORANGE',
    'GREEN':'GREEN',
    'BLUE':'ROYALBLUE',
    'CYAN':'DARKTURQUOISE',
    'MAGENTA':'d740c7'
}

LighterColor = {
    'RED':'LIGHTCORAL',
    'YELLOW':'GOLD',
    'GREEN':'LIGHTGREEN',
    'BLUE':'LIGHTBLUE',
    'MAGENTA':'VIOLET',
    'BLACK':'GREY'
}

def lighten_color(r, g, b):
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    return colorsys.hsv_to_rgb(h, s, min(v+0.2, 1.0))


def darken_color(r, g, b):
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    return colorsys.hsv_to_rgb(h, s, min(v-0.2, 1.0))


def str2color(s):

    if len(s) == 1:
        c = ShortColorAlias[s]
        return str2color(VisualColors.get(c,c))

    if s.startswith('#'):
        s = s[1:]

    try:
        v = int(s, 16)
    except ValueError:
        return Color.__dict__[s.upper()]
    else:
        return Color( (v//0x10000)/256, ((v % 0x10000)//0x100)/256, (v % 0x100)/256)

def list2color(s):
    if s[0] > 1 or s[1] > 1 or s[2] > 1:
        return Color(s[0]/255, s[1]/255, s[2]/255)
    else:
        return Color(s[0], s[1], s[2])


class FloatingPos(enum.Enum):

    AUTO = 0
    CENTER = 1
    LEFT = 2
    RIGHT = 3
    OUTLEFT = 4
    OUTRIGHT = 5
    TOP = 6
    BOTTOM = 7
    OUTTOP = 8
    OUTBOTTOM = 9
    
    def _is_horizontal(self):
        return self.value >= 1 and self.value <= 5
    
    def _is_vertical(self):
        return self.value == 1 or (self.value >= 6 and self.value <= 9)

def str2pos(s):

    if s == 'auto':
        return FloatingPos.AUTO
    elif s == 'center':
        return (FloatingPos.CENTER, FloatingPos.CENTER)
    try:
        v1, v2 = s.split(',')
    except ValueError:
        raise ValueError('Invalid value: "%s"' % s)

    def _convert(val):
        if val == 'auto':
            raise ValueError('auto is not allowed')
        try:
            return FloatingPos.__members__[val.upper()], False
        except KeyError:
            return float(val), True

    m_v1, is_num1 = _convert(v1)
    m_v2, is_num2 = _convert(v2)

    if (is_num2 and not is_num1 and not m_v1._is_horizontal() or
        is_num1 and not is_num2 and not m_v2._is_vertical()):
        raise ValueError('Horizontal/vertical not match')

    if not is_num1 and not is_num2:
        if m_v1._is_vertical() and m_v2._is_horizontal():
            return (m_v2, m_v1)
        elif not (m_v1._is_horizontal() and m_v2._is_vertical()):
            raise ValueError('Horizontal/vertical not match')

    return (m_v1, m_v2)


class Padding:

    def __init__(self, *args):
        if len(args) == 1:
            if isinstance(args[0], (int, float)):
                self.data = [args[0]] * 4
            elif len(args[0]) == 2:
                self.data = [args[0][0], args[0][1], args[0][0], args[0][1]]
            elif len(args[0]) == 4:
                self.data = list(args[0])
            else:
                raise ValueError(args)
        elif len(args) == 2:
            self.data = [args[0], args[1], args[0], args[1]]
        elif len(args) == 4:
            self.data = [args[0], args[1], args[2], args[3]]
        else:
            raise ValueError(args)

    def left(self):
        return self.data[0]
    
    def bottom(self):
        return self.data[1]

    def right(self):
        return self.data[2]

    def top(self):
        return self.data[3]

    def __getitem__(self, idx):
        return self.data[idx]

    def __setitem__(self, idx, val):
        self.data[idx] = val

    def __str__(self):
        return '(%g,%g,%g,%g)' % tuple(self.data)

    def __len__(self):
        return 4

    def __eq__(self, other):
        if isinstance(other, Padding):
            return self.data == other.data
        elif isinstance(other, (list, tuple)):
            return self.data == other
        else:
            return False

    def copy(self):
        return Padding(*self.data)

    def width(self):
        return 1 - self.data[0] - self.data[2]

    def height(self):
        return 1 - self.data[1] - self.data[3]

class Rect:
    
    def __init__(self, *args):
        if len(args) == 1:
            self.x, self.y, self.width, self.height = args[0]
        elif len(args) == 2:
            self.x = 0
            self.y = 0
            self.width, self.height = args
        else:
            self.x, self.y, self.width, self.height = args

    def __getitem__(self, idx):
        return (self.x, self.y, self.width, self.height)[idx]

    def update(self, value):
        self.x, self.y, self.width, self.height = value

    def left(self):
        return self.x

    def right(self):
        return self.x + self.width

    def top(self):
        return self.y + self.height

    def bottom(self):
        return self.y

    def __len__(self):
        return 4

    def __repr__(self):
        return '(x=%.2f, y=%.2f, w=%.2f, h=%.2f)' % (self.x, self.y, self.width, self.height)


class FontProperty:
    """ Properties other than fontfamily
    """

    _OPTIONS = {
        'style': ('normal', 'italic', 'oblique'),
        'variant': ('normal', 'small-caps'),
        'stretch': ( 'ultra-condensed', 'extra-condensed', 'condensed', 'semi-condensed', 'normal', 
            'semi-expanded', 'expanded', 'extra-expanded', 'ultra-expanded'),
        'weight': ('ultralight', 'light', 'normal', 'regular', 'book', 'medium', 'roman', 
        'semibold', 'demibold', 'demi', 'bold', 'heavy', 'extra bold', 'black' ),
        'size': ('xx-small', 'x-small', 'small', 'medium', 'large', 'x-large', 'xx-large'),
    }

    _UPDATORS = {
        'style': lambda x: x if x in FontProperty._OPTIONS['style'] else None,
        'variant': lambda x: x if x in FontProperty._OPTIONS['variant'] else None,
        'stretch': lambda x: x if x in FontProperty._OPTIONS['stretch'] else int(x),
        'weight': lambda x: x if x in FontProperty._OPTIONS['weight'] else int(x),
        'size': lambda x: x if x in FontProperty._OPTIONS['size'] else int(x),
    }

    def __init__(self, *args, **kwargs):
        """ If passed as args, its usage will be auto determined:
                - Any numbers (either in string or int) will be treated as size.
                - "normal" will reset all values other than size.
        If passed as kwargs, will try to fit the option, and numbers will be assigned to the property.
        """
        self._holder = {
            'style':'normal', 'variant':'normal', 'stretch':'normal', 'weight':'normal', 'size':'medium'
        }

        for a in args:
            if isinstance(a, int) or (isinstance(a, str) and a.isdigit()):
                self._holder['size'] = int(a)
            elif a == 'normal':
                self._holder.update({'style':'normal', 'variant':'normal', 'stretch':'normal', 'weight':'normal'})
            else:
                valid_a = False
                for o in self._OPTIONS:
                    if a in self._OPTIONS[o]:   # Ideally use a backmap
                        self._holder[o] = a
                        valid_a = True
                        break
                if not valid_a:
                    raise ValueError('Invalid argument for fontproperty: %s' % a)

        for k, v in kwargs.items():
            self.update(k, v)

    def export(self):
        return self._holder

    def update(self, option, value):
        if option in self._UPDATORS:
            v = self._UPDATORS[option](value)
            if v is None:
                raise ValueError('Incorrect value for font%s: %s' % (option, value))
            else:
                self._holder[option] = v
        else:
            raise ValueError('Incorrect option: font%s' % option)

    def copy(self):
        f = FontProperty()
        f._holder = self._holder.copy()
        return f

    def __getitem__(self, key):
        return self._holder[key]

    def __setitem__(self, key, val):
        return self.update(key, val)

    def __eq__(self, other):
        return self._holder == other._holder if isinstance(other, FontProperty) else False

    def __repr__(self):
        return "{size=%r, style=%r, weight=%r, stretch=%r, variant=%r}" % (
            self._holder['size'], self._holder['style'], self._holder['weight'], self._holder['stretch'], self._holder['variant'])

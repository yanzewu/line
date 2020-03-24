
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

class Color(tuple):

    RED = (1, 0, 0)
    YELLOW = (1, 1, 0)
    GREEN = (0, 1, 0)
    BLUE = (0, 0, 1)
    CYAN = (0, 1, 1)
    MAGENTA = (1, 0, 1)
    WHITE = (1, 1, 1)
    BLACK = (0, 0, 0)
    GREY = (0.5, 0.5, 0.5)

    def __new__(cls, r, g, b):
        self = super(Color, cls).__new__(cls, (r, g, b))
        return self

    def __str__(self):
        rawstr = hex(int(self[0]*256)*65536+int(self[1]*256)*256+int(self[2]*256))[2:]
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

    def __repr__(self):
        return '(x=%s, y=%s, w=%s, h=%s)' % (self.x, self.y, self.width, self.height)


import enum
from collections import namedtuple
from . import palette

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

def str2color(s):

    if len(s) == 1:
        c = ShortColorAlias[s]
        return Color.__dict__[VisualColors.get(c,c)]

    try:
        v = int(s, 16)
    except ValueError:
        return Color.__dict__[s.upper()]
    else:
        return Color( (v//0x10000)/256, ((v % 0x10000)//0x100)/256, (v % 0x100)/256)

# A good way to implement pos is considering the size of object
# but here I just use fixed coordinates
Str2Pos = {
    'topleft': (0.1,0.9),
    'centerleft': (0.1,0.6),
    'bottomleft':(0.1,0.2),
    'topright':(0.7,0.9),
    'centerright':(0.7,0.6),
    'bottomright':(0.7,0.2),
    'best': 'best'
}

def init():
    palette._load_palette_mpl()
    #palette._load_palette_seaborn()
    palette._load_colors_mpl()

init()
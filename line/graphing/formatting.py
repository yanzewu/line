
import math
import re

LATEX_G_FORMAT = re.compile(r'\%\.?\d*m')

def gen_tickformat(fmt:str):
    """ Generate function (value:float, pos:float -> format:str) from format string.
    Alongside C-style string, it supports:
    - %mP: show value as latex 10^b;
    - %mp: Like %mP, but only enable when 0<x<0.01 or x>100;
    - %[.2]m: Like %[.2]g, but show index as latex a x 10^b;
    """
    if r'%mp' in fmt:
        return lambda x, pos: fmt.replace('%mp', ('$\mathregular{10^{%d}}$' % math.log10(x)) if (x > 0 and x < 0.01 or x > 100) else '%.4G' % x)
    elif r'%mP' in fmt:
        return lambda x, pos: fmt.replace('%mP', ('$\mathregular{10^{%d}}$' % math.log10(x)) if x > 0 else '%.4G' % x)
    elif LATEX_G_FORMAT.findall(fmt):
        rem_string = []
        replacer = []
        old_start = 0
        for repl in LATEX_G_FORMAT.finditer(fmt):
            rem_string.append(fmt[old_start:repl.start()])
            old_start = repl.end()
            value1 = repl.group()[:-1] + 'g'
            replacer.append(lambda x: '$\mathregular{%s}$' % re.sub(r'e\+?(|\-)0*(\d+)', '\\\\times10^{\\1\\2}', (value1 % x)))
        rem_string.append(fmt[repl.end():])

        _rem_string = tuple(rem_string) # to avoid modification
        _replacer = tuple(replacer)
        return lambda x, _: ''.join((_rem_string[j] + _replacer[j](x) for j in range(len(_replacer)))) + _rem_string[-1]
    else:
        return lambda x, pos:fmt % x

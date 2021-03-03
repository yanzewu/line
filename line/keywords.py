
style_keywords = {
    'alpha',
    'bgcolor',
    'bin',
    'clip',
    'color',
    'colorid',
    'column',
    'coord',
    'dpi',
    'enabled',
    'edgecolor', 'edgewidth',
    'fillcolor', 'fillstyle',
    'fontfamily', 'fontweight', 'fontstyle', 'fontsize', 'fontprops',
    'format',
    'groupid',
    'height',
    'hold',
    'label',
    'xlabel', 'ylabel', 'x2label', 'y2label',
    'legend',
    'length', 'length-minor',
    'linewidth', 'linecolor', 'linetype', 'linewidth-minor',
    'margin', 'margin-top', 'margin-bottom', 'margin-left', 'margin-right',
    'minor',
    'norm',
    'orient', 'orient-minor',
    'padding', 'padding-top', 'padding-bottom', 'padding-left', 'padding-right',
    'palette',
    'pointsize', 'pointcolor', 'pointtype',
    'pos', 'rpos',
    'range', 'xrange', 'yrange', 'x2range', 'y2range',
    'scale', 'xscale', 'yscale', 'x2scale', 'y2scale',
    'size', 'rsize',
    'skippoint',
    'source',
    'hspacing', 'vspacing', 'spacing',
    'title',
    'tick', 'xtick', 'ytick', 'x2tick', 'y2tick',
    'text',
    'width',
    'visible',
    'zindex'
}

inheritable_styles = {
    'visible', 'fontfamily', 'fontprops', 'color', 'linecolor'
}

style_alias = {
    'w':'linewidth',
    'c':'color',
    't':'label',
    'lw':'linewidth',
    'ps':'pointsize',
    'lt':'linetype',
    'pt':'pointtype',
    'lc':'linecolor',
    'pc':'pointcolor',
    'ec': 'edgecolor',
    'tics':'tick',
    'xtics':'xtick',
    'ytics':'ytick',
    'xlim': 'xrange',
    'ylim': 'yrange',
    'font': 'fontfamily',
    'fontname': 'fontfamily',
}

element_keywords = {
    'figure', 'subfigure', 'axis', 'label', 'tick', 'legend',
    'grid', 'line', 'drawline', 'polygon', 'text'
}

command_keywords = {
    'append',
    'cd',
    'clear',
    'display',
    'figure',
    'fill',
    'fit',
    'group',
    "hist",
    'input',
    'load',
    'line', 'hline', 'vline',
    'ls',
    'pause',
    'plot',
    'plotr',
    'print',
    'pwd',
    'quit',
    'remove',
    'replot',
    'save',
    'set',
    'split', 'hsplit', 'vsplit',
    'show',
    'subfigure',
    'text',
    'update',
}

command_alias = {
    'cla':'clear',
    'q':'quit',
    'exit':'quit',
    'p':'plot',
    'a':'append',
    's': 'set',
    'add':'append',
    'subplot': 'subfigure',
    'sp': 'subfigure',
    'fig': 'figure',
    'plotyy': 'plotr',
}

extended_set_keywords = {
    'grid', 'hold', 'legend', 'palette', 'title',
    'xlabel', 'ylabel',
    'xrange', 'yrange',
    'xscale', 'yscale',
    'style'
}

control_keywords = {
    'if', 'then', 'else', 'for', 'do', 'let', 'call',
}

def is_style_keyword(token):

    return token in style_alias or token in style_keywords

def is_style_desc(token):

    return len(token) <= 4 and all((
        t in 'o+*.xsd^v><ph-:.rgbcmwk' and (t == '-' or token.count(t) == 1)
        for t in token
        ))


all_style_keywords = style_keywords.union(list(style_alias.keys()))
all_command_keywords = command_keywords.union(list(command_alias.keys()))

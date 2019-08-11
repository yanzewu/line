
style_keywords = set([
    'alpha',
    'bgcolor',
    'color',
    'coord',
    'dpi',
    'edgecolor', 'edgewidth', 'fillcolor',
    'font', 'fontfamily', 'fontsize',
    'format',
    'label', 'xlabel', 'ylabel', 'rlabel', 'tlabel',
    'linewidth', 'linecolor', 'linetype',
    'margin', 'margin-top', 'margin-bottom', 'margin-left', 'margin-right',
    'orient',
    'padding', 'padding-top', 'padding-bottom', 'padding-left', 'padding-right',
    'palette',
    'pointsize', 'pointcolor', 'pointtype',
    'pos', 'rpos',
    'range', 'xrange', 'yrange',
    'size', 'rsize',
    'skippoint',
    'hspacing', 'vspacing', 'spacing',
    'title',
    'tick', 'xtick', 'ytick', 'rtick', 'ttick',
    'text',
    'visible',
    'zindex'
])


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
    'tics':'tick',
    'xtics':'xtick',
    'ytics':'ytick'
}

command_alias = {
    'cla':'clear',
    'q':'quit',
    'exit':'quit',
    'p':'plot',
    'a':'append',
    'add':'append',
    'sel':'select'
}

def is_style_keyword(token):

    return token in style_alias or token in style_keywords
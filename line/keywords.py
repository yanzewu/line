
# Single-valued style keywords
style_keywords = set([
    'size', 
    'margin', 'margin-top', 'margin-bottom', 'margin-left', 'margin-right',
    'hspacing', 'vspacing', 'spacing',
    'padding', 'padding-top', 'padding-bottom', 'padding-left', 'padding-right',
    'rsize',
    'rpos',
    'range', 'xrange', 'yrange',
    'label', 'xlabel', 'ylabel',
    'tick', 'xtick', 'ytick',
    'width', 'color', 'type',
    'linewidth', 'linecolor', 'linetype',
    'pointsize', 'pointcolor', 'pointtype',
    'edgewidth', 'edgecolor', 'fillcolor',
    'font', 'fontfamily', 'fontsize',
    'text',
    'format',
    'orient',
    'skippoint',
    'bgcolor',
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
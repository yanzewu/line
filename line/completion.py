
from . import keywords
from . import state
from . import io_util

def get_all_completions():
    return list(keywords.all_style_keywords) + io_util.get_cwd_files()

def get_completions(m_state:state.GlobalState, tokens):
    
    if not tokens:
        return list(keywords.command_keywords)

    command = tokens[0]

    # command with no completion
    if command in ('group', 'split', 'hsplit', 'vsplit', 'subfigure', 'clear', 'replot', 
        'print', 'quit', 'input', 'display',):
        return []

    if command == 'figure':
        return list(m_state.figures.keys())
    
    # styles
    elif command in ('set', 'show', 'line', 'text', 'hline', 'vline', 'remove'):
        return list(keywords.style_keywords)

    elif command in ('save', 'load'):
        return io_util.get_cwd_files()

    elif command in ('plot', 'append'):
        if len(command) == 1 or tokens[-1] == ',':
            return io_util.get_cwd_files()
        else:
            return list(keywords.style_keywords)

        # TODO LOW FEATURE more smart support for completion for plot.

    else:
        return []
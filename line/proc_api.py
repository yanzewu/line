
""" Common functions used by process and api
"""

from . import state
from . import style
from .positioning import split, subfigure_arr
from .style import palette as palette_
from .errors import LineProcessError


def palette(m_state:state.GlobalState, palette_name:str, target:str='line', target_style='color', snapshot_callback=None):
    """ set palette to current subfigure.
    """

    if target == 'point':
        target = 'line'
        target_style = 'fillcolor'

    try:
        m_palette = palette_.get_palette(palette_name)
    except KeyError:
        raise LineProcessError('Palette "%s" does not exist' % palette_name)
    else:
        if snapshot_callback:
            snapshot_callback(m_state)
        palette_.palette2stylesheet(m_palette, target, target_style).apply_to(m_state.cur_subfigure())
        m_state.cur_subfigure().is_changed = True

set_cmap = palette

def subfigure(m_state:state.GlobalState, *args, force_split=False):
    """ subfig (idx) => set current subfigure to idx;
        subfig (a, b, idx) => split, set current subfigure to idx

    force_split: redo split and alignment even if subfigure number does not change.
    """
    m_state.cur_figure(True)
    split_num = None
    if len(args) == 1:
        if args[0] > 100:
            subfig_idx = args[0] % 100 - 1
            split_num = (args[0] // 100, (args[0] // 10) % 10)
        else:
            subfig_idx = args[0] - 1
    elif len(args) == 3:
        subfig_idx = args[2] - 1
        split_num = (args[1], args[0])

    if split_num:
        hs, vs = m_state.cur_figure().get_style('split', raise_error=False, default=(1, 1))
        if force_split or hs != split_num[0] or vs != split_num[1]:
            split_figure(m_state, *split_num)

    if subfig_idx < len(m_state.cur_figure().subfigures):
        m_state.cur_figure().cur_subfigure = subfig_idx
        return m_state.cur_subfigure()
    else:
        raise LineProcessError('subfigure %d does not exist' % (subfig_idx + 1))


def split_figure(m_state:state.GlobalState, hsplitnum:int, vsplitnum:int):
    """ split current figure. 
    hsplit means split horizontally: | | | vsplit means split vertically - - -
    """
    if m_state._history:
        m_state._history.clear()
    split.split_figure(m_state.cur_figure(), hsplitnum, vsplitnum, m_state.options['resize-when-split'])
    m_state.refresh_style(True)
    split.align_subfigures(m_state.cur_figure(), 'axis')


def set_redraw(m_state:state.GlobalState, redraw_all_subfigures=True, compact=False):
    """ set the flag that current figure needs to be redraw.
    """
    if redraw_all_subfigures:
        m_state.cur_figure().is_changed = True
        if compact:
            m_state.cur_figure().needs_rerender = 2
    else:
        m_state.cur_subfigure().is_changed = True


def text(m_state:state.GlobalState, text:str, pos, style_dict:dict, snapshot_callback=None):
    m_state.cur_subfigure(True)
    if snapshot_callback:
        snapshot_callback(m_state)
    if isinstance(pos, str):
        pos = style.str2pos(pos)
    return m_state.cur_subfigure().add_text(text=text, pos=pos, **style_dict)

def line(m_state:state.GlobalState, startpos, endpos, style_dict:dict, snapshot_callback=None):
    m_state.cur_subfigure(True)
    if snapshot_callback:
        snapshot_callback(m_state)
    return m_state.cur_subfigure().add_drawline(startpos=startpos, endpos=endpos, **style_dict)


import itertools
import logging
from collections import deque
import os

import numpy as np

from . import defaults
from . import keywords
from . import io_util
from . import state
from . import plot
from . import cmd_handle

from .style import css
from .style import palette

from .parse import *
from .errors import LineParseError, LineProcessError, warn

expr_proc = None
plot_proc = None
dataview = None

logger = logging.getLogger('line')

def initialize():
    
    global expr_proc
    global plot_proc
    global dataview

    if expr_proc is None:
        from . import expr_proc as expr_proc_1
        expr_proc = expr_proc_1
    if plot_proc is None:
        from . import plot_proc as plot_proc_1
        plot_proc = plot_proc_1

    if dataview is None:
        from . import dataview as dataview_1
        dataview = dataview_1

if defaults.default_options['delayed-init'] == False:
    initialize()


def parse_and_process_command(tokens, m_state:state.GlobalState):
    """ Parse and execute sequence of tokens.
    Args:
        tokens: list of string;
        m_state: GlobalState instance.

    Raises:
        LineParseError: Parsing errors;
        LineProcessError: Error of processing commands;
        others;
    """
    
    if len(tokens) == 0:
        return 0

    logger.debug('Tokens are: %s' % tokens)

    m_tokens = tokens

    m_state.file_caches.clear()
    if m_tokens[0].startswith('$'):
        try:
            asnidx = m_tokens.index('=')
        except ValueError:
            print(process_expr(m_state, ''.join(m_tokens)))
        else:
            varname = expr_proc.canonicalize(''.join(list(m_tokens)[:asnidx]))
            m_state.variables[varname] = process_expr(m_state, ''.join(list(m_tokens)[asnidx+1:]))
        return 0

    command = get_token(m_tokens)
    command = keywords.command_alias.get(command, command)   # expand short commands

    if command in keywords.extended_set_keywords:
        m_tokens.appendleft(command)
        command = 'set'

    do_prompt = m_state.is_interactive or m_state.options['prompt-always']   # prompt
    do_focus_up = False # update focus

    # Long commands

    if command == 'plot':
        parse_and_process_plot(m_state, m_tokens, keep_existed=None)

    elif command == 'append':
        parse_and_process_plot(m_state, m_tokens, keep_existed=True)

    elif command == 'hist':
        parse_and_process_hist(m_state, m_tokens)

    elif command == 'remove':
        parse_and_process_remove(m_state, m_tokens)

    elif command == 'group':
        parse_and_process_group(m_state, m_tokens)

    elif command == 'set':
        parse_and_process_set(m_state, m_tokens)

    elif command == 'show':
        parse_and_process_show(m_state, m_tokens)

    elif command == 'style':
        parse_and_process_style(m_state, m_tokens)

    elif command == 'line':
        x1, _, y1, x2, _, y2 = zipeval([stof, make_assert_token(','), stof, stof, make_assert_token(','), stof], m_tokens)
        
        m_state.cur_subfigure().add_drawline((x1,y1), (x2,y2), parse_style(m_tokens))
        m_state.cur_subfigure().is_changed = True

    elif command == 'hline':
        y = stof(get_token(m_tokens))
        m_state.cur_subfigure().add_drawline((None,y), (None,y), parse_style(m_tokens))
        m_state.cur_subfigure().is_changed = True

    elif command == 'vline':
        x = stof(get_token(m_tokens))
        m_state.cur_subfigure().add_drawline((x,None), (x,None), parse_style(m_tokens))
        m_state.cur_subfigure().is_changed = True

    elif command == 'fill':
        parse_and_process_fill(m_state, m_tokens)
        
    elif command == 'text':
        text = get_token(m_tokens)
        token1 = get_token(m_tokens)
        if lookup(m_tokens) == ',':
            get_token(m_tokens)
            m_state.cur_subfigure().add_text(text, style.str2pos(token1 + ',' + get_token(m_tokens)), parse_style(m_tokens))
        else:
            m_state.cur_subfigure().add_text(text, style.str2pos(token1), {**parse_style(m_tokens), **{'coord':'axis'}})

        m_state.cur_subfigure().is_changed = True

    elif command == 'split':
        hsplitnum, _, vsplitnum = zipeval([stod, make_assert_token(','), stod], m_tokens)
        assert_no_token(m_tokens)
        process_split(m_state, hsplitnum, vsplitnum)

    elif command == 'hsplit':
        splitnum = stod(get_token(m_tokens))
        assert_no_token(m_tokens)
        process_split(m_state, splitnum, m_state.cur_figure().attr('split')[1])

    elif command == 'vsplit':
        splitnum = stod(get_token(m_tokens))
        assert_no_token(m_tokens)
        process_split(m_state, m_state.cur_figure().attr('split')[0], splitnum)

    # select or create figure
    elif command == 'figure':
        if len(m_tokens) == 0:
            fig_name = None
        else:
            fig_name = get_token(m_tokens)
            assert_no_token(m_tokens)
        m_state.figure(fig_name)

        if m_state.is_interactive:
            do_focus_up = True

    # select subfigure
    elif command == 'subfigure':
        arg = stod(get_token(m_tokens))
        
        if m_state.cur_figurename is None:
            m_state.create_figure()
            redraw_cur_figure(m_state)

        m_fig = m_state.cur_figure()

        if lookup(m_tokens) == ',':
            vs = arg
            _, hs, _, subfig_idx = zipeval([make_assert_token(','), stod, make_assert_token(','), stod], m_tokens)
            if (hs, vs) != tuple(m_fig.attr('split')):
                process_split(m_state, hs, vs)
        else:
            subfig_idx = stod(arg)

        assert_no_token(m_tokens)

        subfig_idx -= 1
        if subfig_idx < len(m_fig.subfigures):
            m_fig.cur_subfigure = subfig_idx
        else:
            raise LineProcessError('subfigure %d does not exist' % (subfig_idx + 1))

    # save figure
    elif command == 'save':
        if len(m_tokens) == 0:
            warn('Using current filename: %s' % m_state.cur_save_filename)
            filename = m_state.cur_save_filename
        else:
            filename = get_token(m_tokens)
        assert_no_token(m_tokens)

        process_save(m_state, filename)

    elif command == 'clear':
        m_state.cur_subfigure().clear()

    elif command == 'replot':
        if lookup(m_tokens, 1) == 'all':
            m_state.cur_figure().is_changed = True
        else:
            m_state.cur_subfigure().is_changed = True

    elif command == 'print':
        outstr = ''
        while len(m_tokens) > 0:
            if m_tokens[0].startswith('$'):
                outstr += str(process_expr(m_state, parse_column(m_tokens)))
            else:
                outstr += m_tokens[0]
                m_tokens.popleft()
            if len(m_tokens) > 0:
                outstr += ' '
        print(outstr)

    elif command == 'quit':
        if m_state.options['display-when-quit'] and not m_state.is_interactive:
            plot.show(m_state)

        if m_state.options['prompt-save-when-quit']:
            if len(m_state.figures) == 1:
                if io_util.query_cond('Save current figure? ', do_prompt, False):
                    process_save(m_state, m_state.cur_save_filename)

            for name, figure in m_state.figures.items():
                m_state.cur_save_filename = None
                m_state.cur_figurename = name
                if io_util.query_cond('Save figure %s? ' % name, do_prompt, False):
                    process_save(m_state, '')
                if m_state.is_interactive:
                    plot.close_figure(m_state)

        return True

    elif command == 'input':
        m_state.is_interactive = True
        _cur_figurename = m_state.cur_figurename
        for fig in m_state.figures:
            m_state.cur_figurename = fig
            m_state.cur_figure().is_changed = True
            redraw_cur_figure(m_state)
        m_state.cur_figurename = _cur_figurename

    elif command == 'display':
        process_display(m_state)

    elif command == 'cd':
        dest = get_token(m_tokens)
        assert_no_token(m_tokens)
        
        if io_util.dir_exist(dest):
            os.chdir(dest)
        else:
            raise LineProcessError('Directory "%s" does not exist' % dest)

    elif command == 'load':
        filename = get_token(m_tokens)
        assert_no_token(m_tokens)
        process_load(m_state, filename)

    else:
        raise LineParseError('No command named "%s"' % command)

    if m_state.cur_figurename is None:
        return 0
    if not m_state.is_interactive:
        if m_state.cur_figure().is_changed:
            m_state.refresh_style(True)
        return 0

    # update figure
    if m_state.cur_figure().is_changed or m_state.cur_subfigure().is_changed:
        redraw_cur_figure(m_state)

    if do_focus_up:
        plot.update_focus_figure(m_state)

    return 0

def redraw_cur_figure(m_state:state.GlobalState):

    m_state.refresh_style(True)
    if m_state.cur_figure().is_changed:
        plot.update_figure(m_state, True)
        m_state.cur_figure().is_changed = False
        for m_subfig in m_state.cur_figure().subfigures:
            m_subfig.is_changed = False

    elif m_state.cur_subfigure().is_changed:
        plot.update_subfigure(m_state)
        m_state.cur_subfigure().is_changed = False 


def parse_and_process_plot(m_state:state.GlobalState, m_tokens:deque, keep_existed):
    """ Parsing and processing `plot` and `append` commands.

    Args:
        keep_existed: Keep existed datalines.
    """
    if keep_existed is None:
        if len(m_state.figures) > 0:
            keep_existed = m_state.cur_subfigure().get_style('hold')
        else:
            keep_existed = False

    parser = plot_proc.PlotParser()
    parser.parse(m_state, m_tokens)
    if parser.plot_groups:
        dataview.plot.do_plot(m_state, parser.plot_groups, keep_existed)
    else:
        warn('No data to plot')

def parse_and_process_hist(m_state:state.GlobalState, m_tokens:deque):
    if len(m_state.figures) > 0:
        keep_existed = m_state.cur_subfigure().get_style('hold')
    else:
        keep_existed = False

    parser = plot_proc.PlotParser(plot_proc.PlotParser.M_HIST)
    parser.parse(m_state, m_tokens)
    if parser.plot_groups:
        dataview.plot.do_plot(m_state, parser.plot_groups, keep_existed, chart_type='hist')
    else:
        warn('No data to plot')

def parse_and_process_remove(m_state:state.GlobalState, m_tokens:deque):
    """ Parse and process `remove` command.
    """
    m_subfig = m_state.cur_subfigure()

    selection = parse_style_selector(m_tokens)
    ss = css.StyleSheet(selection)
    elements = ss.select(m_state.cur_subfigure())

    if not elements:
        warn('No element is selected')
        return

    if len(elements) > 1:
        if io_util.query_cond('Remove elements %s?' % (' '.join(e.name for e in elements)), 
            m_state.options['prompt-multi-removal'] and (m_state.options['prompt-always'] or 
            m_state.is_interactive), True):
            pass
        else:
            return

    for e in elements:
        m_state.cur_subfigure().remove_element(e)

    m_state.cur_subfigure().is_changed = True


def parse_and_process_group(m_state:state.GlobalState, m_tokens:deque):
    group_descriptor = get_token(m_tokens)
    assert_no_token(m_tokens)
    if group_descriptor == 'clear':
        m_state.cur_subfigure().update_style({'group':None})
    else:
        m_state.cur_subfigure().update_style({'group': parse_group(group_descriptor)})
        logger.debug('Group is: %s' % str(m_state.cur_subfigure().get_style('group')))

    m_state.cur_subfigure().update_colorid()
    m_state.cur_subfigure().is_changed = True


def parse_and_process_set(m_state:state.GlobalState, m_tokens:deque):
    """ Parse and process `set` command.
    """
    # LL(2)
    
    if lookup(m_tokens) == 'option':
        get_token(m_tokens)

        while len(m_tokens) > 0:
            opt = get_token(m_tokens)
            arg = get_token(m_tokens)
            if arg == '=':
                arg = get_token(m_tokens)
            try:
                m_state.options.update(
                    defaults.parse_default_options({opt:arg}, 
                    option_range=defaults.default_options.keys(), raise_error=True
                ))
            except KeyError:
                raise LineParseError('Invalid option: "%s"' % opt)
            except ValueError:
                raise LineParseError('Invalid value for %s: "%s"' % (opt, arg))

    elif lookup(m_tokens) == 'default':
        get_token(m_tokens)

        if keywords.is_style_keyword(lookup(m_tokens)) and \
            lookup(m_tokens, 1) != ',' and (
            not keywords.is_style_keyword(lookup(m_tokens, 1)) or 
            (lookup(m_tokens, 1) not in ('on', 'off') and len(m_tokens) <= 2)):

            style_list = parse_style(m_tokens)
            selection = css.NameSelector('subfigure')
            # TODO automatically select candidate
        else:
            selection = parse_style_selector(m_tokens)
            for s in selection:
                if not isinstance(s, css.TypeSelector):
                    raise LineParseError('Only element names (e.g. figure, subfigure) are allowed')
            style_list = parse_style(m_tokens)

        ss = css.StyleSheet(selection, style_list)
        m_state.default_stylesheet.update(ss)

    elif lookup(m_tokens) == 'palette':
        get_token(m_tokens)
        if len(m_tokens) == 2:
            target = get_token(m_tokens)
        else:
            target = 'line'
        palette_name = get_token(m_tokens)
        assert_no_token(m_tokens)
        try:
            m_palette = palette.get_palette(palette_name)
        except KeyError:
            raise LineProcessError('Palette "%s" does not exist' % palette_name)
        palette.palette2stylesheet(m_palette, target).apply_to(m_state.cur_subfigure())
        m_state.cur_subfigure().is_changed = True

    else:
        has_updated = False

        # Setting cur_subfigure, recursively
        if keywords.is_style_keyword(lookup(m_tokens)) and lookup(m_tokens, 1) != 'clear' and \
            lookup(m_tokens, 1) != ',' and (
            not keywords.is_style_keyword(lookup(m_tokens, 1)) or 
            (lookup(m_tokens, 1) not in ('on', 'off') and len(m_tokens) <= 2)):
            # the nasty cases... either not a style keyword or not enough style parameters
            # that treated as value

            selection = css.NameSelector('gca')
            style_list, add_class, remove_class = parse_style(m_tokens, recog_class=True)
        else:
            selection = parse_style_selector(m_tokens)
            if lookup(m_tokens) == 'clear':
                get_token(m_tokens)
                assert_no_token(m_tokens)
                style_list = css.ResetStyle()
                add_class = []
                remove_class = []
            else:
                style_list, add_class, remove_class = parse_style(m_tokens, recog_class=True)
            
        ss = css.StyleSheet(selection, style_list)
        has_updated = process_set_style(m_state, ss, add_class, remove_class)

        if has_updated:
            m_state.cur_figure().is_changed = True
        else:
            warn('No style is set')


def parse_and_process_show(m_state:state.GlobalState, m_tokens:deque):
    """ Parse and process `show` command.
    """

    element_name = lookup(m_tokens)

    if element_name == 'currentfile':
        get_token(m_tokens)
        print('File saved:', m_state.cur_save_filename)

    elif element_name == 'pwd':
        print(os.getcwd())

    elif element_name in ('option',  'options'):
        get_token(m_tokens)
        if len(m_tokens) == 0:
            print('OPTION                          VALUE')
            print('------                          -----')
            for opt, val in m_state.options.items():
                print('%s%s%s' % (opt, ' '*(32-len(opt)), val))
        else:
            print(m_state.options[get_token(m_tokens)])
            assert_no_token(m_tokens)

    elif element_name in ('palette', 'palettes'):
        palette_names = list(palette.PALETTES)
        palette_names.sort()
        for i in range(8):
            print(' '.join(('%-15s' % palette_names[n] for n in range(8*i, min(8*i+8, len(palette_names))))))

    else:
        if not m_state.is_interactive:
            m_state.refresh_style(True)

        selection = parse_style_selector(m_tokens)
        ss = css.StyleSheet(selection, None)
        elements = ss.select(m_state.cur_figure())
        
        if len(elements) == 0:
            warn('No element to show')
            return

        # show all styles
        if len(m_tokens) == 0:
            for e in elements:
                print(e.name + ':')
                print('\n'.join(('%s =\t%s' % item for item in e.computed_style.items())))

        # show specified style
        else:
            for style_name in m_tokens:
                style_name = keywords.style_alias.get(style_name, style_name)
                if style_name not in keywords.style_keywords:
                    warn('Skip invalid style "%s"' % style_name)
                print('%s:' % style_name)
                print('\n'.join(('%s\t%s' % (e.name, e.computed_style.get(style_name, '<None>')) 
                    for e in elements)))
        

def parse_and_process_style(m_state:state.GlobalState, m_tokens):
    
    classname = get_token(m_tokens)
    style_list = parse_style(m_tokens)

    ss = css.StyleSheet(css.ClassSelector(classname), style_list)
    m_state.class_stylesheet.update(ss)


def parse_and_process_fill(m_state:state.GlobalState, m_tokens):
    fill_between = []
    while len(m_tokens) > 0:
        if keywords.is_style_keyword(lookup(m_tokens)):
            break
        token = get_token(m_tokens)
        try:
            if '-' in token:
                line1str, line2str = token.split('-', 1)
                line1 = [d for d in m_state.cur_subfigure().datalines if d.name == line1str][0]
                line2 = [d for d in m_state.cur_subfigure().datalines if d.name == line2str][0]
            else:
                line1 = [d for d in m_state.cur_subfigure().datalines if d.name == token][0]
                line2 = None
        except IndexError:
            warn('Skip line "%s" as it does not exist' % token)
        else:
            fill_between.append((line1, line2))

    style_dict = parse_style(m_tokens)
    if not fill_between:
        warn('No line to fill')
    else:
        for line1, line2 in fill_between:
            m_state.cur_subfigure().fill(line1, line2, **style_dict)


def process_set_style(m_state, style_sheet, add_class_list, remove_class_list):
    
    has_updated = style_sheet.apply_to(m_state.cur_figure())

    if len(add_class_list) > 0 or len(remove_class_list) > 0:

        selection = style_sheet.select(m_state.cur_figure())
        if selection is not None:
            for s in selection:
                for c in add_class_list:
                    s.add_class(c)
                for c in remove_class_list:
                    s.remove_class(c)

        has_updated = m_state.class_stylesheet.apply_to(m_state.cur_figure()) or has_updated

    return True


def process_split(m_state:state.GlobalState, hsplitnum:int, vsplitnum:int):
    """ Split current figure by certain grids.
    Will remove additional subfigures if necessary.
    """

    if hsplitnum < 1 or vsplitnum < 1:
        raise LineProcessError('Split number should be greater than 1, got %d' % max(hsplitnum, vsplitnum))

    m_fig = m_state.cur_figure()
    hsplit, vsplit = m_fig.attr('split')
    hspacing, vspacing = m_fig.attr('spacing')

    subfig_state_2d = []
    for i in range(vsplitnum):
        subfig_state_2d.append([])
        for j in range(hsplitnum):
            if i < vsplit and j < hsplit:
                subfig_state_2d[i].append(m_fig.subfigures[i*hsplit + j])
            else:
                subfig_state_2d[i].append(m_state.create_subfigure('subfigure%d' % (i*hsplitnum + j)))

            subfig_state_2d[i][j].update_style({'rpos': (
                j * (1 + hspacing) / hsplitnum,
                (vsplitnum - 1 - i) * (1 + vspacing) / vsplitnum
                ), 
                'rsize': (
                1 / hsplitnum -  (1 - 1/hsplitnum) * hspacing,
                1 / vsplitnum - (1 - 1/vsplitnum) * vspacing
            )})
    
    m_fig.subfigures = list(itertools.chain.from_iterable(subfig_state_2d))
    m_fig.is_changed = True
    
    if m_state.options['resize-when-split']:
        split_old = m_fig.get_style('split')
        size_old = m_fig.get_style('size')
        m_fig.update_style({'size': [
            np.round(size_old[0]*np.sqrt(hsplitnum/split_old[0] * split_old[1]/vsplitnum)), 
            np.round(size_old[1]*np.sqrt(vsplitnum/split_old[1] * split_old[0]/hsplitnum))]
            })

    m_fig.update_style({'split': [hsplitnum, vsplitnum]})
    if m_fig.cur_subfigure >= len(m_fig.subfigures):
        m_fig.cur_subfigure = 0


def process_save(m_state:state.GlobalState, filename:str):
    """ Saving current figure.
    """
    do_prompt = m_state.is_interactive or m_state.options['prompt-always']

    if not filename:
        if m_state.cur_save_filename:
            filename = io_util.query_cond('Enter filename here (default: %s): ' % m_state.cur_save_filename,
            do_prompt, m_state.cur_save_filename, False)
        else:
            filename = io_util.query_cond('Enter filename here: ', do_prompt, None, False)
        if not filename:
            logger.info('Saving cancelled')
            return

    if m_state.options['prompt-overwrite'] and io_util.file_exist(filename):
        if not io_util.query_cond('Overwrite current file "%s"? ' % filename, do_prompt, False):
            warn('Canceled')
            return

    plot.save_figure(m_state, filename)
    m_state.cur_save_filename = filename

def process_display(m_state:state.GlobalState):
    if not m_state.is_interactive:
        plot.show(m_state)

def process_expr(m_state:state.GlobalState, expr):
    evaler = expr_proc.ExprEvaler(m_state.variables, m_state.file_caches)
    evaler.load(expr, True)
    logger.debug(evaler.expr)
    return evaler.evaluate()

def process_load(m_state:state.GlobalState, filename):
    handler = cmd_handle.CMDHandler(m_state)
    is_interactive = m_state.is_interactive # proc_file() requires state to be non-interactive
    plot.finalize(m_state)
    
    cwd = os.getcwd()

    loadpaths = ['.', os.path.expanduser('~/.line/')]

    full_filename = None
    for path in loadpaths:
        if io_util.file_exist(os.path.join(path, filename)):
            full_filename = os.path.join(path, filename)
            break
    
    if not full_filename:
        raise LineProcessError('Cannot open file "%s"' % filename)

    handler.proc_file(full_filename)
    os.chdir(cwd)
    m_state.is_interactive = is_interactive
    plot.initialize(m_state)

import logging
from collections import deque
from warnings import warn
import os
import re
import io
import time

import numpy as np

from . import defaults
from . import keywords
from . import io_util
from . import state
from . import backend
from . import terminal
from . import group_proc

from .positioning import subfigure_arr
from .positioning import split
from .style import css
from .style import palette

from .style_proc import *
from .errors import LineParseError, LineProcessError

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
    if lookup_raw(m_tokens, ret_string=True).startswith('$'):
        if re.match(r'\$[_0-9a-zA-Z\*\?\.]+', lookup_raw(m_tokens, ret_string=True)) and lookup_raw(m_tokens, 1) == '=':
            varname = get_token(m_tokens)
            get_token(m_tokens)
            m_state._vmhost.set_variable(varname, process_expr(m_state, ''.join(list(m_tokens))))
        else:
            ret = process_expr(m_state, ''.join(m_tokens))
            if not (ret is None and not m_state.is_interactive):
                print(ret)
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

    elif command == 'plotr':
        parse_and_process_plot(m_state, m_tokens, keep_existed=None, side=style.FloatingPos.RIGHT)

    elif command == 'append':
        parse_and_process_plot(m_state, m_tokens, keep_existed=True)

    elif command == 'hist':
        parse_and_process_plot(m_state, m_tokens, keep_existed=None, chart_type='hist')

    elif command == 'update':
        parse_and_process_update(m_state, m_tokens)

    elif command == 'fit':
        parse_and_process_fit(m_state, m_tokens)

    elif command == 'remove':
        parse_and_process_remove(m_state, m_tokens)

    elif command == 'group':
        group_desc = get_token(m_tokens)
        assert_no_token(m_tokens)
        process_group(m_state, group_desc)

    elif command == 'set':
        parse_and_process_set(m_state, m_tokens)

    elif command == 'show':
        parse_and_process_show(m_state, m_tokens)

    elif command == 'undo':
        if m_state.is_interactive:
            m_state._history.undo(m_state)
        else:
            warn('"undo" only works in interactive mode')

    elif command == 'redo':
        if m_state.is_interactive:
            m_state._history.redo(m_state)
        else:
            warn('"redo" only works in interactive mode')

    elif command == 'line':
        x1, _, y1, x2, _, y2 = zipeval([stof, make_assert_token(','), stof, stof, make_assert_token(','), stof], m_tokens)
        process_line(m_state, (x1, y1), (x2, y2), parse_style(m_tokens))

    elif command == 'hline':
        y = stof(get_token(m_tokens))
        process_line(m_state, (None,y), (None,y), parse_style(m_tokens))

    elif command == 'vline':
        x = stof(get_token(m_tokens))
        process_line(m_state, (x,None), (x,None), parse_style(m_tokens))

    elif command == 'fill':
        parse_and_process_fill(m_state, m_tokens)
        
    elif command == 'text':
        text = get_token(m_tokens)
        if text.startswith('$('):
            text = process_expr(m_state, text)
        token1 = get_token(m_tokens)
        if lookup(m_tokens) == ',':
            get_token(m_tokens)
            process_text(m_state, text, style.str2pos(token1 + ',' + get_token(m_tokens)), parse_style(m_tokens))
        else:
            process_text(m_state, text, style.str2pos(token1), {**parse_style(m_tokens), **{'coord':'axis'}})

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

        if m_state.is_interactive and not m_state.options['remote']:
            do_focus_up = True

    # select subfigure
    elif command == 'subfigure':
        arg = get_token(m_tokens)
        
        if m_state.cur_figurename is None:
            m_state.create_figure()
            if m_state.is_interactive:
                render_cur_figure(m_state)

        m_fig = m_state.cur_figure()

        if lookup(m_tokens) == ',':
            vs = stod(arg)
            _, hs, _, subfig_idx = zipeval([make_assert_token(','), stod, make_assert_token(','), stod], m_tokens)
            if (hs, vs) != tuple(m_fig.attr('split')):
                process_split(m_state, hs, vs)
        else:
            if arg.startswith('$'):
                subfig_idx = process_expr(m_state, arg)
                if isinstance(subfig_idx, str):
                    subfig_idx = stod(arg)
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
            if lookup_raw(m_tokens, ret_string=True).startswith('$'):
                filename = str(process_expr(m_state, parse_expr(m_tokens)))
            else:
                filename = get_token(m_tokens)

        remote_save = False
        if lookup(m_tokens) == 'remote' and m_state.options['remote']:
            get_token(m_tokens)
            remote_save = True
        assert_no_token(m_tokens)

        process_save(m_state, filename, remote_save)

    elif command == 'clear':
        process_snapshot(m_state, 
            'element/datalines', 'element/bars', 'element/drawlines', 'element/polygons', 'element/texts')
        m_state.cur_subfigure().clear()

    elif command == 'replot':
        if lookup(m_tokens, 0) == 'all':
            m_state.cur_figure().is_changed = True
            if m_state.options['auto-compact']:
                m_state.cur_figure().needs_rerender = 2
        else:
            m_state.cur_subfigure().is_changed = True

    elif command == 'print':
        outstr = ''
        term = 'remote' if m_state.options['remote'] else 'stdout'
        while len(m_tokens) > 0:
            if m_tokens[0].startswith('$'):
                outstr += str(process_expr(m_state, parse_expr(m_tokens)))
            elif m_tokens[0] == '>' and len(m_tokens) > 1:
                m_tokens.popleft()
                term = m_tokens[0]
                break
            else:
                outstr += m_tokens[0]
                m_tokens.popleft()
            if len(m_tokens) > 0:
                outstr += ' '
        if term == 'stdout':
            print(outstr)
        elif term == 'stderr':
            import sys
            print(outstr, file=sys.stderr)
        elif term == 'remote' and m_state.options['remote']:
            from . import remote
            remote.place_block(code=outstr)
        else:
            warn("Terminal %s not recognized. Using stdout instead" % term)
            print(outstr)

    elif command == 'quit':
        if m_state.options['prompt-save-when-quit']:
            if len(m_state.figures) == 1:
                if terminal.query_cond('Save current figure? ', do_prompt, False):
                    process_save(m_state, m_state.cur_save_filename)

            for name, figure in m_state.figures.items():
                m_state.cur_save_filename = None
                m_state.cur_figurename = name
                if terminal.query_cond('Save figure %s? ' % name, do_prompt, False):
                    process_save(m_state, '')
                if m_state.is_interactive:
                    backend.close_figure(m_state)

        return True

    elif command == 'input':
        if m_state.is_interactive:
            warn('"input" does not work in interactive mode')
            return 0
        m_state.is_interactive = True
        if lookup(m_tokens) == 'norender':    # no render exisiting fiture
            return 0

        _cur_figurename = m_state.cur_figurename
        for fig in m_state.figures:
            m_state.cur_figurename = fig
            m_state.cur_figure().is_changed = True
            render_cur_figure(m_state)
        m_state.cur_figurename = _cur_figurename
        m_state._history.clear()

    elif command == 'display':
        if not m_state.is_interactive or m_state.options['remote']:
            process_display(m_state)
        else:
            warn('"display" does not work in interactive mode')

    elif command == 'cd':
        dest = get_token(m_tokens)
        assert_no_token(m_tokens)
        
        if io_util.dir_exist(dest):
            os.chdir(dest)
        else:
            raise LineProcessError('Directory "%s" does not exist' % dest)

    elif command == 'ls':
        files = os.listdir()
        if len(files) < 40 or terminal.query_cond('List all %d files? ' % len(files), 
            m_state.options['prompt-always'] or m_state.is_interactive, not m_state.is_interactive):
            print('\t'.join(files))

    elif command == 'pwd':
        print(os.getcwd())

    elif command == 'load' or command == 'source':
        filename = get_token(m_tokens)
        process_load(m_state, filename, [process_expr(m_state, t) if t.startswith('$') else strip_quote(t) for t in (m_tokens)], 
            preserve_mode=(command == 'source'))

    elif command == 'pause':
        interval = stof(get_token(m_tokens))
        if interval > 0:
            time.sleep(interval)
        else:
            input('Press Enter to continue...')
    elif m_state.options['direct-function-call'] and m_state._vmhost and command in m_state._vmhost.records:
        m_tokens.appendleft(command)
        return m_state._vmhost.exec_invoke(m_state, m_tokens)
    else:
        raise LineParseError('No command named "%s"' % command)

    if m_state.cur_figurename is None:
        return 0
    if not m_state.is_interactive:
        if m_state.cur_figure().is_changed:
            m_state.refresh_style(True)
        return 0

    # when figure.legend.source = subfigure, a change may lead to figure.legend change.
    if m_state.cur_figure().legend.computed_style and \
        m_state.cur_figure().legend.attr('source') == m_state.cur_subfigure().name and \
        m_state.cur_subfigure().is_changed:
        m_state.cur_subfigure().is_changed = True

    # update figure
    if m_state.cur_figure().is_changed or m_state.cur_subfigure().is_changed:
        if m_state.options['remote'] and m_state.options['auto-trigger-remote']:
            process_display(m_state)
        else:
            render_cur_figure(m_state)

    if do_focus_up:
        backend.update_focus_figure(m_state)

    return 0

def render_cur_figure(m_state:state.GlobalState):

    logger.debug('Rendering...')
    m_state.refresh_style(True)
    if m_state.cur_figure().is_changed:
        rerender_times = m_state.cur_figure().needs_rerender
        if m_state.options['auto-compact'] and rerender_times > 0:            
            if rerender_times >= 1:
                backend.update_figure(m_state, True)
            m_state.cur_figure().update_style(margin=subfigure_arr.get_compact_figure_padding(m_state.cur_figure()))
            for sf in m_state.cur_figure().subfigures:
                sf.update_style({'padding': subfigure_arr.get_compact_subfigure_padding(sf)})
            if len(m_state.cur_figure().subfigures) > 1:
                m_state.refresh_style(True)
                split.align_subfigures(m_state.cur_figure(), 'axis')
            else:
                m_state.refresh_style(False)

            # Rendering > 2 only works in multiple subfigures.
            m_state.cur_figure().needs_rerender = rerender_times - 1 \
                if rerender_times > 2 and len(m_state.cur_figure().subfigures) > 1 \
                else 0
            render_cur_figure(m_state)
        else:
            backend.update_figure(m_state, True)
            m_state.cur_figure().is_changed = False
            for m_subfig in m_state.cur_figure().subfigures:
                m_subfig.is_changed = False

    elif m_state.cur_subfigure().is_changed:
        backend.update_subfigure(m_state)
        m_state.cur_subfigure().is_changed = False 


def parse_and_process_plot(m_state:state.GlobalState, m_tokens:deque, keep_existed, side=style.FloatingPos.LEFT, chart_type='line'):
    """ Parsing and processing `plot`/`hist`/`append`/`plotr` commands.

    Args:
        keep_existed: Keep existed datalines.
        side: Side of yaxis. (LEFT/RIGHT)
        chart_type: line/hist.
    """
    if keep_existed is None:
        keep_existed = m_state.cur_subfigure().get_style('hold') if m_state.has_figure() else False
    if chart_type not in ('line', 'hist'):
        raise LineProcessError("Unrecognized chart type")

    parser = plot_proc.PlotParser() if chart_type == 'line' else plot_proc.PlotParser(plot_proc.PlotParser.M_HIST)
    parser.parse(m_state, m_tokens)
    if not parser.plot_groups:
        warn('No data to plot')
        return

    if side == style.FloatingPos.RIGHT:
        for pg in parser.plot_groups:
            pg.style.update({'side': (style.FloatingPos.RIGHT, style.FloatingPos.BOTTOM)})
    for pg in parser.plot_groups:   # expressions
        for s in pg.style:
            if isinstance(pg.style[s], str) and pg.style[s].startswith('$('):
                pg.style[s] = process_expr(m_state, pg.style[s])

    m_state.cur_subfigure(True)
    if not keep_existed:
        element_type=('element/datalines', 'element/bars', 'element/drawlines', 'element/texts', 'element/polygons')
    else:
        element_type = ('element/datalines',) if chart_type == 'line' else ('element/bars',)
    process_snapshot(m_state, 'style', *element_type, cache=False)

    dataview.plot.do_plot(m_state, parser.plot_groups, keep_existed=keep_existed, 
        labelfmt=r'%F:%T' if m_state.options['full-label'] else None, chart_type=chart_type)
    m_state.cur_subfigure().set_automatic_labels()
    if side == style.FloatingPos.RIGHT:
        m_state.cur_subfigure().axes[2].update_style({'enabled':True})
        m_state.cur_subfigure().axes[2].tick.update_style({'visible':True})
        m_state.cur_subfigure().axes[2].label.update_style({'visible':True})


def parse_and_process_update(m_state:state.GlobalState, m_tokens:deque):
    selection = parse_style_selector(m_tokens)
    elements = css.StyleSheet(selection).select(m_state.cur_subfigure())
    if not elements:
        warn('No elements selected')
        return
    m_state.cur_figure()    # update needs an existing figure.

    if all((e.typename == 'line' for e in elements)):
        chart_type = 'line'
        element_type = 'element/datalines'
    elif all((e.typename == 'bar' for e in elements)):
        chart_type = 'bar'
        element_type = 'element/bars'
    else:
        raise LineProcessError("Multiple element types detected. Please only include lines or histograms")

    parser = plot_proc.PlotParser() if chart_type == 'line' else plot_proc.PlotParser(plot_proc.PlotParser.M_HIST)
    parser.parse(m_state, m_tokens)
    if not parser.plot_groups:
        warn('No data to plot')
        return
    process_snapshot(m_state, 'style', element_type, cache=False)
    dataview.plot.do_update(m_state, elements, parser.plot_groups)


def parse_and_process_fit(m_state:state.GlobalState, m_tokens:deque):
    selection = parse_style_selector(m_tokens)
    elements = css.StyleSheet(selection).select(m_state.cur_subfigure())
    if lookup(m_tokens) in ('linear', 'quad', 'exp', 'prop'):
        function = get_token(m_tokens)
    else:
        function = 'linear'
    style_dict = parse_style(m_tokens)

    if not elements:
        warn('No line is fitted')
        return
    process_snapshot(m_state, 'element/datalines')
    fitnames = []
    for e in elements:
        l = dataview.api.fit(m_state, e, function=function, labelfmt=style_dict.pop('label', 'Fit %T'), **style_dict)
        fitnames.append(l.data.myfunc.name)
    m_state._vmhost.set_variable('fit', fitnames)


def parse_and_process_remove(m_state:state.GlobalState, m_tokens:deque):
    """ Parse and process `remove` command.
    """
    m_subfig = m_state.cur_subfigure()

    # special with figure
    figures_to_remove = []
    selection = []
    for s in parse_style_selector(m_tokens):
        if isinstance(s, css.NameSelector):
            if s.name == 'gcf':
                figures_to_remove.append('figure:' + m_state.cur_figurename)
                continue
            elif s.name.startswith('figure'):
                figures_to_remove.append('figure:' + [f for f in m_state.figures if f == s.name[6:]][0])
                continue
        selection.append(s)

    ss = css.StyleSheet(selection)
    elements = ss.select(m_state.cur_subfigure())

    if not elements and not figures_to_remove:
        warn('No element is selected')
        return

    if len(elements) + len(figures_to_remove) > 1:
        if terminal.query_cond('Remove elements %s %s? ' % (
            ' '.join(e.name for e in elements), ' '.join(f for f in figures_to_remove)), 
            m_state.options['prompt-multi-removal'] and (m_state.options['prompt-always'] or 
            m_state.is_interactive), True):
            pass
        else:
            return

    if figures_to_remove:
        m_state._history.clear()
    else:
        process_snapshot(m_state, 
            'element/datalines', 'element/bars', 'element/drawlines', 'element/polygons', 'element/texts')

    logger.debug('Remove elements: %s', elements)
    logger.debug('Remove figures: %s', figures_to_remove)

    cur_figurename = m_state.cur_figurename
    for f in figures_to_remove:
        m_state.cur_figurename = f[7:]
        backend.close_figure(m_state)
        m_state.remove_figure(m_state.cur_figurename)

    if 'figure:' + cur_figurename in figures_to_remove:
        if not m_state.figures:
            m_state.cur_figurename = None
        return
    else:
        m_state.cur_figurename = cur_figurename

    for e in elements:
        m_state.cur_subfigure().remove_element(e)


def process_group(m_state:state.GlobalState, group_desc):
    process_snapshot(m_state, 'style')
    m_state.cur_subfigure().update_style({'group': group_proc.parse_group(group_desc) if group_desc != 'clear' else None})
    logger.debug('Group is: %s' % str(m_state.cur_subfigure().get_style('group')))
    m_state.refresh_style() # need to refresh twice -- for colorid and for actual color
    m_state.cur_subfigure().is_changed = True


def parse_and_process_set(m_state:state.GlobalState, m_tokens:deque):
    """ Parse and process `set` command.
    """
    if test_token_inc(m_tokens, 'option'):
        while len(m_tokens) > 0:
            opt = get_token(m_tokens)
            arg = get_token(m_tokens)
            # TODO readonly options
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

    elif test_token_inc(m_tokens, 'default'):
        selection = parse_style_selector(m_tokens)
        style_list = parse_style(m_tokens)
        m_state.update_default_stylesheet(css.StyleSheet(selection, style_list))

    elif test_token_inc(m_tokens, ('future', 'style')):
        selection, style_list, add_class, remove_class = parse_selection_and_style_with_default(
            m_tokens, css.NameSelector('gca')
        )
        process_snapshot(m_state, 'state')
        m_state.update_local_stylesheet(css.StyleSheet(selection, style_list))

    elif test_token_inc(m_tokens, 'compact'):
        render_cur_figure(m_state)
        m_state.cur_figure().update_style(margin=subfigure_arr.get_compact_figure_padding(m_state.cur_figure()))
        for sf in m_state.cur_figure().subfigures:
            sf.update_style({'padding': subfigure_arr.get_compact_subfigure_padding(sf)})

    elif test_token_inc(m_tokens, ('palette', 'palettes')):
        target = get_token(m_tokens) if len(m_tokens) >= 2 else 'line'
        target_style = 'color'
        if target == 'point':
            target = 'line'
            target_style = 'fillcolor'
        palette_name = get_token(m_tokens)
        assert_no_token(m_tokens)
        try:
            m_palette = palette.get_palette(palette_name)
        except KeyError:
            raise LineProcessError('Palette "%s" does not exist' % palette_name)
        else:
            process_snapshot(m_state, 'style')
            palette.palette2stylesheet(m_palette, target, target_style).apply_to(m_state.cur_subfigure())
            m_state.cur_subfigure().is_changed = True
    else:
        selection, style_list, add_class, remove_class = parse_selection_and_style_with_default(
            m_tokens, css.NameSelector('gca'), recog_expression=True
        )
        # handle expressions appeared in style values
        for s in style_list:
            if isinstance(style_list[s], str) and style_list[s].startswith('$('):
                style_list[s] = process_expr(m_state, style_list[s])

        snapshot_cc = process_snapshot(m_state, 'style', cache=True)
        if m_state.apply_styles(
            css.StyleSheet(selection, style_list), add_class, remove_class):
            m_state.cur_figure().is_changed = True
            snapshot_cc(True)
        else:
            warn('No style is set')
            snapshot_cc(False)


def parse_and_process_show(m_state:state.GlobalState, m_tokens:deque):
    """ Parse and process `show` command.
    """

    if test_token_inc(m_tokens, 'currentfile'):
        print('File saved:', m_state.cur_save_filename)

    elif test_token_inc(m_tokens, ('option',  'options')):
        if len(m_tokens) == 0:
            # TODO help message
            print('OPTION                          VALUE')
            print('------                          -----')
            for opt, val in m_state.options.items():
                print('%s%s%s' % (opt, ' '*(32-len(opt)), val))
        else:
            print(m_state.options[get_token(m_tokens)])
            assert_no_token(m_tokens)

    elif test_token_inc(m_tokens, ('palette', 'palettes')):
        palette_names = sorted(palette.PALETTES)
        for i in range(8):
            print(' '.join(('%-15s' % palette_names[n] for n in range(8*i, min(8*i+8, len(palette_names))))))

    else:
        if not m_state.is_interactive:
            m_state.refresh_style(True)

        if keywords.is_style_keyword(lookup(m_tokens)) and lookup(m_tokens, 1) != ',' and len(m_tokens) < 2:
            selection = css.NameSelector('gca')
        else:
            selection = parse_style_selector(m_tokens)
        ss = css.StyleSheet(selection, None)
        elements = ss.select(m_state.cur_figure())
        
        if len(elements) == 0:
            warn('No element to show')
            return

        if len(m_tokens) == 0:
            for e in elements:
                print(e.name + ':')
                print('\n'.join(('%s =\t%s' % item for item in e.computed_style.items())))
        else:
            for style_name in m_tokens:
                style_name = keywords.style_alias.get(style_name, style_name)
                if style_name not in keywords.style_keywords:
                    warn('Skip invalid style "%s"' % style_name)
                    continue
                print('%s:' % style_name)
                output = []
                for e in elements:
                    try:
                        output.append('%s\t%s' % (e.name, e.computed_style[style_name]))
                    except KeyError:
                        output.append('%s\t%s' % (e.name, e.get_style(style_name, '<None>')))
                print('\n'.join(output))


def parse_and_process_fill(m_state:state.GlobalState, m_tokens:deque):
    fill_between = []
    find_dataline = lambda x: [d for d in m_state.cur_subfigure().datalines if d.name == x][0]

    while len(m_tokens) > 0:
        if keywords.is_style_keyword(lookup(m_tokens)):
            break
        token = get_token(m_tokens)
        try:
            if '-' in token:
                line1str, line2str = token.split('-', 1)
                line1 = find_dataline(line1str)
                line2 = find_dataline(line2str) if line2str.startswith('line') else float(line2str)
            else:
                line1, line2 = find_dataline(token), None
        except IndexError:
            warn('Skip line "%s" as it does not exist' % token)
        else:
            fill_between.append((line1, line2))

    style_dict = parse_style(m_tokens)
    if not fill_between:
        warn('No line to fill')
        return
    
    process_snapshot(m_state, 'element/polygons')
    for line1, line2 in fill_between:
        dataview.api.fill_h(m_state, line1, line2, **style_dict)


def process_text(m_state:state.GlobalState, text:str, pos, style_dict:dict):
    process_snapshot(m_state, 'element/texts')
    return m_state.cur_subfigure().add_text(text=text, pos=pos, **style_dict)

def process_line(m_state:state.GlobalState, pos1, pos2, style_dict:dict):
    process_snapshot(m_state, 'element/drawlines')
    return m_state.cur_subfigure().add_drawline(startpos=pos1, endpos=pos2, **style_dict)

def process_split(m_state:state.GlobalState, hsplitnum:int, vsplitnum:int):
    m_state._history.clear()
    split.split_figure(m_state.cur_figure(), hsplitnum, vsplitnum, m_state.options['resize-when-split'])
    m_state.refresh_style(True)
    split.align_subfigures(m_state.cur_figure(), 'axis')


def process_save(m_state:state.GlobalState, filename:str, remote_save=False):
    """ Saving current figure.
    """
    do_prompt = (m_state.is_interactive or m_state.options['prompt-always']) and not remote_save

    if not filename:
        if m_state.cur_save_filename:
            filename = terminal.query_cond('Enter filename here (default: %s): ' % m_state.cur_save_filename,
            do_prompt, m_state.cur_save_filename, False)
        else:
            filename = terminal.query_cond('Enter filename here: ', do_prompt, None, False)
        if not filename:
            logger.info('Saving cancelled')
            return

    if not remote_save and m_state.options['prompt-overwrite'] and io_util.file_exist(filename):
        if not terminal.query_cond('Overwrite current file "%s"? ' % filename, do_prompt, False):
            warn('Canceled')
            return

    render_cur_figure(m_state)
    if remote_save:
        # TODO suffix has many corner cases -- either use mpl's implementation or check them
        process_save_remote(m_state, filename[-3:] if filename[-4] == '.' else 'png', filename)
    else:
        backend.save_figure(m_state, filename)
    m_state.cur_save_filename = filename

def process_display(m_state:state.GlobalState):

    backend.finalize(m_state)
    backend.initialize(m_state, silent=m_state.options['remote'])   # not remote --> must be displayable
    if m_state.cur_figurename:
        cf = m_state.cur_figurename
        for f in m_state.figures:
            m_state.cur_figurename = f
            render_cur_figure(m_state)
        m_state.cur_figurename = cf
        if not m_state.options['remote']:
            backend.show(m_state)
        else:
            # TODO display every figure?
            process_save_remote(m_state)
                

def process_save_remote(m_state:state.GlobalState, fmt='svg', filename='image', wait_client=True):
    """ Save current figure to remote. Will wait client to connect if wait_client is set.
    """
    from . import remote
    from html import escape

    if fmt == 'svg':
        f = io.StringIO()
    else:
        f = io.BytesIO()
    backend.save_figure(m_state, f, format=fmt)
    f.seek(0)
    img_id = remote.place_image_data(f.read(), filename=filename if filename.endswith(fmt) else '%s.%s' % (filename, fmt))

    display_cmd = 'display' if fmt == 'svg' else 'save'
    display_info = '%s @ [%s:%d]' % (display_cmd, escape(m_state._vmhost.pc[0].filename), m_state._vmhost.pc[0].lineid) if m_state._vmhost else display_cmd
    remote.place_block(display_info, img_id=img_id, is_svg=fmt=='svg', img_name=filename)
    if wait_client:
        if not m_state.is_interactive:  # assuming we would stay a while in interactive; I'm not sure why this works.
            time.sleep(0.5)
        remote.wait_client()

def process_expr(m_state:state.GlobalState, expr:str):
    evaler = expr_proc.ExprEvaler(m_state._vmhost.variables, m_state.file_caches)
    if expr.startswith('$!('):
        logger.debug(expr)
        return evaler.evaluate_system(expr[2:])
    else:
        evaler.load(expr, True)
        logger.debug(evaler.expr)
        return evaler.evaluate()

def process_snapshot(m_state:state.GlobalState, *snapshot_type, cache=False):
    if m_state.is_interactive:
        if snapshot_type != 'state':
            m_state.cur_figure()
        if cache:
            return m_state._history.cache_snapshot(m_state, snapshot_type)
        else:
            return m_state._history.take_snapshot(m_state, snapshot_type)
    else:
        return lambda x: None if cache else None


def process_load(m_state:state.GlobalState, filename:str, args:list, preserve_mode=False):
    # preserve_mode => do not change to file mode

    handler = terminal.CMDHandler(m_state)
    preserve_mode = preserve_mode and hasattr(handler, 'proc_source')   # has not implemented in legacy shell
    if not preserve_mode:
        is_interactive = m_state.is_interactive # proc_file() requires state to be non-interactive
        
    cwd = os.getcwd()

    loadpaths = [os.getcwd(), os.path.expanduser('~/.line/')]

    full_filename = None
    for path in loadpaths:
        if io_util.file_exist(os.path.join(path, filename)):
            full_filename = os.path.join(path, filename)
            break
    
    if not full_filename:
        raise LineProcessError('File "%s" does not exist' % filename)

    m_state._vmhost.push_args([filename] + args)
    m_state._history.clear()
    if not preserve_mode:
        backend.finalize(m_state)
        m_state.is_interactive = False
        handler.proc_file(full_filename)
    else:
        handler.proc_source(full_filename)
    m_state._vmhost.pop_args()
    os.chdir(cwd)
    if not preserve_mode:
        m_state.is_interactive = is_interactive
        backend.initialize(m_state, silent=m_state.options['remote'] or not is_interactive)
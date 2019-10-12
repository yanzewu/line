
import sys
import itertools
import logging
from collections import deque
import os

import numpy as np

from . import state
from . import plot
from . import sheet_util
from . import io_util
from . import keywords
from . import defaults
from . import scale
from . import cmd_handle

from . import style_man
from . import palette

from .parse import *
from .errors import LineParseError, LineProcessError, warn
from .collection_util import extract_single

logger = logging.getLogger('line')


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
    command = get_token(m_tokens)
    command = keywords.command_alias.get(command, command)   # expand short commands

    do_prompt = m_state.is_interactive or m_state.options['prompt-always']   # prompt
    do_focus_up = False # update focus

    # Long commands

    if command == 'plot':
        parse_and_process_plot(m_state, m_tokens, keep_existed=False)

    elif command == 'append':
        parse_and_process_plot(m_state, m_tokens, keep_existed=True)

    elif command == 'remove':
        parse_and_process_remove(m_state, m_tokens)

    elif command == 'group':
        group_descriptor = get_token(m_tokens)
        assert_no_token(m_tokens)
        if group_descriptor == 'clear':
            m_state.cur_subfigure().update_style({'group':None})
        else:
            m_state.cur_subfigure().update_style({'group': parse_group(group_descriptor)})
            logger.debug('Group is: %s' % str(m_state.cur_subfigure().get_style('group')))

        m_state.cur_subfigure().update_colorid()
        m_state.cur_subfigure().is_changed = True

    elif command == 'set':
        parse_and_process_set(m_state, m_tokens)

    elif command == 'show':
        parse_and_process_show(m_state, m_tokens)

    elif command == 'style':
        parse_and_process_style(m_state, m_tokens)

    elif command == 'line':
        x1 = stof(get_token(m_tokens))
        assert_token(get_token(m_tokens), ',')
        y1 = stof(get_token(m_tokens))
        x2 = stof(get_token(m_tokens))
        assert_token(get_token(m_tokens), ',')
        y2 = stof(get_token(m_tokens))
        
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

    elif command == 'text':
        text = get_token(m_tokens)
        token1 = get_token(m_tokens)
        if lookup(m_tokens) == ',':
            get_token(m_tokens)
            pos = (stof(token1), stof(get_token(m_tokens)))
            m_state.cur_subfigure().add_text(text, pos, parse_style(m_tokens))
        else:
            pos = style.Str2Pos[token1]
            style_list = parse_style(m_tokens)
            style_list['coord'] = 'axis'
            m_state.cur_subfigure().add_text(text, pos, style_list)

        m_state.cur_subfigure().is_changed = True

    elif command == 'split':
        hsplitnum = stod(get_token(m_tokens))
        assert_token(get_token(m_tokens), ',')
        vsplitnum = stod(get_token(m_tokens))
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
            i = 1
            while str(i) in m_state.figures:
                i += 1
            fig_name = str(i)
        else:
            fig_name = get_token(m_tokens)
            assert_no_token(m_tokens)

        m_state.cur_figurename = fig_name
        if fig_name not in m_state.figures:
            m_state.create_figure()
            m_state.cur_figure().is_changed = True

        if m_state.is_interactive:
            do_focus_up = True

    # select subfigure
    elif command == 'subfigure':
        subfig_idx = stod(get_token(m_tokens))
        assert_no_token(m_tokens)

        m_fig = m_state.cur_figure()

        if subfig_idx < len(m_fig.subfigures):
            m_fig.cur_subfigure = subfig_idx
        else:
            raise LineProcessError('subfigure %d does not exist' % subfig_idx)

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
        assert_no_token(m_tokens)
        m_state.cur_subfigure().clear()

    elif command == 'replot':
        arg1 = None
        if len(m_tokens) >= 1:
            assert_token(get_token(m_tokens), 'all')
            arg1 = 'all'

        assert_no_token(m_tokens)
        if arg1:
            m_state.cur_figure().is_changed = True
        else:
            m_state.cur_subfigure().is_changed = True

    elif command == 'print':
        print(' '.join(m_tokens))

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

    else:
        raise LineParseError('No command named "%s"' % command)

    if m_state.cur_figurename is None:
        return 0
    if not m_state.is_interactive:
        if m_state.cur_figure().is_changed:
            m_state.refresh_style(True)
        return 0

    # update figure
    if m_state.cur_figure().is_changed:
        m_state.refresh_style(True)
        plot.update_figure(m_state, True)
        m_state.cur_figure().is_changed = False
        for m_subfig in m_state.cur_figure().subfigures:
            m_subfig.is_changed = False

    elif m_state.cur_subfigure().is_changed:
        m_state.refresh_style()
        plot.update_subfigure(m_state)
        m_state.cur_subfigure().is_changed = False

    if do_focus_up:
        plot.update_focus_figure(m_state)

    return 0

def parse_and_process_plot(m_state:state.GlobalState, m_tokens:deque, keep_existed):
    """ Parsing and processing `plot` and `append` commands.

    Args:
        keep_existed: Keep existed datalines.
    """
    # LL(2)

    file_loaded = {}
    
    data_list = []
    style_list = []

    # Recording x data and label
    cur_xdata = None
    cur_xlabel = None

    while len(m_tokens) > 0:

        # when it could be filename:
        # force-column-selection is not set
        # no : at next
        # not starting with $ or (

        is_newfile = False  # is new filename 

        if m_state.options['force-column-selection'] == False and \
            (len(m_tokens) == 1 or m_tokens[1] != ':') or \
            (m_tokens[0] != '' and m_tokens[0][0] not in '$('):

            if io_util.file_exist(m_tokens[0]):
                filename = get_token(m_tokens)
                is_newfile = True
                logger.debug('New file found: %s' % filename)
            elif m_tokens[0][0] not in '$(' and not m_tokens[0].isdigit():    # maybe a column title?
                m_file_test = file_loaded.get(m_state.cur_open_filename, None)
                if not m_file_test or not m_file_test.has_label(m_tokens[0]):

                    # wildcard?
                    if '*' in m_tokens[0] or '?' in m_tokens[0]:
                        import fnmatch
                        files = fnmatch.filter([f for f in os.listdir() if os.path.isfile(f)], m_tokens[0])
                        if files:
                            print('Matched files:', ' '.join(files))
                            get_token(m_tokens)
                            filename = files[0]
                            is_newfile = True
                            for f in files[1:]:
                                m_tokens.appendleft(',')
                                m_tokens.appendleft(f)
                        else:
                            warn('No matching files by "%s"' % m_tokens[0])
                            skip_tokens(m_tokens, ',')
                            continue
                        
                    else:
                        warn('File "%s" not found' % m_tokens[0])
                        skip_tokens(m_tokens, ',')
                        continue
                
        if not is_newfile:
            filename = m_state.cur_open_filename
            warn('Treat "%s" as column label' % m_tokens[0])

        if not filename:
            raise LineParseError('Filename expected')
        elif filename in file_loaded:
            logger.debug('Exist file found: %s' % filename)
            m_file = file_loaded[filename]
        else: 
            m_file = sheet_util.load_file(filename,
                m_state.options['data-title'],
                m_state.options['data-delimiter'],
                m_state.options['ignore-data-comment']
            )
            if not m_file:
                warn('Skip invalid file "%s"' % filename)
                skip_tokens(m_tokens, ',')
                continue
            else:
                logger.debug('New file loaded: %s' % m_file)
                m_state.cur_open_filename = filename
                file_loaded[filename] = m_file

        # no column expr 
        if not m_state.options['force-column-selection'] and (
            len(m_tokens) == 0 or lookup(m_tokens, 0) == ',' or lookup(m_tokens, 1) == '=' or 
            keywords.is_style_keyword(m_tokens[0])):
            # you need to specify column name like $t if it coincides with style name

            if m_file.cols() == 0:
                raise RuntimeError('File has no valid column')
            elif m_file.cols() == 1:
                data_list.append((m_file.get_sequence(), m_file.get_column(0),
                    m_file.get_label(0), '', m_file.filename))
            elif m_file.cols() == 2:
                data_list.append((m_file.get_column(0), m_file.get_column(1), 
                    m_file.get_label(1), m_file.get_label(0), m_file.filename))
            else:
                if m_file.cols() > 10:
                    warn('Load all %d columns to plot' % m_file.cols())
                for j in range(1, m_file.cols()):
                    data_list.append((m_file.get_column(0), m_file.get_column(j),
                        m_file.get_label(j), m_file.get_label(0), m_file.filename))
            logger.debug('All column in file loaded: Total %d datasets' % m_file.cols())
        
        else:
            column_expr = parse_column(m_tokens)
            column = m_file.eval_column_expr(column_expr)
            label = m_file.get_label(int(column_expr)-1) if column_expr.isdigit() else column_expr
            if column is None:  # failed
                warn('Skip column "%s" with no valid data' % column_expr)
                skip_tokens(m_tokens, ',')
                continue

            if lookup(m_tokens) == ':':
                # when a x data appears, the following y data is based on this x.
                cur_xdata = column
                cur_xlabel = label

                logger.debug('Try parsing y data')
                get_token(m_tokens)
                column_expr2 = parse_column(m_tokens)
                column2 = m_file.eval_column_expr(column_expr2)
                label2 = m_file.get_label(int(column_expr2)-1) if column_expr2.isdigit() else column_expr2
                if column2 is not None:
                    data_list.append((column, column2, label2, label, m_file.filename))
                else:
                    skip_tokens(m_tokens, ',')
                    warn('Skip column "%s" with no valid data' % column_expr2)
                    continue
            else:
                if cur_xdata is None:
                    cur_xdata = m_file.get_sequence()
                    cur_xlabel = ''
                data_list.append((cur_xdata, column, label, cur_xlabel, m_file.filename))

        # style parameters
        styles = parse_style(m_tokens, ',', recog_comma=False)
        while len(style_list) < len(data_list): # this is for a file containing multiple columns
            style_list.append(styles)

        if lookup(m_tokens) == ',':
            get_token(m_tokens)
            continue

    assert_no_token(m_tokens)

    if len(data_list) == 0:
        warn('No data to plot')
        return

    # Broadcasting styles
    for bc_style in m_state.options['broadcast-style']:
        if bc_style in style_list[0]:
            for i in range(1, len(style_list)):
                style_list[i].setdefault(bc_style, style_list[0][bc_style])



    logger.debug('Processing plot')
    if len(data_list) > 0:
        
        # first time: create figure
        if m_state.cur_figurename is None:
            m_state.create_figure()
            m_state.refresh_style()

        # handle append
        if not keep_existed:
            m_state.cur_subfigure().datalines.clear()

        # add filename to data label?
        filename_prefix = len(set((d[4] for d in data_list))) != 1

        for (x, y, label, xlabel, filename), style in zip(data_list, style_list):
            ylabel = filename + ':' + str(label) if filename_prefix else str(label)
            m_state.cur_subfigure().add_dataline((x, y), ylabel, xlabel, style)
        
        # Set labels
        xlabels = set((d.get_style('xlabel') for d in m_state.cur_subfigure().datalines))
        ylabels = set((d.get_style('label') for d in m_state.cur_subfigure().datalines))
        if len(xlabels) == 1:
            m_state.cur_subfigure().axes[0].label.update_style({'text': xlabels.pop()})
        if len(ylabels) == 1:
            m_state.cur_subfigure().axes[1].label.update_style({'text': ylabels.pop()})

        # Set range
        if m_state.options['auto-adjust-range'] or (
            m_state.cur_subfigure().axes[0].get_style('range')[0] is None or
            m_state.cur_subfigure().axes[0].get_style('range')[1] is None or
            m_state.cur_subfigure().axes[1].get_style('range')[0] is None or
            m_state.cur_subfigure().axes[1].get_style('range')[1] is None
        ):
            logger.debug('Setting automatic range')
            process_autorange(m_state)

        m_state.cur_subfigure().is_changed = True
    else:
        pass


def parse_and_process_remove(m_state:state.GlobalState, m_tokens:deque):
    """ Parse and process `remove` command.
    """

    dataline_sel = set()
    drawline_sel = set()
    text_sel = set()

    m_subfig = m_state.cur_subfigure()

    selection = parse_style_selector(m_tokens)
    ss = style_man.StyleSheet(selection)
    elements = ss.select(m_state.cur_subfigure())

    if not elements:
        warn('No element is selected')
        return

    for element in elements:
        if isinstance(element, state.DataLine):
            dataline_sel.add(int(element.name[4:]))
        elif isinstance(element, state.DrawLine):
            drawline_sel.add(int(element.name[8:]))
        elif isinstance(element, state.Text):
            text_sel.add(int(element.name[4:]))

    if len(dataline_sel) > 1:
        if io_util.query_cond('Remove data %s?' % (' '.join((str(d) for d in dataline_sel))), 
            m_state.options['prompt-multi-removal'] and (m_state.options['prompt-always'] or 
            m_state.is_interactive), True):
            for idx in sorted(dataline_sel, reverse=True):
                m_subfig.datalines.pop(idx)
            logger.debug('Removed dataline: %s' % dataline_sel)
    elif len(dataline_sel) == 1:
        m_subfig.datalines.pop(dataline_sel.pop())

    for idx in sorted(drawline_sel, reverse=True):
        m_subfig.drawlines.pop(idx)
    logger.debug('Removed drawline: %s' % drawline_sel)
    
    for idx in sorted(text_sel, reverse=True):
        m_subfig.texts.pop(idx)
    logger.debug('Removed text: %s' % text_sel)

    # rename
    for i, l in enumerate(m_subfig.datalines):
        l.name = 'line%d' % i
    for i, l in enumerate(m_subfig.drawlines):
        l.name = 'drawline%d' % i        
    for i, l in enumerate(m_subfig.texts):
        l.name = 'text%d' % i

    m_state.cur_subfigure().is_changed = True


def parse_and_process_set(m_state:state.GlobalState, m_tokens:deque):
    """ Parse and process `set` command.
    """
    # LL(2)
    
    if m_tokens[0] == 'option':
        get_token(m_tokens)

        while len(m_tokens) > 0:
            opt = get_token(m_tokens)
            arg = get_token(m_tokens)
            if arg == '=':
                arg = get_token(m_tokens)
            if opt not in m_state.options:
                warn('Skip invalid option "%s"' % opt)
            else:
                if opt not in m_state.options:
                    raise LineParseError('Invalid option: "%s"' % opt)
                m_state.options[opt] = translate_option_val(opt, arg)

    # TODO auto generate ss when set palette (either here or in subfigure)

    elif m_tokens[0] == 'default':
        get_token(m_tokens)

        has_updated = False
        if keywords.is_style_keyword(m_tokens[0]) and not keywords.is_style_keyword(m_tokens[1]):
            style_list = parse_style(m_tokens)
            selection = style_man.NameSelector('subfigure')
            # TODO automatically select candidate
        else:
            selection = parse_style_selector(m_tokens)
            for s in selection:
                if not isinstance(s, style_man.TypeSelector):
                    raise LineParseError('Only element names (e.g. figure, subfigure) are allowed')
            style_list = parse_style(m_tokens)

        ss = style_man.StyleSheet(selection, style_list)
        has_updated = m_state.default_stylesheet.update(ss)

        if not has_updated:
            warn('No style is set')

    elif m_tokens[0] == 'palette':
        get_token(m_tokens)
        palette_name = get_token(m_tokens)
        assert_no_token(m_tokens)
        try:
            m_palette = palette.get_palette(palette_name)
        except KeyError:
            raise LineProcessError('Palette "%s" does not exist' % palette_name)
        palette.palette2stylesheet(m_palette).apply_to(m_state.cur_subfigure())
        m_state.cur_subfigure().is_changed = True

    else:
        has_updated = False

        # Setting cur_subfigure, recursively
        if keywords.is_style_keyword(m_tokens[0]) and (
            not keywords.is_style_keyword(m_tokens[1]) or 
            (m_tokens[1] not in ('on', 'off') and len(m_tokens) <= 2)):
            # the nasty cases... either not a style keyword or not enough style parameters
            # that treated as value

            selection = style_man.NameSelector('gca')
            style_list, add_class, remove_class = parse_style(m_tokens, recog_class=True)
        else:
            selection = parse_style_selector(m_tokens)
            if lookup(m_tokens) == 'clear':
                get_token(m_tokens)
                assert_no_token(m_tokens)
                style_list = style_man.ResetStyle()
                add_class = []
                remove_class = []
            else:
                style_list, add_class, remove_class = parse_style(m_tokens, recog_class=True)
            
        ss = style_man.StyleSheet(selection, style_list)
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
        print('File opened:', m_state.cur_open_filename)
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

    elif element_name == 'palettes':
        palette_names = list(palette.PALETTES)
        palette_names.sort()
        for i in range(8):
            print(' '.join(('%-15s' % palette_names[n] for n in range(8*i, min(8*i+8, len(palette_names))))))

    else:
        if not m_state.is_interactive:
            m_state.refresh_style(True)

        selection = parse_style_selector(m_tokens)
        ss = style_man.StyleSheet(selection, None)
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

    ss = style_man.StyleSheet(style_man.ClassSelector(classname), style_list)
    m_state.class_stylesheet.update(ss)


def process_autorange(m_state:state.GlobalState):
    max_x = max([np.max(d.x) for d in m_state.cur_subfigure().datalines])
    min_x = min([np.min(d.x) for d in m_state.cur_subfigure().datalines])
    max_y = max([np.max(d.y) for d in m_state.cur_subfigure().datalines])
    min_y = min([np.min(d.y) for d in m_state.cur_subfigure().datalines])

    x_ticks = scale.get_ticks(min_x, max_x)
    y_ticks = scale.get_ticks(min_y, max_y)

    m_state.cur_subfigure().axes[0].update_style({'range': (x_ticks[0], x_ticks[-1], x_ticks[1]-x_ticks[0])})
    m_state.cur_subfigure().axes[1].update_style({'range': (y_ticks[0], y_ticks[-1], y_ticks[1]-y_ticks[0])})
    logger.debug('xrange set: %g:%g' % (x_ticks[0], x_ticks[-1]))
    logger.debug('yrange set: %g:%g' % (y_ticks[0], y_ticks[-1]))


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
                j / hsplitnum + hspacing / 2,
                (vsplitnum - 1 - i) / vsplitnum + vspacing / 2
                ), 
                'rsize': (
                1 / hsplitnum -  hspacing,
                1 / vsplitnum - vspacing
            )})
    
    m_fig.subfigures = list(itertools.chain.from_iterable(subfig_state_2d))
    m_fig.is_changed = True
    m_fig.update_style({'split': [hsplitnum, vsplitnum]})


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

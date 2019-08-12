
import sys
import itertools
import logging
from collections import deque

import numpy as np

from . import state
from . import plot
from . import sheet_util
from . import io_util
from . import keywords
from . import defaults
from . import scale

from .parse import *
from .errors import LineParseError, LineProcessError, warn

logger = logging.getLogger('line')

# TODO LOW prompt only in interactive mode

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
        return

    logger.debug('Tokens are: %s' % tokens)

    m_tokens = deque(tokens)
    command = get_token(m_tokens)
    command = keywords.command_alias.get(command, command)   # expand short commands

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
        m_state.cur_subfigure().set_style('group', parse_group(group_descriptor))
        logger.debug('Group is: %s' % str(m_state.cur_subfigure().attr['group']))

        m_state.cur_subfigure().update_template_palatte()
        plot.update_subfigure(m_state)

    elif command == 'set':
        parse_and_process_set(m_state, m_tokens)

    elif command == 'show':
        parse_and_process_show(m_state, m_tokens)

    elif command == 'line':
        x1 = stof(get_token(m_tokens))
        assert_token(get_token(m_tokens), ',')
        y1 = stof(get_token(m_tokens))
        x2 = stof(get_token(m_tokens))
        assert_token(get_token(m_tokens), ',')
        y2 = stof(get_token(m_tokens))
        
        m_state.cur_subfigure().add_drawline((x1,y1), (x2,y2), parse_style(m_tokens))
        plot.update_subfigure(m_state)

    elif command == 'hline':
        y = stof(get_token(m_tokens))
        m_state.cur_subfigure().add_drawline((None,y), (None,y), parse_style(m_tokens))
        plot.update_subfigure(m_state)

    elif command == 'vline':
        x = stof(get_token(m_tokens))
        m_state.cur_subfigure().add_drawline((x,None), (x,None), parse_style(m_tokens))
        plot.update_subfigure(m_state)

    elif command == 'text':
        text = get_token(m_tokens)
        token1 = get_token(m_tokens)
        if len(m_tokens) > 0 and m_tokens[0] == ',':
            get_token(m_tokens)
            pos = (stof(token1), stof(get_token(m_tokens)))
            m_state.cur_subfigure().add_text(text, pos, parse_style(m_tokens))
        else:
            pos = style.Str2Pos[token1]
            style_list = parse_style(m_tokens)
            style_list['coord'] = 'axis'
            m_state.cur_subfigure().add_text(text, pos, style_list)

        plot.update_subfigure(m_state)

    elif command == 'split':
        hsplitnum = stod(get_token(m_tokens))
        assert_token(get_token(m_tokens), ',')
        vsplitnum = stod(get_token(m_tokens))
        assert_no_token(m_tokens)
        process_split(m_state, hsplitnum, vsplitnum)

    elif command == 'hsplit':
        splitnum = stod(get_token(m_tokens))
        assert_no_token(m_tokens)
        process_split(m_state, splitnum, m_state.cur_figure().attr['split'][1])

    elif command == 'vsplit':
        splitnum = stod(get_token(m_tokens))
        assert_no_token(m_tokens)
        process_split(m_state, m_state.cur_figure().attr['split'][0], splitnum)

    # select or create figure
    elif command == 'figure':
        fig_name = get_token(m_tokens)
        assert_no_token(m_tokens)

        m_state.cur_figurename = fig_name
        if fig_name not in m_state.figures:
            m_state.create_figure()
            plot.update_figure(m_state)

        plot.update_focus_figure(m_state)

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
            print('Using current filename: %s' % m_state.cur_save_filename)
            filename = m_state.cur_save_filename
        else:
            filename = get_token(m_tokens)
        assert_no_token(m_tokens)

        process_save(m_state, filename)

    elif command == 'clear':
        assert_no_token(m_tokens)
        plot.cla(m_state)
        m_state.cur_subfigure().clear()

    elif command == 'cls':
        assert_no_token(m_tokens)
        plot.cls(m_state)
        m_state.cur_subfigure().clear()

    elif command == 'replot':
        arg1 = None
        if len(m_tokens) >= 1:
            assert_token(get_token(m_tokens), 'all')
            arg1 = 'all'

        assert_no_token(m_tokens)
        if arg1:
            plot.update_figure(m_state)
        else:
            plot.update_subfigure(m_state)

    elif command == 'print':
        print(' '.join(m_tokens))

    elif command == 'quit':
        if m_state.options['auto-save']:
            if len(m_state.figures) == 1:
                if input('Save current figure? ') in ('yes', 'Y', 'y'):
                    process_save(m_state, m_state.cur_save_filename)

            for name, figure in m_state.figures.items():
                m_state.cur_save_filename = None
                m_state.cur_figurename = name
                if input('Save figure %s? ' % name) in ('yes', 'Y', 'y'):
                    process_save(m_state, '')
                plot.close_figure(m_state)

        return True

    elif command == 'input':
        m_state.is_interactive = True

    else:
        raise LineParseError('No command named %s' % command)

    return 0

def parse_and_process_plot(m_state:state.GlobalState, m_tokens:deque, keep_existed):
    """ Parsing and processing `plot` and `append` commands.

    Args:
        keep_existed: Keep existed datalines.
    """
    # LL(2)

    reload_file = True  # if the file should be reloaded
    
    data_list = []
    style_list = []

    while len(m_tokens) > 0:

        is_new_file = False

        # when it could be filename:
        # force-column-selection is not set
        # no : at next
        # not starting with $ or (
        if m_state.options['force-column-selection'] == False and \
            (len(m_tokens) == 1 or m_tokens[1] != ':') or \
            (m_tokens[0] != '' and m_tokens[0][0] not in '$('):

            if io_util.file_exist(m_tokens[0]):
                is_new_file = True
                filename = get_token(m_tokens)
                logger.debug('New file found: %s' % filename)
            else:
                warn('Treat %s as column label' % m_tokens[0])

        elif m_tokens[0] == '':
            get_token(m_tokens)
        
        if not is_new_file and reload_file:
            filename = m_state.cur_open_filename
            if not filename:
                raise LineParseError('Filename expected')
            else:
                logger.debug('Exist file found: %s' % filename)
                
        # old file is reloaded once per command.
        if is_new_file or reload_file:
            m_file = sheet_util.load_file(filename,
                m_state.options['data-title'],
                m_state.options['data-delimiter'],
                m_state.options['ignore-data-comment']
            )
            if not m_file:
                warn('Cannot open file %s, skipping...' % filename)
                skip_tokens(m_tokens, ',')
                continue
            else:
                logger.debug('File loaded: %s' % m_file)
                m_state.cur_open_filename = filename

        reload_file = False

        # no column expr 
        if not m_state.options['force-column-selection'] and (
            len(m_tokens) == 0 or m_tokens[0] == ',' or
            (len(m_tokens) > 1 and m_tokens[1] == '=')):
            if m_file.cols() == 0:
                raise RuntimeError('File has no valid column')
            elif m_file.cols() == 1:
                data_list.append((m_file.get_sequence(), m_file.get_column(0),
                    m_file.get_label(0), ''))
            elif m_file.cols() == 2:
                data_list.append((m_file.get_column(0), m_file.get_column(1), 
                    m_file.get_label(1), m_file.get_label(0)))
            else:
                if m_file.cols() > 10:
                    warn('Load all %d columns to plot' % m_file.cols())
                for j in range(1, m_file.cols()):
                    data_list.append((m_file.get_column(0), m_file.get_column(j),
                        m_file.get_label(j), m_file.get_label(0)))
            logger.debug('All column in file loaded: Total %d datasets' % m_file.cols())
        
        else:
            column_expr = parse_column(m_tokens)
            column = m_file.eval_column_expr(column_expr)
            label = m_file.get_label(int(column_expr)-1) if column_expr.isdigit() else column_expr
            if column is None:  # failed
                warn('Skipping column %s with no valid data' % column_expr)
                skip_tokens(m_tokens, ',')
                continue

            # TODO MID Default x data to additional y
            # For example: plot 1:2,3 => plot 1:2, 1:3

            if len(m_tokens) > 0 and m_tokens[0] == ':':
                logger.debug('Try parsing y data')
                get_token(m_tokens)
                column_expr2 = parse_column(m_tokens)
                column2 = m_file.eval_column_expr(column_expr2)
                label2 = m_file.get_label(int(column_expr2)-1) if column_expr2.isdigit() else column_expr2
                if column2 is not None:
                    data_list.append((column, column2, label2, label))
                else:
                    skip_tokens(m_tokens, ',')
                    warn('Skipping column %s with no valid data' % column_expr2)
            else:
                data_list.append((m_file.get_sequence(), column, column_expr, ''))

        # style parameters
        styles = parse_style(m_tokens, ',', recog_comma=False)
        while len(style_list) < len(data_list): # this is for a file containing multiple columns
            style_list.append(styles)

        if len(m_tokens) > 0 and m_tokens[0] == ',':
            get_token(m_tokens)
            continue

    assert_no_token(m_tokens)

    # Broadcasting styles
    for bc_style in m_state.options['broadcast-style']:
        if bc_style in style_list[0]:
            for i in range(1, len(style_list)):
                style_list[i].setdefault(bc_style, style_list[0][bc_style])

    # TODO LOW automatically determine skip points (or can be done later)

    logger.debug('Processing plot')
    # do the plot!
    if len(data_list) > 0:
        
        # first time: create figure
        # TODO MID initiate figure instance first, and then show
        # to avoid setting before plot.
        if m_state.cur_figurename is None:
            m_state.create_figure()
            plot.update_figure(m_state)

        # handle append
        if not keep_existed:
            m_state.cur_subfigure().datalines.clear()

        for (x, y, label, xlabel), style in zip(data_list, style_list):
            m_state.cur_subfigure().add_dataline((x, y), label, xlabel, style)
        
        # Set labels
        xlabels = set((d.attr['xlabel'] for d in m_state.cur_subfigure().datalines))
        ylabels = set((d.attr['label'] for d in m_state.cur_subfigure().datalines))
        if len(xlabels) == 1:
            m_state.cur_subfigure().axes[0].label.set_style('text', xlabels.pop())
        if len(ylabels) == 1:
            m_state.cur_subfigure().axes[1].label.set_style('text', ylabels.pop())

        # Set range
        if m_state.options['adjust-range'] == 'auto' or (
            m_state.cur_subfigure().axes[0].attr['range'][0] is None or
            m_state.cur_subfigure().axes[0].attr['range'][1] is None or
            m_state.cur_subfigure().axes[1].attr['range'][0] is None or
            m_state.cur_subfigure().axes[1].attr['range'][1] is None
        ):
            logger.debug('Setting automatic range')
            process_autorange(m_state)

        plot.update_subfigure(m_state)
    else:
        warn('No valid data for plotting...')


def parse_and_process_remove(m_state:state.GlobalState, m_tokens:deque):
    """ Parse and process `remove` command.
    """

    dataline_sel = set()
    drawline_sel = set()
    text_sel = set()

    m_subfig = m_state.cur_subfigure()

    while len(m_tokens) > 0:
        elements = []

        if len(m_tokens) > 1 and m_tokens[1] == '=':
            style_name, style_val = parse_single_style(m_tokens)

            dataline_sel.update((
                int(d.name[4:]) for d in filter(lambda x:x.style[style_name] == style_val, m_subfig.datalines)))
            if m_state.options['remove-element-by-style']:
                try:
                    drawline_sel.update((
                        int(d.name[8:]) for d in filter(lambda x:x.style[style_name] == style_val, m_subfig.drawlines)))
                    text_sel.update((
                        int(d.name[4:]) for d in filter(lambda x:x.style[style_name] == style_val, m_subfig.texts)))
                except KeyError:
                    pass

        else:
            element_name = get_token(m_tokens)
            elements = m_subfig.find_elements(element_name, False)
            if not elements:
                warn('No element is selected by %s' % element_name)

            for element in elements:
                if isinstance(element, state.DataLine):
                    dataline_sel.add(int(element.name[4:]))
                elif isinstance(element, state.DrawLine):
                    drawline_sel.add(int(element.name[8:]))
                elif isinstance(element, state.Text):
                    text_sel.add(int(element.name[4:]))

    if m_state.options['prompt-multi-removal'] and len(dataline_sel) > 1:
        if input('Remove data %s?' % (' '.join((str(d) for d in dataline_sel)))) in ('y', 'Y', 'yes'):
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

    plot.update_subfigure(m_state)


def parse_and_process_set(m_state:state.GlobalState, m_tokens:deque):
    """ Parse and process `set` command.
    """
    # LL(2)
    
    if m_tokens[0] == 'default':
        get_token(m_tokens)

        has_updated = False
        if keywords.is_style_keyword(m_tokens[0]) and not keywords.is_style_keyword(m_tokens[1]):
            elements = [m_state.default_figure.subfigures[0]]
            style_list = parse_style(m_tokens)
            for s, v in style_list.items():
                has_updated = has_updated or m_state.cur_figure().set_style_recur(s, v)

        else:
            element_names = parse_token_with_comma(m_tokens)
            style_dict = parse_style(m_tokens)
            has_updated = process_set_style(m_state, element_names, style_dict, m_state.default_figure)

        if not has_updated:
            warn('No style is set')

    # TODO MID implement `set future`
    elif m_tokens[0] == 'option':
        get_token(m_tokens)

        while len(m_tokens) > 0:
            opt = get_token(m_tokens)
            arg = get_token(m_tokens)
            if arg == '=':
                arg = get_token(m_tokens)
            if opt not in m_state.options:
                warn('Skipping option %s' % opt)
            else:
                if opt not in m_state.options:
                    raise LineParseError('Invalid option: %s' % opt)
                m_state.options[opt] = translate_option_val(opt, arg)

    else:

        has_updated = False

        # Setting cur_subfigure, recursively
        if keywords.is_style_keyword(m_tokens[0]) and not keywords.is_style_keyword(m_tokens[1]):
            elements = [m_state.cur_subfigure()]
            style_list = parse_style(m_tokens)
            for s, v in style_list.items():
                has_updated = has_updated or m_state.cur_figure().set_style_recur(s, v)

        else:
            element_names = parse_token_with_comma(m_tokens)
            style_dict = parse_style(m_tokens)

            has_updated = process_set_style(m_state, element_names, style_dict, m_state)

        # TODO HIGH Implement clear

        if has_updated:
            plot.update_figure(m_state)
        else:
            warn('No style is set')


def parse_and_process_show(m_state:state.GlobalState, m_tokens:deque):
    """ Parse and process `show` command.
    """

    element_name = get_token(m_tokens)

    if element_name == 'currentfile':
        print('File opened:', m_state.cur_open_filename)
        print('File saved:', m_state.cur_save_filename)

    elif element_name == 'option' or element_name in 'options':
        if len(m_tokens) == 0:
            print('Option\tValue\n---- ----')
            for opt, val in m_state.options.items():
                print('%s\t%s' % (opt, val))
        else:
            print(m_state.options[get_token(m_tokens)])
            assert_no_token(m_tokens)

    else:   # show style
        elements = m_state.find_elements(element_name)
        if not elements:
            print('No elements selected')
            return

        # show all styles
        if len(m_tokens) == 0:
            for e in elements:
                print(e.name + ':')
                print('\n'.join(('%s=%s' % item for item in e.export_style().items())))

        # show specified style
        else:
            for style_name in m_tokens:
                style_name = keywords.style_alias.get(style_name, style_name)
                if style_name not in keywords.style_keywords:
                    warn('Skipping invalid style: %s' % style_name)
                print('%s:' % style_name)
                print('\n'.join(('%s\t%s' % (e.name, e.get_style(style_name)) 
                    for e in elements)))
        

def process_autorange(m_state:state.GlobalState):
    max_x = max([np.max(d.x) for d in m_state.cur_subfigure().datalines])
    min_x = min([np.min(d.x) for d in m_state.cur_subfigure().datalines])
    max_y = max([np.max(d.y) for d in m_state.cur_subfigure().datalines])
    min_y = min([np.min(d.y) for d in m_state.cur_subfigure().datalines])

    x_ticks = scale.get_ticks(min_x, max_x)
    y_ticks = scale.get_ticks(min_y, max_y)

    m_state.cur_subfigure().axes[0].set_style('range', (x_ticks[0], x_ticks[-1], x_ticks[1]-x_ticks[0]))
    m_state.cur_subfigure().axes[1].set_style('range', (y_ticks[0], y_ticks[-1], y_ticks[1]-y_ticks[0]))
    logger.debug('xrange set: %g:%g' % (x_ticks[0], x_ticks[-1]))
    logger.debug('yrange set: %g:%g' % (y_ticks[0], y_ticks[-1]))


def process_set_style(m_state, element_names, style_dict, scope):

    for element_name in element_names:
        elements = scope.find_elements(element_name)
    if not elements:
        warn('No element is selected by %s' % element_name)
        return False

    has_updated = False
    for e in elements:
        for s, v in style_dict.items():
            # By default, failure to set style will cause error.
            try:
                e.set_style(s, v)
            except (KeyError, ValueError):
                raise LineProcessError('Cannot set %s to style %s for %s' % (
                    v, s, e.name
                ))
            else:
                has_updated = True
    return has_updated


def process_split(m_state:state.GlobalState, hsplitnum:int, vsplitnum:int):
    """ Split current figure by certain grids.
    Will remove additional subfigures if necessary.
    """

    if hsplitnum < 1 or vsplitnum < 1:
        raise LineProcessError('Split number must be greater or equal than 1')

    m_fig = m_state.cur_figure()
    hsplit, vsplit = m_fig.get_attr('split')
    hspacing, vspacing = m_fig.get_style('spacing')

    subfig_state_2d = []
    for i in range(vsplitnum):
        subfig_state_2d.append([])
        for j in range(hsplitnum):
            if i < vsplit and j < hsplit:
                subfig_state_2d[i].append(m_fig.subfigures[i*hsplit + j])
            else:
                subfig_state_2d[i].append(m_state.default_figure.subfigures[0].copy())

            subfig_state_2d[i][j].name = 'subfigure%d' % (i*hsplitnum + j)
            subfig_state_2d[i][j].set_attr('rpos', (
                j / hsplitnum + hspacing / 2,
                (vsplitnum - 1 - i) / vsplitnum + vspacing / 2
            ))
            subfig_state_2d[i][j].set_attr('rsize', (
                1 / hsplitnum -  hspacing,
                1 / vsplitnum - vspacing
            ))
    
    m_fig.subfigures = list(itertools.chain.from_iterable(subfig_state_2d))
    plot.update_figure(m_state, redraw_subfigures=True)
    m_fig.set_style('split', [hsplitnum, vsplitnum])


def process_save(m_state:state.GlobalState, filename:str):
    """ Saving current figure.
    """

    if not filename:
        if m_state.cur_save_filename:
            filename = input('Enter filename here (default: %s): ' % m_state.cur_save_filename)
        else:
            filename = input('Enter filename here: ')
        if not filename:
            logger.info('Saving cancelled')
            return

    if m_state.options['prompt-overwrite'] and io_util.file_exist(filename):
        answer = input('Overwrite current file "%s"? ' % filename)
        if not answer in ('yes', 'y', 'Y'):
            print('Canceled')
            return

    plot.save_figure(m_state, filename)
    m_state.cur_save_filename = filename

def get_completions(tokens):
    pass
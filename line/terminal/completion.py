
import prompt_toolkit as pt
import re

from .. import keywords
from ..style import palette
from .completion_util import get_filelist
from . import lexer
from ..errors import LineParseError
from ..parse_util import is_quoted, strip_quote
from .. import io_util
from .. import defaults

class Completer(pt.completion.Completer):
    
    WordMatcher = re.compile(r'[^,:=;#\\\"\'\s]+')

    def __init__(self, m_state=None):
        self.m_state = m_state
        self.inspect_cache = {}
        super().__init__()

    def get_completions(self, document:pt.document.Document, complete_event):

        d = document.get_word_before_cursor(Completer.WordMatcher)

        # We are in the first word
        if document.find_start_of_previous_word() is None or \
            document.get_start_of_line_position() == document.find_start_of_previous_word() and \
            d:
            yield from self.generate_completion_list(d, keywords.all_command_keywords, lambda x:x+' ')

        # Otherwise
        else:
            # String --> filename
            if d.startswith('\'') or d.startswith('"'):
                yield from self.generate_completion_list(d, get_filelist(d))
                return

            try:
                tokens = lexer.split(document.text[:document.cursor_position])[0]
            except LineParseError:
                return

            if d.endswith((':', ',', '=')):
                d = ''
            elif d != '':
                d = tokens[-1]

            # get index before current word and index OF current word
            cur_idx = len(tokens) - 1 if d else len(tokens)

            if cur_idx > 2 and tokens[cur_idx-1] == '=' and tokens[cur_idx-2] in ('lc', 'c', 'color', 'linecolor', 'edgecolor', 'fillcolor'):
                from .. import style
                yield from self.generate_completion_list(d, self.complete_colors(d), filter_=False)

            command = keywords.command_alias.get(tokens[0], tokens[0])

            if command in ('plot', 'plotr', 'hist', 'append', 'scatter'):
                if cur_idx == 1:
                    if self.m_state:
                        yield from self.generate_completion_list(d, self.m_state._vmhost.variables.keys(), self.format_varname)
                elif cur_idx == 2 or (len(tokens)>2 and tokens[cur_idx-2] == ',') or tokens[cur_idx-1] in ':,':
                    if tokens[cur_idx-1] in ':,':
                        inspect_idx = cur_idx-1
                        while inspect_idx > 1 and tokens[inspect_idx-1] != ',':
                            inspect_idx -= 1
                        varname = tokens[inspect_idx]
                    else:    # just the left one
                        varname = tokens[cur_idx-1]

                    if is_quoted(varname):
                        yield from self.complete_title(d, strip_quote(varname))

                    if self.m_state:    # model will only be available after state is initialized.
                        if not is_quoted(varname) and '__var' + varname in self.m_state._vmhost.variables:
                            from .. import model
                            yield from self.generate_completion_list(d, model.util.columns(self.m_state._vmhost.get_variable(varname)))
                        yield from self.generate_completion_list(d, self.m_state._vmhost.variables.keys(), self.format_varname)

                    if tokens[cur_idx-1] not in ':,':
                        yield from self.generate_completion_list(d, keywords.all_style_keywords, self.format_stylename)
                elif not tokens[cur_idx-1].endswith('='):
                    yield from self.generate_completion_list(d, keywords.all_style_keywords, self.format_stylename)

            elif command in ('set', 'show', 'remove', 'style', 'legend'):
                if cur_idx == 1 or tokens[cur_idx-1] == ',':
                    if command == 'set':
                        yield from self.generate_completion_list(d, ('option ', 'default ', 'style ', 'compact ', 'palette '))
                    elif command == 'show':
                        yield from self.generate_completion_list(d, ('currentfile ', 'option ', 'palette '))
                    
                    yield from self.generate_completion_list(d, self.complete_elements(d), filter_=False)

                elif cur_idx == 2 and tokens[cur_idx-1] == 'option':
                    yield from self.generate_completion_list(d, (x+'=' for x in defaults.default_options))
                    
                elif cur_idx == 2 and tokens[cur_idx-1] == 'palette':
                    yield from self.generate_completion_list(d, ('line ', 'point ', 'bar ', 'polygon '))
                    yield from self.generate_completion_list(d, palette.PALETTES)

                elif cur_idx == 3 and tokens[cur_idx-2] == 'palette':
                    yield from self.generate_completion_list(d, palette.PALETTES)

                elif d.startswith('+'):
                    if self.m_state:
                        try:
                            yield from self.generate_completion_list(d, map(lambda x: '+' +x.classname, self.m_state.class_stylesheet.data))
                        except AttributeError:
                            pass

                elif not tokens[cur_idx-1].endswith('='):
                    yield from self.generate_completion_list(d, keywords.all_style_keywords, self.format_stylename)

            elif command == 'fit':
                if cur_idx == 1 or tokens[cur_idx-1] == ',':
                    yield from self.generate_completion_list(d, self.complete_elements(d), filter_=False)
                else:
                    yield from (x for x in ('linear', 'quad', 'exp', 'prop'))

            elif command == 'cd':
                yield from self.generate_completion_list(d, get_filelist(d, True))

            elif command in ('load', 'save', 'source'):
                yield from self.generate_completion_list(d, get_filelist(d, False))

                
    def generate_completion_list(self, d, candidates, formatter=None, filter_=True):
        if filter_:
            if formatter:
                return (pt.completion.Completion(formatter(c), start_position=-len(d)) for c in candidates if c.startswith(d))    
            else:
                return (pt.completion.Completion(c, start_position=-len(d)) for c in candidates if c.startswith(d))
        else:
            if formatter:
                return (pt.completion.Completion(formatter(c), start_position=-len(d)) for c in candidates)
            else:
                return (pt.completion.Completion(c, start_position=-len(d)) for c in candidates)

    def format_varname(self, x):
        return x[5:] if x.startswith('__var') else x + '('

    def format_stylename(self, x):
        return x+'='

    def complete_elements(self, d, subfigure_only=False):
        yield from (c for c in keywords.element_keywords if c.startswith(d))

        if self.m_state and self.m_state.cur_figurename:
            if subfigure_only:
                yield from map(lambda x:x.name, self.m_state.gca().get_all_children(lambda x:x.name.startswith(d)))
            else:
                yield from map(lambda x:x.name, self.m_state.gcf().get_all_children(lambda x:x.name.startswith(d)))

    def complete_colors(self, d):
        from .. import style
        ud = d.upper()
        return (c.lower() for c in style.Color.__dict__ if not c.startswith('__') and c.startswith(ud))

    def complete_title(self, d, filename):
        if filename not in self.inspect_cache:
            try:
                l = open(filename, 'r').readline().strip()
            except IOError:
                self.inspect_cache[filename] = ()
            else:
                if l.startswith('#'):
                    self.inspect_cache[filename] = ()
                else:
                    split_by_white = l.split()
                    if ',' in l:
                        split_by_comma = l.split(',')
                        if len(split_by_comma) > len(split_by_white):
                            self.inspect_cache[filename] = split_by_comma
                    else:
                        self.inspect_cache[filename] = split_by_white

        return self.generate_completion_list(d, self.inspect_cache[filename])


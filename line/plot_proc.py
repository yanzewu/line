
import re
import numpy as np

from . import state
from . import model
from . import io_util
from . import errors

from .style_proc import *
from . import expr_proc


class PlottingPackage:

    def __init__(self, hint1=None, expr1=None, hint2=None, expr2=None, style=None):
        self.hint1 = hint1
        self.expr1 = expr1
        self.hint2 = hint2
        self.expr2 = expr2
        self.style = style

        self.xdata = None
        self.ydata = None

        self.source = None
        self.xlabel = None
        self.ylabel = None

    def __repr__(self):
        return ('PlottingGroup(hint1=%s expr1=%s hint2=%s expr2=%s xlabel=%s '
            'ylabel=%s data1=%s data2=%s style=%s)') % (
            self.hint1, self.expr1, self.hint2, self.expr2, 
            self.xlabel, self.ylabel, self._repl_sheet(self.xdata), 
            self._repl_sheet(self.ydata), self.style
        )

    def _repl_sheet(self, s):
        if isinstance(s, model.SheetCollection):
            return type(s)
        else:
            return '%s[%s]' % (type(s), s.shape) if s is not None else 'None'


class PlotParser:

    M_PLOT = 0
    M_HIST = 1

    def __init__(self, mode=M_PLOT):
        self.mode = mode

    def parse(self, m_state:state.GlobalState, m_tokens):
        
        self.m_state = m_state
        self.m_tokens = m_tokens
        self.plot_groups = []
        self.cur_hint = None
        self.cur_xexpr = None

        while len(self.m_tokens) > 0:
            try:
                if self.mode == PlotParser.M_PLOT:
                    self.parse_single_group()
                elif self.mode == PlotParser.M_HIST:
                    self.parse_single_hist_group()
            except Exception:
                raise

                # warn('Skipping invalid plotting section')
                # skip_tokens(m_tokens, ',')
            if self.next() == ',':
                get_token(self.m_tokens)
        
        logger.debug('Plot groups:' + str(self.plot_groups))

    def parse_single_group(self):
        
        pg = PlottingPackage()
        self.token_stack = []

        self.shift_expr()

        if self.next() == ':':  # expr :
            pg.hint1 = self.cur_hint
            pg.expr1 = self.token_stack.pop()
            get_token(self.m_tokens)
            self._parse_y(pg, must_begin_with_expr=True)
        elif self.next() not in ' ,;=' and (self._must_be_expr(self.next(), self.next(1)) or self.next(1) == ':'):  # hint expr ?
            pg.hint1 = self.token_stack.pop()
            pg.expr1 = parse_expr(self.m_tokens)    

            if self.next() == ':':  # hint expr :
                get_token(self.m_tokens)
                self._parse_y(pg, must_begin_with_expr=True)
            else:   # hint expr
                pg.hint2 = pg.hint1
                pg.expr2 = pg.expr1
                if is_quoted(pg.expr1) or pg.hint1 != self.cur_hint:
                    self.cur_xexpr = None # if it's a file or hint changes, reset x index
                pg.expr1 = self.cur_xexpr
                pg.style = self._parse_style()

        elif self.next(1) == '=':    # expr style
            pg.hint1 = self.cur_hint
            pg.expr1 = self.cur_xexpr
            pg.hint2 = pg.hint1
            pg.expr2 = self.token_stack.pop()
            pg.style = self._parse_style()

        else:   # got a style keyword, but not sure
            pg.hint1 = self.cur_hint
            pg.expr1 = self.cur_xexpr
            self._parse_group2(pg)

        self.cur_hint = pg.hint2
        self.cur_xexpr = pg.expr1
        
        if pg.expr1 is not None:
            pg.xdata = self.evaluate(pg.hint1, pg.expr1)
        pg.ydata = self.evaluate(pg.hint2, pg.expr2)
        # missing x index
        if pg.expr1 is None:
            # file: take first column as index, unless not possible
            if is_quoted(pg.expr2):
                if model.util.cols(pg.ydata) == 1:
                    pg.xdata = model.util.get_index(pg.ydata)
                else:
                    pg.xdata = pg.ydata[:, 0]
                    pg.ydata = pg.ydata[:, 1:]
            # others: use sequence as index
            else:
                pg.xdata = model.util.get_index(pg.ydata)

        logger.debug('New plotting group: ' + str(pg))
        self._add_plotgroup(pg)

    def parse_single_hist_group(self):
        pg = PlottingPackage()
        pg.hint1 = self.cur_hint
        pg.expr1 = self.cur_xexpr

        self.token_stack = []
        self._parse_y(pg)
        self.cur_hint = pg.hint2
        pg.ydata = self.evaluate(pg.hint2, pg.expr2)
        logger.debug('New histogram group: ' + str(pg))

        pg.source = [pg.hint2 if pg.hint2 else pg.expr2]
        
        ycols = model.util.cols(pg.ydata)
        if ycols == 1:
            ylabels = model.util.columns(pg.ydata, None)
            if ylabels is None:
                ylabels = [pg.expr2 if pg.expr2 else '']
        else:
            ylabels = model.util.columns(pg.ydata, (pg.expr2 if pg.expr2 else '') + '[%d]')

        for idx in range(ycols):
            m_pg = PlottingPackage(pg.hint1, pg.expr1, pg.hint2, pg.expr2, pg.style.copy())
            m_pg.ydata = pg.ydata if ycols == 1 else model.util.loc_col(pg.ydata, idx)
            m_pg.ylabel = ylabels[idx]
            m_pg.source = pg.source[idx // (ycols // len(pg.source)) ]
            self.plot_groups.append(m_pg)

    def _parse_y(self, pg:PlottingPackage, must_begin_with_expr=False):
        # must_be_expr => expr (style...) 
        # otherwise => expr? (style...)
        self.shift_expr()
        if must_begin_with_expr or not self.next() or self.next() == ',':
            pg.hint2 = pg.hint1
            pg.expr2 = self.token_stack.pop()
            pg.style = self._parse_style()
        elif self.next() not in ' ,;=' and self._must_be_expr(self.next(), self.next(1)):
            pg.hint2 = self.token_stack.pop()
            pg.expr2 = parse_expr(self.m_tokens)
            pg.style = self._parse_style()
        elif self.next(1) == '=':    # expr style
            pg.hint2 = pg.hint1
            pg.expr2 = self.token_stack.pop()
            pg.style = self._parse_style()
        else:
            self._parse_group2(pg)

    def _parse_group2(self, pg:PlottingPackage):
        # expr? style...
        m_tokens2 = self.m_tokens.copy()
        try:
            pg.style = parse_style(m_tokens2, ',', recog_comma=False, recog_class=False, raise_error=True)
        except LineParseError as e:
            if e.message.startswith('Invalid style') or e.message.startswith('Incomplete command'):
                pg.hint2 = self.token_stack.pop()
                pg.expr2 = parse_expr(self.m_tokens)
                pg.style = self._parse_style()
            else:
                pg.style = self._parse_style()
        else:
            pg.hint2 = pg.hint1
            pg.expr2 = self.token_stack.pop()
            self.m_tokens = m_tokens2
            
    def _add_plotgroup(self, pg:PlottingPackage):

        if isinstance(pg.xdata, model.SheetCollection):
            pg.xdata = pg.xdata.flatten()
        if isinstance(pg.ydata, model.SheetCollection):
            pg.source = [d.source for d in pg.ydata.data]
            pg.ydata = pg.ydata.flatten()
        else:
            pg.source = [pg.hint2 if pg.hint2 else pg.expr2]

        xcols = model.util.cols(pg.xdata)
        ycols = model.util.cols(pg.ydata)
        expr1_str = pg.expr1 if pg.expr1 else '%d'
        expr2_str = pg.expr2 if pg.expr2 else '%d'
        if xcols == 1:
            xlabels = model.util.columns(pg.xdata, expr1_str)
        else:
            xlabels = model.util.columns(pg.xdata, expr1_str + '[%d]')
        if ycols == 1:
            ylabels = model.util.columns(pg.ydata, expr2_str)
        else:
            ylabels = model.util.columns(pg.ydata, expr2_str + '[%d]')

        for i in range(len(xlabels)):
            xlabels[i] = self._format_label(xlabels[i], expr1_str)
        for i in range(len(ylabels)):
            ylabels[i] = self._format_label(ylabels[i], expr2_str)

        # split columns
        if xcols == 1 or xcols == ycols:
            for idx in range(ycols):
                m_pg = PlottingPackage(pg.hint1, pg.expr1, pg.hint2, pg.expr2, pg.style.copy())
                m_pg.xdata = pg.xdata if xcols == 1 else model.util.loc_col(pg.xdata, idx)
                m_pg.ydata = pg.ydata if ycols == 1 else model.util.loc_col(pg.ydata, idx)
                m_pg.xlabel = xlabels[0] if xcols == 1 else xlabels[idx]
                m_pg.ylabel = ylabels[idx]
                m_pg.source = pg.source[idx // (ycols // len(pg.source))]  # the only situation with multiple idx > ycols is SheetCollection,
                                                                            # so this should be fine. But careful when refactory.
                self.plot_groups.append(m_pg)
        else:
            raise errors.LineProcessError("Column number not match: x:%d, y:%d" % (model.util.cols(pg.xdata), model.util.cols(pg.ydata)))

    def shift_expr(self):
        if self._must_be_expr(self.next(), None):
            self.token_stack.append(parse_expr(self.m_tokens))
        else:
            return self.token_stack.append(get_token_raw(self.m_tokens))

    def next(self, idx=0):
        return lookup_raw(self.m_tokens, idx, True)

    def _parse_style(self):
        if len(self.m_tokens) == 0:
            return {}
        else:
            return parse_style(self.m_tokens, ',', recog_comma=False, recog_class=False)

    def _must_be_expr(self, token, token2):
        return not is_quoted(token) and \
            (token.startswith('(') or \
            (
                '(' in token and 
                token[:token.index('(')] in expr_proc.ExprEvaler.FUNCTIONS) or \
            token.startswith('$') or \
            not self._must_be_style(token, token2))

    def _must_be_style(self, token, token2):
        return token2 == '=' or \
            keywords.is_style_desc(token) or \
            (keywords.is_style_keyword(token) and self._satisfy_style(token, token2))

    def _satisfy_style(self, style_name, style_val):
        try:
            translate_style_val(style_name, style_val)
        except Exception:
            return False
        else:
            return True

    def _is_quoted(self, expr):
        return expr.startswith('\'') or expr.startswith('"')

    def _format_label(self, label, repl):
        return re.sub(r'\$(\d+)', r'col(\1)', 
            re.sub(r'\<expr(\d+)\>', repl + r'[\1]', label
                ).replace('<expr>', repl)
            ).replace('$', '')

    def evaluate(self, hintvar, expr):
        evaler = expr_proc.ExprEvaler(self.m_state._vmhost.variables, self.m_state.file_caches)
        if expr.isdigit():
            expr = '$' + expr
        if is_quoted(expr):
            if hintvar is None or io_util.file_or_wildcard_exist(strip_quote(expr)):
                expr = 'load(%s)' % expr if not ('*' in expr or '?' in expr) else 'load(*expand(%s))' % expr
            else:
                expr = 'col(%s)' % expr
        evaler.load(expr, omit_dollar=True)
        if hintvar:
            evaler2 = expr_proc.ExprEvaler(self.m_state._vmhost.variables, self.m_state.file_caches)
            if hintvar.startswith('$('):
                evaler2.load(hintvar)
                hintvalue = evaler2.evaluate()
            else:
                if '*' in hintvar or '?' in hintvar:
                    evaler2.load('load(*expand("%s"))' % strip_quote(hintvar))
                    hintvalue = evaler2.evaluate()
                else:
                    evaler2.load_singlevar(hintvar)
                    hintvalue = evaler2.evaluate_singlevar()
        else:
            hintvalue = None
        return evaler.evaluate_with_hintvar(hintvalue)
        
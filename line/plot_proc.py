
import numpy as np

from . import state
from . import sheet_util
from . import io_util

from .parse import *
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
            self._parse_y(pg)
        elif self.next() not in ' ,;=' and (self._must_be_expr(self.next(), self.next(1)) or self.next(1) == ':'):  # hint expr ?
            pg.hint1 = self.token_stack.pop()
            pg.expr1 = parse_column(self.m_tokens)    

            if self.next() == ':':  # hint expr :
                get_token(self.m_tokens)
                self._parse_y(pg)
            else:   # hint expr
                pg.hint2 = pg.hint1
                pg.expr2 = pg.expr1
                if self._is_quoted(pg.expr1) or pg.hint1 != self.cur_hint:
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
            # file: take first column as index, unless specified explicitly
            if self._is_quoted(pg.expr2):
                pg.xdata = np.arange(pg.ydata.shape[0]) if sheet_util.cols(pg.ydata) == 1 else pg.ydata.get_column(0)
                if sheet_util.cols(pg.ydata) > 1:
                    pg.ydata = pg.ydata.get_column(slice(1,None))
            # others: use sequence as index
            else:
                pg.xdata = np.arange(pg.ydata.shape[0])

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

        if isinstance(pg.hint2, sheet_util.SheetFile):
            pg.source = pg.hint2.filename.copy()
        else:
            pg.source = [pg.hint2 if pg.hint2 else pg.expr2]
        
        ycols = sheet_util.cols(pg.ydata)
        if ycols == 1:
            ylabels = sheet_util.columns(pg.ydata, None)
            if ylabels is None:
                ylabels = [pg.expr2 if pg.expr2 else '']
        else:
            ylabels = sheet_util.columns(pg.ydata, (pg.expr2 if pg.expr2 else '') + '[%d]')

        if ycols == 1:
            pg.source = pg.source[0]
            pg.ylabel = ylabels[0]
            self.plot_groups.append(pg)
        elif ycols > 1:
            assert len(pg.source) == 1 or len(pg.source) == ycols
            for idx in range(ycols):
                m_pg = PlottingPackage(pg.hint1, pg.expr1, pg.hint2, pg.expr2, pg.style)
                m_pg.ydata = sheet_util.loc_col(pg.ydata, idx)
                m_pg.ylabel = ylabels[idx]
                m_pg.source = pg.source[idx] if len(pg.source) > 1 else pg.source[0]
                self.plot_groups.append(m_pg)

    def _parse_y(self, pg:PlottingPackage):
        
        self.shift_expr()
        if not self.next() or self.next() == ',':
            pg.hint2 = pg.hint1
            pg.expr2 = self.token_stack.pop()
            pg.style = {}
        elif self.next() not in ' ,;=' and self._must_be_expr(self.next(), self.next(1)):
            pg.hint2 = self.token_stack.pop()
            pg.expr2 = parse_column(self.m_tokens)
            pg.style = self._parse_style()
        elif self.next(1) == '=':    # expr style
            pg.hint2 = pg.hint1
            pg.expr2 = self.token_stack.pop()
            pg.style = self._parse_style()
        else:
            self._parse_group2(pg)

    def _parse_group2(self, pg:PlottingPackage):
        m_tokens2 = self.m_tokens.copy()
        try:
            pg.style = parse_style(m_tokens2, ',', recog_comma=False, recog_class=False, raise_error=True)
        except LineParseError as e:
            if e.message.startswith('Invalid style') or e.message.startswith('Incomplete command'):
                pg.hint2 = self.token_stack.pop()
                pg.expr2 = parse_column(self.m_tokens)
                pg.style = self._parse_style()
            else:
                pg.style = self._parse_style()
        else:
            pg.hint2 = pg.hint1
            pg.expr2 = self.token_stack.pop()
            self.m_tokens = m_tokens2
            
    def _add_plotgroup(self, pg:PlottingPackage):

        if isinstance(pg.hint2, sheet_util.SheetFile):
            pg.source = pg.hint2.filename.copy()
        else:
            pg.source = [pg.hint2 if pg.hint2 else pg.expr2]
        
        if isinstance(pg.xdata, sheet_util.SheetFile):
            pg.xdata = pg.xdata.flatten()
        if isinstance(pg.ydata, sheet_util.SheetFile):
            pg.ydata = pg.ydata.flatten()

        xcols = sheet_util.cols(pg.xdata)
        ycols = sheet_util.cols(pg.ydata)
        if xcols == 1:
            xlabels = sheet_util.columns(pg.xdata, None)
            if xlabels is None:
                xlabels = [pg.expr1 if pg.expr1 else '']
        else:
            xlabels = sheet_util.columns(pg.xdata, (pg.expr1 if pg.expr1 else '') + '[%d]')
        if ycols == 1:
            ylabels = sheet_util.columns(pg.ydata, None)
            if ylabels is None:
                ylabels = [pg.expr2 if pg.expr2 else '']
        else:
            ylabels = sheet_util.columns(pg.ydata, (pg.expr2 if pg.expr2 else '') + '[%d]')

        # split columns
        if xcols == 1 and ycols == 1:
            pg.source = pg.source[0]
            pg.xlabel = xlabels[0]
            pg.ylabel = ylabels[0]
            self.plot_groups.append(pg)
        elif xcols == 1 and ycols > 1:
            assert len(pg.source) == 1 or len(pg.source) == ycols
            for idx in range(ycols):
                m_pg = PlottingPackage(pg.hint1, pg.expr1, pg.hint2, pg.expr2, pg.style)
                m_pg.xdata = pg.xdata
                m_pg.ydata = sheet_util.loc_col(pg.ydata, idx)
                m_pg.xlabel = xlabels[0]
                m_pg.ylabel = ylabels[idx]
                m_pg.source = pg.source[idx] if len(pg.source) > 1 else pg.source[0]
                self.plot_groups.append(m_pg)
        elif xcols == ycols:
            assert len(pg.source) == 1 or len(pg.source) == ycols   # WARNING: assertion will fail when plotting all columns from wildcard
            for idx in range(ycols):
                m_pg = PlottingPackage(pg.hint1, pg.expr1, pg.hint2, pg.expr2, pg.style)
                m_pg.xdata = sheet_util.loc_col(pg.xdata, idx)
                m_pg.ydata = sheet_util.loc_col(pg.ydata, idx)
                m_pg.xlabel = xlabels[idx]
                m_pg.ylabel = ylabels[idx]
                m_pg.source = pg.source[idx] if len(pg.source) > 1 else pg.source[0]
                self.plot_groups.append(m_pg)
        else:
            raise LineProcessError("Column number not match: x:%d, y:%d" % (self._cols(pg.xdata, self._cols(pg.ydata))))

    def shift_expr(self):
        if self._must_be_expr(self.next(), None):
            self.token_stack.append(parse_column(self.m_tokens))
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
        return not self._is_quoted(token) and \
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

    def evaluate(self, hintvar, expr):
        evaler = expr_proc.ExprEvaler(self.m_state.variables, self.m_state.file_caches)
        if expr.isdigit():
            expr = '$' + expr
        if self._is_quoted(expr):
            if hintvar is None or io_util.file_or_wildcard_exist(strip_quote(expr)):
                expr = 'load(%s)' % expr
            else:
                expr = 'col(%s)' % expr
        evaler.load(expr, omit_dollar=True)
        return evaler.evaluate_with_hintvar(hintvar)
        
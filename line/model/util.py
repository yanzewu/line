import pandas
import numpy as np

from . import sheet


def loc_col(mat, colidx:int):
    """ Locate column by index (always starting from 0!)
    """
    if isinstance(mat, pandas.DataFrame):
        return pandas.DataFrame(mat.iloc[:, colidx])
    else:
        return mat[:, colidx]


def loc_col_str(mat, colname:str):
    """ Locate column by string. Will parse numbers as integers.
    Reads `SourceableSheet.BEGIN` for offset convention.
    """
    
    if colname.isdigit():
        colidx = int(colname) - sheet.SourceableSheet.BEGIN
        if colidx == -1:
            return get_index(mat)
        elif colidx < 0:
            raise ValueError('Index must be positive')

        if isinstance(mat, pandas.DataFrame):
            return mat.iloc[:, colidx]
        else:
            return mat[:, colidx]
    else:
        if isinstance(mat, pandas.DataFrame):
            return mat.loc[:, colname]
        else:
            return mat[:, colname]


def loc_col_wildcard(mat, colname:str, expand_range=True):
    """ Locate all columns matched by wildcard.
    If `expand_range` is set and colname is "a-b"/"a:b"/"a:b:c" where both a,b,c are numbers,
    match indices instead of column names.

    raises `KeyError` if nothing is matched.
    """

    import re
    import fnmatch

    if isinstance(mat, sheet.SheetCollection):
        return sheet.SheetCollection([
            sheet.SourceableSheet(loc_col_wildcard(x, colname, expand_range=expand_range)) for x in mat.data],
            mat.name_convention)

    if expand_range and re.match(r'\d+\-\d+$', colname):
        a, b = colname.split('-')
        indices = np.arange(int(a)-sheet.SourceableSheet.BEGIN, int(b)+1-sheet.SourceableSheet.BEGIN)
    elif expand_range and re.match(r'\d+\:\d+$', colname):
        a, b = colname.split(':')
        indices = slice(int(a)-sheet.SourceableSheet.BEGIN, int(b)-sheet.SourceableSheet.BEGIN)
    elif expand_range and re.match(r'\d+\:\d+\:\d+$', colname):
        a, b, c = colname.split(':')
        indices = slice(int(a)-sheet.SourceableSheet.BEGIN, int(c)-sheet.SourceableSheet.BEGIN, int(b))
    else:
        c = columns(mat)
        indices = np.array([i for i in range(len(c)) if fnmatch.fnmatch(c[i], colname)])

    if isinstance(indices, np.ndarray) and len(indices) == 0:
        raise KeyError("Nothing is matched")

    if isinstance(mat, pandas.DataFrame):
        return mat.iloc[:, indices]
    else:
        return mat[:, indices]


def columns(mat, title_sub='%d'):
    """ Get column titles.
    Return title_sub % (integer) sequences (start from 1) for arrays.
    """
    
    if isinstance(mat, pandas.DataFrame):
        return _make_cols(mat.columns, title_sub)
    elif isinstance(mat, sheet.SourceableSheet):
        return _make_cols(mat.columns(), title_sub)
    elif title_sub is not None:
        return _make_cols(list(range(cols(mat))), title_sub)
    else:
        return None


def _make_cols(columns_, title_sub):

    if len(columns_) == 0:
        return
    if isinstance(columns_[0], int):
        if '%d' in title_sub:
            return [title_sub % (c+1) for c in columns_]
        else:
            return [title_sub] * len(columns_)
    else:
        return [str(c) for c in columns_]

def cols(mat):
    """ Return number of columns of 1D and 2D array.
    """
    try:
        return mat.shape[1]
    except IndexError:
        return 1

def get_index(mat):

    if isinstance(mat, sheet.SheetCollection):
        return get_index(mat.data[0])
    elif isinstance(mat, sheet.SourceableSheet):
        return mat.index()
    else:
        return np.arange(sheet.SourceableSheet.BEGIN, sheet.SourceableSheet.BEGIN + mat.shape[0])

def stack(*mats):

    c = []
    for m in mats:
        if isinstance(m, (pandas.DataFrame, pandas.Series)):
            c.append(m)
        elif isinstance(m, sheet.SourceableSheet):
            c.append(m.data)
        else:
            c.append(pandas.DataFrame(m))

    return sheet.SourceableSheet(pandas.concat(c, axis=1), source='<expr>')

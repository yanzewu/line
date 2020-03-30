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

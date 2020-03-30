
import pandas as pd
import numpy as np


class Source:

    def __init__(self, value=None):
        """ Value may be str / None.
        """
        self.value = value
        self.nodes = []

    def applies_to(self, others:list):
        self.nodes = others

    def __str__(self):
        if not self.nodes:
            if self.value is None:
                return ''
            else:
                return str(self.value)
        else:
            return self.value % (str(n) for n in self.nodes)


class SourceableSheet(np.lib.mixins.NDArrayOperatorsMixin):

    BEGIN_PYTHON = 0
    BEGIN_MATLAB = 1
    BEGIN = BEGIN_MATLAB

    def __init__(self, data, source=None):

        if isinstance(data, pd.DataFrame):
            self.data = data.copy()
        elif isinstance(data, SourceableSheet):
            self.data = data.data.copy()
            self.source = data.source
        else:
            try:
                self.data = pd.DataFrame(data)
            except ValueError:
                raise 

        if isinstance(source, Source):
            self.source = source
        else:
            assert source is None or isinstance(source, str)
            self.source = Source(source)

        self.iloc = self.data.iloc
        self.loc = self.data.loc
        self.shape = self.data.shape

    def __getitem__(self, idx):

        if isinstance(idx, int):
            return self.column_iloc(idx)
        elif isinstance(idx, str):
            return self.column_sloc(idx)
        elif isinstance(idx, (slice, tuple)):
            return self.slice_loc(idx)
        else:
            raise ValueError(idx)
    
    def cols(self):
        return self.shape[1]

    def index(self):
        """ Get a sequence of indicies [begin, begin+N)
        """
        return np.arange(self.BEGIN, self.data.shape[0] + self.BEGIN)

    def column_sloc(self, title):
        """ Get column by title
        """
        return SourceableSheet(self.data.loc[:, title], self.source)
        
    def column_iloc(self, idx):
        """ Get column by indices
        """
        if self.BEGIN > 0 and idx < self.BEGIN:
            if idx == self.BEGIN - 1:
                return self.index()
            else:
                raise IndexError(idx)
        return SourceableSheet(self.data.iloc[:, idx - self.BEGIN], self.source)

    def slice_loc(self, slice_):
        """ Locate element/column by slice. Always follow python's convention (start from 0)
        """
        if (isinstance(slice_, tuple) and isinstance(slice_[1], str)) or isinstance(slice_, str):
            r = self.data.loc[slice_]
        else:
            r = self.data.iloc[slice_]
        if isinstance(r, pd.Series):
            return SourceableSheet(r, None)
        else:
            return r

    def copy(self):
        return SourceableSheet(self.data, self.source)

    def columns(self):
        return list(self.data.columns)
        
    def has_column(self, column):
        return column in self.data.columns

    def to_numpy(self):
        return self.data.to_numpy()

    def __repr__(self):
        return 'Sheet(%s, source=%s)' % (self.data, self.source)

    def __array__(self):
        return self.data.values

    def __array_ufunc__(self, ufunc, method, *inputs, **kwargs):

        if 'out' in kwargs:
            return NotImplemented

        r = getattr(ufunc, method)(*(i if i is not self else self.data for i in inputs), **kwargs)
        self.shape = self.data.shape
        if isinstance(r, (pd.DataFrame, pd.Series)):
            return SourceableSheet(r, '<expr>')
        else:
            return r


class SheetCollection:

    def __init__(self, datalist:list, name_convention=r'%F:%T'):
        """ Datalist is required to be SourceableSheet
        """

        self.data = datalist.copy()
        self.name_convention = name_convention

    def add_sheet(self, other):
        self.data.append(SourceableSheet(other))

    def flatten(self):
        """ Merge all sheets into a 2D array.
        """
        new_data = []
        sources = [str(d.source) for d in self.data]
        for d, fn in zip(self.data, sources):
            new_data_ = d.data
            new_data_.columns = [
                self.name_convention.replace(r'%T',str(c)).replace(r'%F',fn) for c in d.columns()
            ]
            new_data.append(new_data_)
        return SourceableSheet(pd.concat(new_data, axis=1), None)

    def __getitem__(self, idx):
        return self.loc_dense(idx)

    def loc_dense(self, idx):
        return SheetCollection(self.loc_loose(idx), self.name_convention).flatten()

    def loc_loose(self, idx):
        return [d[idx] for d in self.data]


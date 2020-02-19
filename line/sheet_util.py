
import csv
import re
import io
import os.path
import logging
import pandas
import numpy as np
import warnings

logger = logging.getLogger('line')

SNIFF_NUM = 5

class SheetFile(np.lib.mixins.NDArrayOperatorsMixin):
    """ Store spreadsheet or a series of spreadsheets categorized with same titles and shape.
    """

    def __init__(self, datalist=[], filename=[]):
        self.data = datalist.copy()
        self.filename = filename.copy()

        self.name_convention = r'%F:%T'
        self.shape = (self.data[0].shape[0], self.data[0].shape[1], len(self.data)
        ) if len(self.data) > 0 else (0, 0, 0)

    def add_file(self, data, filename, do_copy=False):
        if len(self.data) > 0 and (self.data[0].shape != data.shape or (self.data[0].columns != data.columns).any()):
            raise ValueError("Data shape or column name does not match")

        if isinstance(data, pandas.DataFrame):
            self.data.append(data if not do_copy else data.copy())
        else:
            raise ValueError("Invalid data type: %s" % type(data))

        self.filename.append(filename)
        self.shape = (self.data[0].shape[0], self.data[0].shape[1], self.shape[2]+1)

    def add_sheet(self, other):
        if not isinstance(other, SheetFile):
            raise ValueError("Invalid data type: %s" % type(other))
        if len(other.data) == 0:
            return
        else:
            for d, f in zip(other.data, other.filename):
                self.add_file(d, f, True)
        
    def reload(self, keep_shape=True):
        """ Reload files according to recorded filename.
        If `keep_shape` is set, force the new shape to be matched.
        """
        new_sheet = load_file(*self.filename, False)
        if keep_shape and new_sheet.shape != self.shape:
            raise ValueError("Data shape does not match")
        self.data = new_sheet.data
        self.filename = new_sheet.filename
        self.shape = new_sheet.shape

    def cols(self):
        return self.data.shape[1]

    def __getitem__(self, idx):
        """ Indexing column by string, integer or slice.
        Notice the index starts from 1. Set idx = 0 would result
        np.arange(0, number_of_rows)

        For programming, please use `get()`.
        """
        if isinstance(idx, str):
            return self.get_column_by_label(idx)
        elif isinstance(idx, int):
            if idx == 0:
                return self.get_sequence()
            else:
                return self.get_column(idx-1)
        elif isinstance(idx, slice):
            newidx = idx
            if isinstance(newidx.start, int): newidx.start -= 1
            if isinstance(newidx.stop, int): newidx.stop -= 1
            if isinstance(newidx.step, int): newidx.step -= 1
            return self.get_column(newidx)
        elif isinstance(idx, tuple):
            return self.to_numpy()[idx]
        else:
            raise RuntimeError('Invalid indexing type: "%s"' % type(idx))

    def get(self, idx):
        """ Get column by using both string and integer.
        """
        if isinstance(idx, str):
            return self.get_column_by_label(idx)
        elif isinstance(idx, (int, slice, range)):
            return self.get_column(idx)
        else:
            raise RuntimeError('Invalid indexing type: "%s"' % type(idx))        

    def get_label(self, idx:int):
        """ index => label
        """
        try:
            return self.data[0].columns[idx]
        except IndexError:
            raise IndexError('Index is out of bounds')

    def get_column(self, idx):
        """ Get column by index (int/slice)
        """
        m_union = []
        for d in self.data:
            try:
                m_union.append(pandas.DataFrame(d.iloc[:,idx]))
            except IndexError:
                raise IndexError('Index is out of bounds')
        return SheetFile(m_union, self.filename)

    def get_column_by_label(self, label:str):
        """ Get column by str
        """
        m_union = []
        for d in self.data:
            try:
                m_union.append(pandas.DataFrame(d[label]))
            except KeyError:
                raise KeyError(label)
        return SheetFile(m_union, self.filename)

    def get_index_by_label(self, label):
        try:
            return self.data[0].columns.get_loc(label)
        except KeyError:
            raise KeyError(label)

    def get_sequence(self):
        return np.arange(self.data[0].shape[0])

    def has_label(self, label):
        return label in self.data[0].columns

    def columns(self):
        return self.data[0].columns

    def copy(self):
        return SheetFile([d.copy() for d in self.data], self.filename.copy())

    def flatten(self):
        if len(self.data) == 1:
            return self

        new_data = []
        for d, fn in zip(self.data, self.filename):
            new_columns = []
            new_data_ = d.copy()
            for i in range(d.shape[1]):
                new_columns.append(self.name_convention.replace(r'%T',d.columns[i]).replace(r'%F',fn))
            new_data_.columns = new_columns
            new_data.append(new_data_.copy())
        return SheetFile([pandas.concat(new_data, axis=1)], [self.filename[0]])

    def stack(self, method='sum-'):
        # TODO implement stack
        pass

    def to_numpy(self):
        return np.dstack((d.values for d in self.data)) if len(self.data) > 1 else self.data[0].values

    def __repr__(self):
        return 'SheetFile(%s)' % ','.join(('sheet%d%s:%s' % (idx, self.data[idx].shape, self.filename[idx]) for idx in range(len(self.data))))

    def __array__(self):
        return self.to_numpy()

    def __array_ufunc__(self, ufunc, method, *inputs, **kwargs):

        if method == 'reduceat':
            return NotImplemented

        if 'out' in kwargs:
            return NotImplemented

        if ufunc.nin == 1:
            ret = SheetFile([ufunc(d, **kwargs) for d in inputs[0].data], inputs[0].filename)

        elif ufunc.nin == 2 and (isinstance(inputs[0], (int, float)) or isinstance(inputs[1], (int, float))):
            if isinstance(inputs[0], (int, float)):
                ret = SheetFile([ufunc(inputs[0], d) for d in inputs[1].data], inputs[1].filename)
            elif isinstance(inputs[1], (int, float)):
                ret = SheetFile([ufunc(d, inputs[1]) for d in inputs[0].data], inputs[0].filename)

        elif ufunc.nin == 2 and (isinstance(inputs[0], SheetFile) and isinstance(inputs[1], SheetFile)
            and inputs[0].filename == inputs[1].filename):
            assert inputs[1].shape == inputs[0].shape
            ret = SheetFile([ufunc(a, b) for a, b in zip(inputs[0].data, inputs[1].data)], inputs[0].filename)

        else:
            m_inputs = []
            for i in inputs:
                m_inputs.append(i.to_numpy() if isinstance(i, SheetFile) else i)

            return getattr(ufunc, method)(*m_inputs, **kwargs)

        # rename columns
        for d in ret.data:
            if len(d.columns) == 1:
                d.columns = ('<expr>',)
            else:
                d.columns = ['<expr:%d>' % i for i in range(len(d.columns))]

        return ret


def load_file(*filenames, allow_wildcard=True, **kwargs):
    
    filenames_full = []
    for filename in filenames:
        if allow_wildcard and ('*' in filename or '?' in filename):
            import fnmatch
            path, fn = os.path.split(filename)
            if path == '':
                path = '.'
            flist = [os.path.join(path, f) for f in os.listdir(path)]
            m_filenames = fnmatch.filter([f for f in flist if os.path.isfile(f)], os.path.join(path, fn))
            if not m_filenames:
                warnings.warn('Wildcard "%s" does not match any file' % filename)
            filenames_full += m_filenames
        else:
            filenames_full.append(filename)

    sf = SheetFile()
    for fn in filenames_full:
        sf.add_file(load_dataframe(fn, **kwargs), fn)
    return sf


def load_single_file(filename, **kwargs):

    return SheetFile([load_dataframe(filename, **kwargs)], [filename])
    

def load_dataframe(filename, data_title='auto', data_delimiter='auto', ignore_data_comment=True, na_filter=True):
    """ Load file as `pandas.DataFrame` instance.
    """

    f = open(filename, 'r')
    data_info = sniff(f)
    if data_title != 'auto':
        data_info['title'] = data_title
    if data_delimiter == 'white':
        data_info['delimiter'] = r'\s+'
    elif data_delimiter != 'auto':
        data_info['delimiter'] = data_delimiter
    if ignore_data_comment == False:
        data_info['comment'] = None
    elif ignore_data_comment == 'smart':
        data_info['comment'] = 'smart'
    else:
        data_info['comment'] = True

    if data_info['comment'] == 'smart':
        m_f = io.StringIO()
        line = f.readline()
        while line:
            q = line.find('#')
            if q != -1:
                line = line[:q]
                if len(line) == 0 or line.isspace():
                    pass
                else:
                    m_f.write(line[:q])
                    m_f.write('\n')
            else:
                m_f.write(line)
                m_f.write('\n')
            line = f.readline()
        data_info['comment'] = None
    else:
        m_f = f

    logger.debug(data_info)
    return pandas.read_csv(m_f,
        sep=data_info['delimiter'],
        header=0 if data_info['title'] else None,
        index_col=False,
        skip_blank_lines=True,
        skipinitialspace=True,
        comment='#' if data_info['comment'] else None,
        na_filter=na_filter,
    )


def sniff(f, default_delimiter=r'\s+', ignore_comment=True):
    """ Different from csv.Sniffer -- this is for numerical data.
    The only allowed delimiters are , tab and space.
    """

    lines = []
    data_info = {}

    line = f.readline()

    while line and len(lines) < SNIFF_NUM:
        if ignore_comment and line.startswith('#'):
            pass
        elif ignore_comment and '#' in line:
            line = line[:line.index('#')]
            if not line.isspace():
                lines.append(line)
            else:
                data_info['comment'] = 'smart'
        elif len(line) == 0 or line.isspace():
            pass
        else:
            lines.append(line)
        
        line = f.readline()


    sample = ''.join(lines)
    spaces = re.findall(r'\s+', sample)
    commas = re.findall(r',', sample)

    if len(spaces) == 0 and len(commas) == 0:   # ... a bad guess is better than nothing?
        data_info['delimiter'] = default_delimiter
        try:
            float(lines[0])
        except ValueError:
            data_info['title'] = True
        else:
            data_info['title'] = False
        return data_info

    if len(spaces) > len(commas):

        # check tab or single space
        whites_by_line = [re.findall(r'\s+', line) for line in lines]
        
        single_tab_num = [len(list(filter(lambda x:x=='\t', wl))) for wl in whites_by_line]
        is_sep_tab = True
        for i in range(len(whites_by_line)):
            if single_tab_num[i] == 0:
                is_sep_tab = False
                break
            elif single_tab_num[i] < len(whites_by_line[i]) / 2:
                is_sep_tab = False
                break
            elif i < len(whites_by_line)-1 and single_tab_num[i] != single_tab_num[i+1]:
                is_sep_tab = False
                break

        if is_sep_tab:
            sep = '\t'
        else:
            sep = ' '

        # if most separators has more than one whites then treat as white
        if len([s for s in spaces if len(s) > 0]) > 0:
            sep = r'\s+'
    else:
        sep = ','

    data_info['delimiter'] = sep
    
    try:
        for s in re.split(sep, lines[0].strip()):
            float(s)
    except ValueError:
        data_info['title'] = True
    else:
        data_info['title'] = False

    f.seek(0)
    return data_info

# Universal operations on SheetFile, DataFrame and np.array

def save_file(mat, path):
    """ Save the matrix into file.
    if mat is pandas.DataFrame, use pandas save function;
    if mat is SheetFile, use pandas save function, and will be 
        flatten if there are multiple sheets;
    if mat is array-like, use np.savetxt().
    """
    if isinstance(mat, pandas.DataFrame):
        mat.to_csv(path, sep='\t', index=False)
    elif isinstance(mat, SheetFile):
        if len(mat.data) > 1:
            mat2 = mat.copy()
            mat2.flatten()
            mat2.data[0].to_csv(path, sep='\t', index=False)
        else:
            mat.data[0].to_csv(path, sep='\t', index=False)
    else:
        np.savetxt(path, mat, fmt='%18g', delimiter='\t')


def loc_col(mat, colidx):
    """ Locate column by index (starting from 0)
    """
    if isinstance(mat, pandas.DataFrame):
        return pandas.DataFrame(mat.iloc[:, colidx])
    else:
        return mat[:, colidx]

def loc_col_str(mat, colname):
    """ Locate column by string (starting from 1)
    """
    colidx = int(colname)-1 if colname.isdigit() else None

    if colidx == -1:
        return np.arange(mat.shape[0])

    if isinstance(mat, pandas.DataFrame):
        if colidx is None:
            return mat.loc[:, colname].to_numpy()
        else:
            return mat.iloc[:, colidx].to_numpy()
    elif isinstance(mat, SheetFile):
        return mat[colname if colidx is None else colidx+1]
    else:
        if colidx is None:
            raise ValueError('Expect integer index for array, got "%s"' % colname)
        else:
            return mat[:, colidx]


def columns(mat, title_sub='%d'):
    """ Get column titles.
    Return title_sub % (integer) sequences (start from 1) for arrays.
    """
    
    if isinstance(mat, pandas.DataFrame):
        return _make_cols(mat.columns, title_sub)
    elif isinstance(mat, SheetFile):
        return _make_cols(mat.columns(), title_sub)
    elif title_sub is not None:
        return _make_cols(list(range(cols(mat))), '%d')
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

def dimension(mat):
    return len(mat.shape)

def flatten(mat):
    return np.array(mat).flatten()
    
def histogram(mat, bins=10, norm='pdf'):

    h, e = np.histogram(np.array(mat).flatten(), bins, density=False)
    if norm in ('Density', 'density', 'PDF', 'pdf', 'Distribution', 'distribution'):
        h = h / np.sum(h) / (e[1]-e[0])
    elif norm in ('Probability', 'probability', 'Prob', 'prob'):
        h = h / np.sum(h)

    e = e[1:] + (e[1]-e[0])/2
    return np.hstack((e[:, None], h[:, None]))


import csv
import re
import logging
import pandas
import numpy as np

logger = logging.getLogger('line')

class SheetFile:
    
    COLUMN_MATCHER = re.compile(r'(?P<a>\$\d+)|(?P<b>\$\D\w*)|(?P<c>col\([^\)]+\))')
    SNIFF_NUM = 5   # number of lines used in sniff

    def __init__(self):
        self.data = None
        self.filename = None

        self._used_indices = []
        self._replaced_str = []

    def cols(self):
        return self.data.shape[1]

    def load(self, filename, data_title='auto', data_delimer='auto', ignore_data_comment=True):
        """ Load spreadsheet file.
        Options:
            data_title: Does the data has title. 'auto'/True/False.
            data_delimer: Delimiter of data. 'auto'/[char]
            ignore_data_comment: Ignore lines beginning with '#'.
        """
        try:
            f = open(filename, 'r')
        except IOError:
            return False
        self.filename = filename

        # pandas's python engine is slow, so I use a 'sample' to
        # detect basic information before actual reading

        data_info = self.sniff(f, ignore_data_comment)
        f.seek(0)

        # overwrite information
        if data_title != 'auto':
            data_info['title'] = data_title
        if data_delimer != 'auto':
            data_info['delimiter'] = data_delimer
        
        if data_info['delimiter'] == 'white':
            data_info['delimiter'] = r'\s+'

        print(data_info)
        self.data = pandas.read_csv(f,
            sep=data_info['delimiter'],
            header=data_info['first_row'] if data_info['title'] else None,
            index_col=False,
            skiprows=data_info['add_blank_rows'],
            skip_blank_lines=True,
            skipinitialspace=data_info['initial_space']>0,
            comment='#' if ignore_data_comment else None
            )

        if not data_info['title']:
            self.data.rename(dict((str(i), i) for i in range(self.cols())))

        return True


    def sniff(self, f, ignore_data_comment=True):
        lines = []
        data_info = {}

        line = f.readline()
        rowcount = 0 
        add_blank_rows = [] # additional blank rows by comment

        while line and len(lines) < SheetFile.SNIFF_NUM:
            if ignore_data_comment:
                if line.startswith('#'):
                    rowcount += 1
                elif '#' in line and line[:line.index('#')].isspace():
                    add_blank_rows.append(rowcount)
                    rowcount += 1
                elif len(line) == 0 or line.isspace():
                    add_blank_rows.append(rowcount)
                else:
                    lines.append(line)
                    if len(lines) == 1:
                        data_info['first_row'] = rowcount
            else:
                if len(line) == 0 or line.isspace():
                    add_blank_rows.append(rowcount)
                    rowcount += 1
                else:
                    lines.append(line)
                    data_info['first_row'] = rowcount
            line = f.readline()

        data_info['add_blank_rows'] = add_blank_rows

        s = csv.Sniffer()
        s.preferred = ['\t',' ',',',';',':']

        sample = ''.join(lines)
        
        
        try:
            dialect = s.sniff(sample)
        except csv.Error:   # sample too small, using alternative detector

            spaces = re.findall(r'\s+', sample)
            commas = re.findall(r',', sample)

            if len(spaces) == 0 and len(commas) == 0:   # ... a bad guess is better than nothing?
                data_info['delimiter'] = '\t'
                data_info['initial_space'] = False
                try:
                    float(lines[0])
                except ValueError:
                    data_info['title'] = True
                else:
                    data_info['title'] = False
                return data_info

            if len(spaces) > len(commas):
                sep = spaces[0][0]
                if len([s for s in spaces if len(s) > 0]) > 0:  # if most separators has more than one whites then treat as white
                    sep = 'white'
            else:
                sep = ','

            data_info['delimiter'] = sep
            m = re.match(r'\s+', lines[-1])
            data_info['initial_space'] = m.span()[1] if m else 0

            try:
                if sep != 'white':
                    float(lines[0].strip().split(sep)[0])
                else:
                    float(re.split(r'\s+', lines[0].strip())[0])
            except ValueError:
                data_info['title'] = True
            else:
                data_info['title'] = False
        else:
            data_info['title'] = s.has_header(sample)
            if not data_info['title']:
                if re.match(r'[a-zA-Z_]', lines[0]):
                    data_info['title'] = True   # anything not number is regarded as title.
            data_info['delimiter'] = dialect.delimiter
            data_info['initial_space'] = dialect.skipinitialspace

        return data_info

    def __getitem__(self, idx):
        return self.data.iloc[:,idx]

    def get_label(self, idx):
        try:
            return self.data.columns[idx]
        except IndexError:
            raise IndexError('Index is out of bounds')

    def get_column(self, idx):
        try:
            return self.data.iloc[:,idx]
        except IndexError:
            raise IndexError('Index is out of bounds')

    def get_column_by_label(self, label):
        try:
            return self.data.loc[:,label]
        except KeyError:
            raise KeyError(label)        

    def get_index_by_label(self, label):
        try:
            self.data.columns.get_loc[label]
        except KeyError:
            raise KeyError(label)

    def get_sequence(self):
        return np.arange(self.data.shape[0])

    def has_label(self, label):
        return label in self.data.columns

    def eval_column_expr(self, col_expr):

        # fast return
        if not col_expr[0] in '$(':
            try:
                idx = int(col_expr)
            except ValueError:
                return self.get_column_by_label(col_expr)
            else:
                return self.get_column(idx-1)
                

        elif col_expr[0] == '(':
            col_expr = col_expr[1:-1]   # removing bracket
        
        self._used_indices.clear()
        col_expr = self.COLUMN_MATCHER.sub(lambda m:self._replace_column(m), col_expr)
        
        arg_table = dict((('column%d' % (i+1), self.get_column(i)) for i in self._used_indices))
        arg_table['column0'] = self.get_sequence()

        arg_table.update({
            'sin':np.sin,
            'cos':np.cos,
            'tan':np.tan,
            'cumsum':np.cumsum,
            'exp':np.exp,
            'log':np.log,
            'sinh':np.sinh,
            'cosh':np.cosh,
            'tanh':np.tanh,
            'sqrt':np.sqrt,
            'abs':np.abs,
            'min':np.minimum,
            'max':np.maximum
        })

        logger.debug('Column expression: %s' % col_expr)

        return eval(col_expr, arg_table)

    def _replace_column(self, match):
        if match.group('a'):    # integer
            idx = int(match.group('a')[1:])
            if idx != 0:
                self._replaced_str.append(match.group('a')[1:])
                self._used_indices.append(idx-1)
            elif idx-1 >= self.cols():
                raise IndexError('Index out of bounds: %d' % idx)

            return 'column%d' % idx
        elif match.group('b'):
            idx = self.get_index_by_label(match.group('b')[1:])
            self._replaced_str.append(match.group('b')[1:])
            self._used_indices.append(idx)
            return 'column%d' % (idx+1)
        elif match.group('c'):
            idx = self.get_index_by_label(match.group('c')[4:-1])
            self._replaced_str.append(match.group('c')[4:-1])
            self._used_indices.append(idx)
            return 'column%d' % (idx+1)


def load_file(filename, data_title='auto', data_delimer='white', ignore_data_comment=True) -> SheetFile:
    sheet_file = SheetFile()
    if not sheet_file.load(filename, data_title, data_delimer, ignore_data_comment):
        return None
    else:
        return sheet_file

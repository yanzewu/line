
import csv
import re
import logging
import pandas
import numpy as np

logger = logging.getLogger('line')

class SheetFile:
    
    COLUMN_MATCHER = re.compile(r'(?P<a>\$\d+)|(?P<b>\$\D\w*)|(?P<c>col\([^\)]+\))')

    def __init__(self):
        self.data = None

        self._used_indices = []

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
            data_info['delimiter'] = '\s+'

        self.data = pandas.read_csv(f,
            sep=data_info['delimiter'],
            header=0 if data_info['title'] else None,
            index_col=False,
            skipinitialspace=data_info['initial_space'],
            comment='#' if ignore_data_comment else None
            )

        if not data_info['title']:
            self.data.rename(dict((str(i), i) for i in range(self.cols())))

        return True


    def sniff(self, f, ignore_data_comment=True):
        
        lines = []

        line = f.readline()
        while line and len(lines) < 5:
            if not ignore_data_comment or not line.strip().startswith('#'):
                lines.append(line)
            line = f.readline()

        s = csv.Sniffer()
        s.preferred = ['\t',' ',',',';',':']

        sample = ''.join(lines)
        data_info = {}
        
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
            else:
                sep = ','
            dialect = s.sniff(sample, sep)
            try:
                float(lines[0].strip().split(sep)[0])
            except ValueError:
                data_info['title'] = True
            else:
                data_info['title'] = False
        else:
            data_info['title'] = s.has_header(sample)

        data_info['delimiter'] = dialect.delimiter
        data_info['initial_space'] = dialect.skipinitialspace

        return data_info

    def __getitem__(self, idx):
        return self.data.iloc[:,idx]

    def get_label(self, idx):
        return self.data.columns[idx]

    def get_column(self, idx):
        return self.data.iloc[:,idx]

    def get_sequence(self):
        return np.arange(self.data.shape[0])

    def eval_column_expr(self, col_expr):
        if not col_expr[0] in '$(':
            try:
                idx = int(col_expr)
            except ValueError:
                return self.data.loc[:, col_expr]
            else:
                return self.data.iloc[:, idx-1]
        elif col_expr[0] == '(':
            col_expr = col_expr[1:-1]   # removing bracket
        
        self._used_indices.clear()
        col_expr = self.COLUMN_MATCHER.sub(lambda m:self._replace_column(m), col_expr)
        try:
            arg_table = dict((('column%d' % (i+1), self.get_column(i)) for i in self._used_indices))
        except IndexError as e:
            print(e)
            return None
        else:
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
            if idx > 0:
                self._used_indices.append(idx-1)
            return 'column%d' % idx
        elif match.group('b'):
            idx = self.data.columns.get_loc(match.group('b')[1:])
            self._used_indices.append(idx)
            return 'column%d' % (idx+1)
        elif match.group('c'):
            idx = self.data.columns.get_loc(match.group('c')[4:-1])
            self._used_indices.append(idx)
            return 'column%d' % (idx+1)


def load_file(filename, data_title='auto', data_delimer='white', ignore_data_comment=True) -> SheetFile:
    sheet_file = SheetFile()
    if not sheet_file.load(filename, data_title, data_delimer, ignore_data_comment):
        return None
    else:
        return sheet_file

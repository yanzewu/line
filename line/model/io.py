import csv
import re
import io
import os.path
import fnmatch
import logging
import pandas
import numpy as np
import warnings

from . import sheet

logger = logging.getLogger('line')


def load_file(*filenames, allow_wildcard=True, mode='auto', **kwargs):
    """ Load multiple files from filename list.
    Args:
        allow_wildcard: Match files by wildcard (currently only support same directory).
        mode: 
            'single': Load the first (matched) file and generate `SourceableSheet';
            'multiple': Always generate `SheetCollection';
            'auto': Determine type by number of files;

    Additional args is passed to `load_single_file'.
    """

    filenames_full = []
    for filename in filenames:
        if allow_wildcard and ('*' in filename or '?' in filename):
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

    if not filenames_full:
        raise IOError("No file is matched")

    if mode == 'single' or (mode == 'auto' and len(filenames_full) == 1):
        return load_single_file(filenames_full[0], **kwargs)
    elif mode == 'multiple' or (mode == 'auto' and len(filenames_full) > 1):
        return sheet.SheetCollection([
            load_single_file(fn, **kwargs) for fn in filenames_full])
    else:
        raise ValueError(mode)


def load_single_file(filename, **kwargs):
    """ Load file as `SourceableSheet` instance.
    """
    return sheet.SourceableSheet(load_dataframe(filename, **kwargs), source=filename)
    

def load_dataframe(filename, data_title='auto', data_delimiter='auto', ignore_data_comment=True, na_filter=True, sniff_num=5):
    """ Load file as `pandas.DataFrame` instance.
    """

    f = open(filename, 'r')
    data_info = sniff(f, sniff_num=sniff_num)
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


def sniff(f, default_delimiter=r'\s+', ignore_comment=True, sniff_num=5):
    """ Different from csv.Sniffer -- this is for numerical data.
    The only allowed delimiters are , tab and space.
    """

    lines = []
    data_info = {}

    line = f.readline()

    while line and len(lines) < sniff_num:
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


def save_file(mat, path, delimiter='\t', format_='%18g'):
    """ Save the matrix into file.
    if mat is pandas.DataFrame or SourceableSheet, use pandas save function;
    Otherwise invokes use np.savetxt().
    """
    if isinstance(mat, pandas.DataFrame):
        mat.to_csv(path, sep=delimiter, float_format=format_, index=False)
    elif isinstance(mat, sheet.SourceableSheet):
        mat.data.to_csv(path, sep=delimiter, float_format=format_, index=False)
    else:
        np.savetxt(path, mat, fmt=format_, delimiter=delimiter)



import os
import glob
import re
from functools import cmp_to_key


def file_exist(filename):
    """ Check if a regular file exists.
    """
    return os.path.exists(filename) #and os.path.isfile(filename)
    
def dir_exist(filename):

    return os.path.exists(filename) and os.path.isdir(filename)
    
def file_or_wildcard_exist(filename):
    
    return '*' in filename or '?' in filename or file_exist(filename)


def query_cond(question, cond, default, set_true=True):
    """ If cond is True, ask question and get answer, otherwise use default.
    if `set_ture`, automatically convert positive answer to True, and other False.
    """
    if cond:
        answer = input(question)
        if set_true:
            answer = answer in ('y', 'Y', 'yes', 'Yes')
        return answer
    else:
        return default


def expand(filename, sort=True):
    """ If `sort` is `True`, compare two string by
    (1) extract the common part (PREFIX)
    (2) if the next part starts with a number (include one '.'), compare
        that number. Otherwise compare as normal string.
    """
    matched = glob.glob(filename, recursive=True)
    if sort:
        matched = sorted(matched, key=cmp_to_key(_cmp_numerical))
    if os.name == "nt":
        return [m.replace('\\', '/') for m in matched]
    else:
        return matched


def _cmp_numerical(s1, s2):
    
    i = 0
    j = 0
    while i < len(s1) and j < len(s2):
        if s1[i].isdigit() and s2[j].isdigit():
            a = re.match(r'\d+(\.\d+)?', s1[i:]).group(0)
            b = re.match(r'\d+(\.\d+)?', s2[j:]).group(0)
            try:
                fa = float(a)
                fb = float(b)
            except ValueError:
                break
            if fa == fb:
                i += len(a)
                j += len(b)
            else:
                return (fa > fb) - (fa < fb)

        elif s1[i] == s2[j]:
            i += 1
            j += 1
        else:
            break

    return (s1 > s2) - (s1 < s2)


def _test_cmp_numerical():
    
    assert _cmp_numerical('123', '456') == -1
    assert _cmp_numerical('abc', 'def') == -1
    assert _cmp_numerical('abc.123', 'd.456') == -1
    assert _cmp_numerical('abc.123', 'abc.45') == 1
    assert _cmp_numerical('abc12', 'abc3') == 1
    assert _cmp_numerical('abc12', 'abc3.4') == 1
    assert _cmp_numerical('abc3.4.4', 'abc3.4.5') == -1
    assert _cmp_numerical('abc.3.5.4', 'abc.3.4.5') == 1
    assert _cmp_numerical('', '') == 0
    assert _cmp_numerical('abc-3.4-5.6', 'abc-3.4-5.6') == 0
    assert _cmp_numerical('abc-3.4-5.6', 'abc-3.4-5.5.4') == 1
    assert _cmp_numerical('abc-3.4-5.6aaa', 'abc-3.4-5.5.4zzz') == 1

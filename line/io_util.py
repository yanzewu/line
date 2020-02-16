
import os

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


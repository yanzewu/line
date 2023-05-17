""" Utilities of option parsing and string conversion.
"""

def to_bool(token:str):
    try:
        return {'true':True, 'false':False}[token.lower()]
    except KeyError:
        raise ValueError(token)


def parse_range(token:str):
    """ Parse the range start:step:stop / start:stop into tuple (start, stop, step)
    """
    ssplit = token.split(':')
    start = float(ssplit[0]) if ssplit[0] else None
    if len(ssplit) == 3:
        step = float(ssplit[1]) if ssplit[1] else None
    else:
        step = None
    stop = float(ssplit[-1]) if ssplit[-1] else None

    return start, stop, step


def parse_general(token:str):
    """ Parse string into one of int,float,bool,None,str,list,range.
    """
    if ',' in token:
        return [parse_general(t) for t in token.split(',')]
    elif ':' in token:
        return parse_range(token)

    else:
        return parse_token(token)

def parse_token(token:str):
    """ Parse string into one of int,float,bool,None,str.
    """
    try:
        return to_bool(token)
    except ValueError:
        pass
    if token.lower() == 'none':
        return None
    
    if '.' in token or 'e' in token:
        try:
            return float(token)
        except ValueError:
            return token
    try:
        return int(token)
    except ValueError:
        return token


def parse_option(opt, raw_arg, option_range=None, default_handler=parse_general, custom_handler_dict={}, strict=False):
    """ Parse raw_arg => arg.
    Args:
        opt, raw_arg: option name and string value of option.
        option_range: Container that holds the valid options, if `None' then all options are consider valid.
        default_handler: Default parser for option, will be called as f(arg).
        custom_handler_dict: Custom handlers, key is option. Will be called as d[opt](arg).
        strict: If `True' then raise `KeyError` if opt not in `option_range'.
    Returns:
        The value parsed.
    """
    
    if option_range is not None and strict and opt not in option_range:
        raise KeyError(opt)

    if opt in custom_handler_dict:
        return custom_handler_dict[opt](raw_arg)
    else:
        return default_handler(raw_arg)


def parse_option_list(option_list, option_range=None, default_handler=parse_general, custom_handler_dict={}, strict=False, omit_when_valueerror=False):
    """ Parse a list of tuple (opt, arg) => dict of {opt:arg}.
    Args:
        option_list: dict/list of tuple (opt, arg).
        option_range: Container that holds the valid options, if `None' then all options are consider valid. Only
            options in option_range will be returned.
        default_handler: Default parser for option, will be called as f(arg).
        custom_handler_dict: Custom handlers, key is option. Will be called as d[opt](arg).
        strict: If `True' then raise `KeyError` if option not in `option_range'.
        omit_when_valueerror:  If `True' then all ValueError will be ignored (but the argument will also be omitted).
    Returns:
        dict(opt=arg)
    """

    ret = {}
    for opt, arg in (option_list if not isinstance(option_list, dict) else option_list.items()):
        if option_range is not None and opt not in option_range and not strict:
            continue
        try:
            ret[opt] = parse_option(opt, arg, 
                option_range=option_range, 
                default_handler=default_handler, 
                custom_handler_dict=custom_handler_dict,
                strict=strict)
        except ValueError:
            if not omit_when_valueerror:
                raise

    return ret
            
def get_options(arg_list:list, handler=parse_general, group_repeated:bool=False) -> dict:
    """ Parse a unix-style argument list => dict of {opt:arg}
    Example:
        get_options("-a 1 --b 2 3 4".split()) => {'a':1, 'b':2, None:[3, 4]}
    Args:
        arg_list: Iterable of string. Option must begin with '-'/'--' followed by a letter (e.g. "-2"
            is treated as a number rather than an option). Both '-' and '--' are treated as same options.
        handler: function to parse the string; If None then just return the string.
        group_repeated: If one option appears multiple times, the args will be grouped as a list.
    Returns:
        dict(opt=arg). The entry `None` stores all the positional args, and is always guaranteed to be a list.
    """
    if handler is None:
        handler = lambda x:x

    ret = {None:[]}
    current_option = None

    def appending_option(opt, v):
        if opt in ret:
            if group_repeated or opt is None:
                if isinstance(ret[opt], list):
                    ret[opt].append(v)
                else:
                    ret[opt] = [ret[opt], v]
            else:
                ret[opt] = v
        else:
            if group_repeated:
                ret[opt] = [v]
            else:
                ret[opt] = v

    for a in arg_list:
        if isinstance(a, str) and a.startswith('--') and (len(a) < 3 or a[2].isalpha()):
            if current_option:
                appending_option(current_option, True)
            current_option = a[2:]
        elif isinstance(a, str) and a.startswith('-') and (len(a) < 2 or a[1].isalpha()):
            if current_option:
                appending_option(current_option, True)
            current_option = a[1:]
        else:
            v = handler(a) if isinstance(a, str) else a
            appending_option(current_option, v)
            current_option = None

    return ret

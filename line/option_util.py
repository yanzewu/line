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
    """ Parse general token into python objects.
    """
    if ',' in token:
        return [parse_general(t) for t in token.split(',')]
    elif ':' in token:
        return parse_range(token)

    else:
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
            

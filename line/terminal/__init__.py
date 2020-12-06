
# Check IPython and prompt_toolkit

import importlib

from .. import defaults

legacy_shell = True
if defaults.default_options['fancy-prompt'] and \
    importlib.util.find_spec('IPython') and importlib.util.find_spec('prompt_toolkit'):   # we cannot import them now, cause it will be slow
    import prompt_toolkit as pt
    if pt.VERSION[0] >= '3':    # we need pt3
        legacy_shell = False


__all__ = ['CMDHandler', 'query_cond', 'completion_util']

if legacy_shell:
    from .cmd_handle import CMDHandler, query_cond
else:
    from .shell import CMDHandler, query_cond

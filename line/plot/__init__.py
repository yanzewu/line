
from .. import state
from .. import style
from .. import defaults

backend = 'mpl'
backend_module = None

def initialize(m_state:state.GlobalState, *args, **kwargs):
    
    global backend_module

    if backend_module is not None:
        backend_module.initialize(m_state, *args, **kwargs)
        return

    m = None

    if backend == 'mpl':
        from . import mpl
        m = mpl

    if m is None:
        raise RuntimeError('Backend "%s" not found' % backend)
    else:
        import sys

        myself = sys.modules[__name__]
        m.initialize(m_state, *args, **kwargs)
        setattr(myself, 'finalize', m.finalize)
        setattr(myself, 'update_figure', m.update_figure)
        setattr(myself, 'update_subfigure', m.update_subfigure)
        setattr(myself, 'save_figure', m.save_figure)
        setattr(myself, 'update_focus_figure', m.update_focus_figure)
        setattr(myself, 'close_figure', m.close_figure)
        setattr(myself, 'show', m.show)

        backend_module = m
        
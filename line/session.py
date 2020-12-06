
from . import state
from . import vm
from . import defaults


_instance = None

def has_instance():
    return _instance is not None


def get_instance(debug=False):
    global _instance
    if _instance is None:
        _instance = Session(debug=debug)
    return _instance

def instance():
    return _instance


def get_vm():
    return instance().vm


def get_state():
    return instance().state


def is_interactive():
    return instance().state.is_interactive


class Session:

    def __init__(self, debug=False):

        self.state = state.GlobalState()
        self.vm = vm.VMHost(debug=debug)
        self.state._vmhost = self.vm

        defaults.init_global_state(self.state)




from . import state
from . import vm
from . import defaults
from . import history


_instance = None

def has_instance() -> bool:
    return _instance is not None


def get_instance(debug=False, enable_history=False):
    global _instance
    if _instance is None:
        _instance = Session(debug=debug, enable_history=enable_history)
    return _instance

def instance():
    return _instance


def get_vm() -> vm.VMHost:
    return instance().vm


def get_state() -> state.GlobalState:
    return instance().state


def get_history():
    return instance().history


def is_interactive() -> bool:
    return instance().state.is_interactive


class ShellState:

    def __init__(self, filename:str, interactive:bool):
        self.filename = filename
        self.interactive = interactive
        self.handler = None

class Session:

    def __init__(self, debug=False, enable_history=True):

        self.state = state.GlobalState()
        self.vm = vm.VMHost(debug=debug)
        self.state._vmhost = self.vm
        self.history = history.HistoryManager() if enable_history else history.DummyHistoryManager()
        self.state._history = self.history
        self.shell_state = []

        defaults.init_global_state(self.state)

    def push_shell(self, filename:str, interactive:bool):
        self.shell_state.append(ShellState(filename, interactive))

    def pop_shell(self):
        self.shell_state.pop()

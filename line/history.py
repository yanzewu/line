# NOTE this is for undo/redo functionality. Not command history.

import copy

from numpy.lib.arraysetops import isin

from . import state
from .errors import LineProcessError
from .element import figobject

class StateSnapshot:
    """ Snapshot of the overall state, excluding elements.
    """
    def __init__(self, m_state:state.GlobalState):
        self.typename = 'state'
        self.custom_stylesheet = copy.deepcopy(m_state.custom_stylesheet)

    def apply_to(self, m_state:state.GlobalState):
        m_state.custom_stylesheet = copy.deepcopy(self.custom_stylesheet)


class StyleSnapshot:
    """ Snapshot of element styles.
    """
    def __init__(self, node:figobject.FigObject):
        self.typename = 'style'
        self.name = node.name
        self.classnames = node.classnames.copy()
        self.style = copy.deepcopy(node.style)
        self.computed_style = copy.deepcopy(node.computed_style)
        self.children = dict([(c.name, StyleSnapshot(c)) for c in node.get_children()])

    def apply_to(self, node:figobject.FigObject):
        node.classnames = self.classnames.copy()
        node.style = copy.deepcopy(self.style)
        old_style = node.computed_style
        node.computed_style = copy.deepcopy(self.computed_style)
        if node.computed_style:
            node.on_style_updated(old_style, node.computed_style)
        for c in node.get_children():
            self.children[c.name].apply_to(c)


class ElementSnapshot:
    """ Snapshot of removable elements (usually children of a subfigure).
    """
    def __init__(self, figname, node, element_type):
        self.typename = 'element/' + element_type
        self.figname = figname
        self.nodename = node.name
        self.element_type = element_type
        self.elements = getattr(node, element_type).copy()
    
    def apply_to(self, node):
        setattr(node, self.element_type, self.elements.copy())


class UnionSnapshot:
    """ Just a storage of multiple snapshots.
    """
    def __init__(self, snapshots):
        self.typename = [s.typename for s in snapshots]
        self.snapshots = snapshots


class HistoryManager:

    def __init__(self, max_history=20):
        self.stack = []
        self.index = -1     # where the latest history *before current state* is pointing on
        self.stack_size = max_history
        self.snapshot_cache = None

    def undo(self, m_state:state.GlobalState):
        if self.index < 0 or len(self.stack) == 0:
            raise LineProcessError("No further history exists.")
        
        if self.index == len(self.stack) - 1:   # we are in the latest, keep a copy of current state (otherwise cannot redo)
            current_snapshot = self._take_snapshot(m_state, snapshot_type=self.stack[self.index].typename)
            self.stack.append(current_snapshot)
            if len(self.stack) > self.stack_size:
                self.stack.pop(0)
                self.index -= 1

        self._apply_snapshot(m_state, self.stack[self.index])
        self.index -= 1

    def redo(self, m_state:state.GlobalState):
        if self.index + 2 >= len(self.stack):
            raise LineProcessError("Already in the latest state.")

        self._apply_snapshot(m_state, self.stack[self.index + 2])
        self.index += 1

    def take_snapshot(self, m_state:state.GlobalState, snapshot_type='style'):
        """ Takes a snapshot of state.
        """
        self.cache_snapshot(m_state, snapshot_type)(True)

    def cache_snapshot(self, m_state:state.GlobalState, snapshot_type='style'):
        """ Returns a lambda that accept True (-> commit_snapshot) or False -> (forget_snapshot)
        """
        self.snapshot_cache = self._take_snapshot(m_state, snapshot_type)
        
        return lambda x:self.commit_snapshot() if x else self.clear_cache()

    def commit_snapshot(self):
        if not self.snapshot_cache:
            raise LineProcessError('No snapshot is waiting for commit')
        self.index += 1
        if self.index >= len(self.stack):
            self.stack.append(self.snapshot_cache)
        else:
            self.stack[self.index] = self.snapshot_cache

        if len(self.stack) > self.stack_size:
            self.stack.pop(0)
            self.index -= 1
        self.snapshot_cache = None

    def clear_cache(self):
        self.cache_snapshot = None

    def clear(self):
        self.stack.clear()
        self.index = -1
        
    def _apply_snapshot(self, m_state:state.GlobalState, snapshot):
        if isinstance(snapshot, StateSnapshot):
            snapshot.apply_to(m_state)
        elif isinstance(snapshot, StyleSnapshot):
            for fig in m_state.figures.values():
                if fig.name == snapshot.name:
                    snapshot.apply_to(fig)
                    fig.is_changed = True
                    break
        elif isinstance(snapshot, ElementSnapshot):
            for name, fig in m_state.figures.items():
                if name == snapshot.figname:
                    for subfig in fig.subfigures:
                        if subfig.name == snapshot.nodename:
                            snapshot.apply_to(subfig)
                            subfig.is_changed = True
                            return
        elif isinstance(snapshot, UnionSnapshot):
            for s in reversed(snapshot.snapshots):
                self._apply_snapshot(m_state, s)

    def _take_snapshot(self, m_state:state.GlobalState, snapshot_type):

        if isinstance(snapshot_type, (list, tuple)):
            return UnionSnapshot([self._take_snapshot(m_state, s) for s in snapshot_type])

        if snapshot_type == 'style':
            return StyleSnapshot(m_state.gcf())
        elif snapshot_type == 'state':
            return StateSnapshot(m_state)
        elif snapshot_type.startswith('element/'):
            return ElementSnapshot(m_state.cur_figurename, m_state.gca(), snapshot_type[8:])
        

class DummyHistoryManager:
    """ Used when we don't want history.
    """
    def __init__(self):
        pass        

    def undo(self, m_state):
        pass

    def redo(self, m_state):
        pass

    def take_snapshot(self, m_state, snapshot_type='style'):
        pass

    def cache_snapshot(self, m_state, snapshot_type='style'):
        return lambda x: None

    def clear(self):
        pass
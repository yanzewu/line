
import sys

from . import cmd_handle
from . import plot

if __name__ == '__main__':
    
    cmd_handler = cmd_handle.CMDHandler()
    cmd_handler.init_input()

    plot.initialize(True)
    ret = 0
    while ret == 0:
        ret = cmd_handler.proc_input()
    plot.finalize(True)
        
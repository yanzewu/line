
import sys

from . import cmd_handle
from . import plot

if __name__ == '__main__':
    
    cmd_handler = cmd_handle.CMDHandler()
    cmd_handler.init_input()
    cmd_handler.input_loop()
        
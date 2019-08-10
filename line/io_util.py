
import os

def file_exist(filename):
    return os.path.exists(filename) and os.path.isfile(filename)
    
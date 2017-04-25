#!/usr/bin/env python
# Add a relative path
import sys
import os
file_dir = os.path.dirname(os.path.realpath(__file__))
relative_path = "/.."
path = os.path.abspath(file_dir + relative_path)
sys.path.insert(0, path)

import importlib
import pdb


def main():
    dirs = os.walk('../')
    for d in dirs:
        dirname = d[0]
        if 'test' in dirname:
            execute_on_dir(dirname, d[2])

def execute_on_dir(dirname, filenames):
    for i in filenames:
        if check_py(i):
            import_str1 = dirname[3:].replace('/', '.') + '.' + i
            #import_str = import_str1.strip(".py")
            import_str = import_str1[:-3]
            #i = i[:-3]
            print 'importing:', import_str
            print len(import_str)
            importlib.import_module(import_str)

def check_py(filename):
    pyfile = ".py" in filename
    notpyc = ".pyc" not in filename
    notswp = ".swp" not in filename
    notinit = "__init__" not in filename
    return pyfile and notpyc and notinit and notswp

if __name__ == "__main__":
    main()

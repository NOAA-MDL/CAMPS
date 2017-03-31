#!/usr/bin/env python
# Add a relative path
import sys, os
file_dir = os.path.dirname(os.path.realpath(__file__))
relative_path = "/.."
path = os.path.abspath(file_dir + relative_path)
sys.path.insert(0, path)

import importlib

def main():
    dirs = os.walk('../')
    for d in dirs:
        dirname = d[0] 
        if 'test' in dirname:
            for i in d[2]:
                if ".py" in i:
                    import_str = dirname[3:].replace('/','.')+'.'+i
                    import_str = import_str.strip(".py")
                    print 'importing:', import_str
                    importlib.import_module(import_str)


if __name__ == "__main__":
    main()

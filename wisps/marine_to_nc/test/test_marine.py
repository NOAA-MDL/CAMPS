#!/usr/bin/env python
import sys
import os
file_dir = os.path.dirname(os.path.realpath(__file__))
relative_path = "/.."
path = os.path.abspath(file_dir + relative_path)
sys.path.insert(0, path)

import marinereader

print "Tested Marine"

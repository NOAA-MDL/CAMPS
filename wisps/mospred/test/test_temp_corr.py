#!/usr/bin/env python
import os
import sys
file_dir = os.path.dirname(os.path.realpath(__file__))
relative_path = '/..'
path = os.path.abspath(file_dir + relative_path)
sys.path.insert(0, path)
import temp_corr


def test_temp_corr_setup():
    """  """
    pass

def test_temp_corr():
    """  """
    pass




test_temp_corr_setup()
test_temp_corr()

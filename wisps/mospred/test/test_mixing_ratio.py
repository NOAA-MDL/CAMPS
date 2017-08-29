#!/usr/bin/env python
import os
import sys
file_dir = os.path.dirname(os.path.realpath(__file__))
relative_path = '/..'
path = os.path.abspath(file_dir + relative_path)
sys.path.insert(0, path)


def test_mixing_ratio_setup():
    """  """
    pass

def test_mixing_ratio():
    """  """
    pass



if __name__ == "__main__":

    test_mixing_ratio_setup()
    test_mixing_ratio()

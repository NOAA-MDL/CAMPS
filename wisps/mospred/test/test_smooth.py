#!/usr/bin/env python
import os
import sys
file_dir = os.path.dirname(os.path.realpath(__file__))
relative_path = '/..'
path = os.path.abspath(file_dir + relative_path)
sys.path.insert(0, path)
import smooth
import numpy as np


def test_smooth():
    """  """
    tst_arr = np.random.rand(10,20)
    tst_arr = tst_arr * 10

    smooth.smooth(tst_arr, '9')

    arr = np.array(
            [[1, 5, 5],
             [5, 5, 5],
             [5, 5, 5]])
    smooth.smooth(tst_arr, '9')
    assert(arr[0][0] == 4)

if __name__ == '__main__': 
    test_smooth()

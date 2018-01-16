#!/usr/bin/env python
import os
import sys
file_dir = os.path.dirname(os.path.realpath(__file__))
relative_path = '/../..'
path = os.path.abspath(file_dir + relative_path)
sys.path.insert(0, path)
import mospred.thickness as thickness
import data_mgmt.Wisps_data as wd


def test_thickness():
    """  """

    thickness.thickness(


def get_dummy_obj():
    obj = wd.Wisps_data('thickness')
    



if __name__ == '__main__': 
    test_thickness()

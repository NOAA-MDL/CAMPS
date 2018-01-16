#!/usr/bin/env python
import os
import sys
file_dir = os.path.dirname(os.path.realpath(__file__))
relative_path = '/..'
path = os.path.abspath(file_dir + relative_path)
sys.path.insert(0, path)
import reader

def _get_test_data():
    """Returns test data"""
    pass

def test_read():
    """  """
    pass

def test_add_metadata_from_netcdf_variable():
    """  """
    pass

def test_read_var():
    """  """
    pass

def test_subset_time():
    """Test subset_time function."""

def test_create_time():
    """  """
    pass

def test_get_procedures():
    """  """
    pass

def test_get_times():
    """  """
    pass

def test_get_coordinate():
    """  """
    pass

def test_removeTime():
    """  """
    pass

def test_get_metadata():
    """  """
    pass

def test_create_wisps_data():
    """  """
    pass

def test_parse_processes_string():
    """  """
    pass

def test_separate_procedure_and_data():
    """  """
    pass

def test_separate_time_and_data():
    """  """
    pass

def test_separate_coordinate_and_data():
    """  """
    pass




if __name__ == "__main__":
    test_read()
    test_add_metadata_from_netcdf_variable()
    test_read_var()
    test_subset_time()
    test_create_time()
    test_get_procedures()
    test_get_times()
    test_get_coordinate()
    test_removeTime()
    test_get_metadata()
    test_create_wisps_data()
    test_parse_processes_string()
    test_separate_procedure_and_data()
    test_separate_time_and_data()
    test_separate_coordinate_and_data()

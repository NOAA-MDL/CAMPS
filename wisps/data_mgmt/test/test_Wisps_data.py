#!/usr/bin/env python
import os, sys
relative_path = os.path.abspath(os.path.dirname(os.path.realpath(__file__))+"/..")
sys.path.insert(0, relative_path)
from Wisps_data import Wisps_data
import writer
import pdb
import numpy as np
from netCDF4 import Dataset

num_passed = 0

def passed():
    global num_passed
    print "passed", num_passed
    num_passed += 1

def test_check_correct_dimension():
    obj = Wisps_data('wind_speed')
    obj.set_dimensions(('some_dim',))
    #obj.add_data(np.zeros((12,12))) #adding 2 dimensional array
    obj.data = np.zeros((10,100))
    obj_arr = [obj]
    res = False
    try:
        writer.get_dimensions(obj_arr) #should throw ValueError
    except ValueError:
        # Should throw value error
        res = True
    assert res == True
    passed()
    obj.set_dimensions(('some_dim1', 'some_dim2'))
    obj_arr = [obj]
    dims = writer.get_dimensions(obj_arr)
    assert dims['some_dim1'] == 10
    assert dims['some_dim2'] == 100
    passed()




def test_variable():

    mmk = Wisps_data('wind_speed')
    nc = Dataset('test2.nc', 'w', format="NETCDF4")
    mmk.dimensions = ['ayy','bee']
    mmk.data = np.array([[1,2,34],[3,2,9]])
    mmk.get_nc_variable(nc)
    passed() 


test_variable()
test_check_correct_dimension()

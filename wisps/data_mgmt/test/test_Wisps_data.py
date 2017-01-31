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

def passed(func=""):
    global num_passed
    print "passed",func, num_passed
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
    passed("check_dim")
    obj.set_dimensions(('some_dim1', 'some_dim2'))
    obj_arr = [obj]
    dims = writer.get_dimensions(obj_arr)
    assert dims['some_dim1'] == 10
    assert dims['some_dim2'] == 100
    passed("check shape")




def test_variable():

    temp = Wisps_data('wind_speed')
    nc = Dataset('test2.nc', 'w', format="NETCDF4")
    temp.dimensions = ['ayy','bee']
    temp.data = np.array([[1,2,34],[3,2,9]])
    temp.write_to_nc(nc)
    nc.close()
    passed("test_variable") 

def test_plev():
    nc = Dataset('test2.nc', 'w', format="NETCDF4")
    temp = Wisps_data('test_plev')
    temp.dimensions = ['ayy','bee']
    temp.data = np.array([[1,2,34],[3,2,9]])
    temp.write_to_nc(nc)

    temp2 = Wisps_data('test_plev2')
    temp2.dimensions = ['ayy','bee']
    temp2.data = np.array([[1,2,34],[3,2,9]])
    temp2.write_to_nc(nc)

    temp2 = Wisps_data('test_elev')
    temp2.dimensions = ['ayy','bee']
    temp2.data = np.array([[1,2,34],[3,2,9]])
    temp2.write_to_nc(nc)

    temp2 = Wisps_data('test_elev_bounds')
    temp2.dimensions = ['ayy','bee']
    temp2.data = np.array([[1,2,34],[3,2,9]])
    temp2.write_to_nc(nc)

    temp2 = Wisps_data('test_plev_bounds')
    temp2.dimensions = ['ayy','bee']
    temp2.data = np.array([[1,2,34],[3,2,9]])
    temp2.write_to_nc(nc)
    nc.close()

    passed("test_plev") 

def test_has_coord():
    temp = Wisps_data('test_plev')
    assert temp.has_plev()
    assert not temp.has_elev()
    assert not temp.has_bounds()
    temp = Wisps_data('test_time_bounds')
    assert not temp.has_plev()
    assert not temp.has_elev()
    assert temp.has_time_bounds()
    assert not temp.has_elev_bounds()
    temp = Wisps_data('test_elev_bounds')
    assert not temp.has_plev()
    assert temp.has_elev()
    assert temp.has_elev_bounds()
    passed("test_coord")
    

test_has_coord()
test_variable()
test_plev()
test_check_correct_dimension()

#!/usr/bin/env python
import numpy as np
from netCDF4 import Dataset
import pdb
import time
from subprocess import call


filename = '/scratch3/NCEPDEV/mdl/Riley.Conroy/test.nc'

def get_2d_array(xsize, ysize):
    return np.random.rand(xsize,ysize)

def get_3d_array(xsize, ysize, zsize):
    return np.random.rand(xsize,ysize, zsize)

def write_nc(array, numTimes):
    nc = Dataset(filename,mode='w', format="NETCDF4")
    dimensions = ['a','b','c','d','e','f','g']
    shape = array.shape
    dimensions = dimensions[:len(shape)]
    for i,d in enumerate(dimensions):
        nc.createDimension(d, shape[i])

    dimensions = tuple(dimensions)
    for i in range(numTimes):
        var = nc.createVariable('testVar'+str(i),
            datatype=array.dtype, 
            dimensions=dimensions)
        var[:] = array
    nc.close()

def read_nc(filename):
    start = time.time()
    nc = Dataset(filename,mode='r', format="NETCDF4")
    tmp_arr = []
    for i in nc.variables:
        tmp_arr = nc.variables[i][:]
        tmp_arr = tmp_arr[:]
        #other_arr = tmp_arr[255,255,20]
#        print other_arr
    print "done reading nc"
    end = time.time()
    print "Elapsed Time : ", end-start
        
def test_write_3d():
    arr = get_2d_array(300,300)
    for i in range(10):
        newarr = get_2d_array(300,300)
        arr = np.dstack((arr, newarr))
    write_nc(arr, 1000)

def test_write_2d():
    arr = get_2d_array(300,300)
    write_nc(arr, 10000)


def test_num_vars():
    x = [50000, 5000 , 5000, 500 , 500]
    y = [50000, 50000, 5000, 5000, 500]
    for i,num in enumerate([1,10,100,1000,10000]):
        call(['rm','-f',filename])
        print i
        print 'size', x[i] * y[i] * num
        print 'num vars', num
        arr = get_2d_array(x[i],y[i])
        print 'writing'
        write_nc(arr, num)
        print 'reading'
        read_nc(filename)
    

def test_write_var():
    filename = 'testaroo.nc'
    nc = Dataset(filename,mode='w', format="NETCDF4")
    nc.createDimension('a',300)
    nc.createDimension('b',200)
    nc.createDimension('c',3)
    dimensions = ('a','b','c')
    array = np.random.rand(300,200,3)
    var = nc.createVariable('testVar',
            datatype=array.dtype, 
            dimensions=dimensions)
    var[:] = array
    call(['rm','-f',filename])

test_num_vars()

#print "writing 2D"
#test_write_2d()
#print "reading"
#read_nc(filename)

#call(['rm','-f',filename])
#
#print "writing 3D"
#test_write_3d()
#print "reading"
#read_nc(filename)





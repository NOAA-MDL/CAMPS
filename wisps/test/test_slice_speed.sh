#!/bin/bash

echo "Using 300 x 300 x 300 == 27,000,000 doubles == 216 Mb"

if [[ $1 ]]; then
echo "SLICING from memory"

echo "slicing [:]"
python -m timeit \
    -s 'import numpy' \
    -s 'arr = numpy.random.rand(300,300,300)' \
    'subset = arr[:]'

echo "slicing [:,:,:]"
python -m timeit \
    -s 'import numpy' \
    -s 'arr = numpy.random.rand(300,300,300)' \
    'subset = arr[:,:,:]'

echo "slicing [:,:,1]"
python -m timeit \
    -s 'import numpy' \
    -s 'arr = numpy.random.rand(300,300,300)' \
    'subset = arr[:,:,1]'

echo "slicing [:,250,:]"
python -m timeit \
    -s 'import numpy' \
    -s 'arr = numpy.random.rand(300,300,300)' \
    'subset = arr[:,250,:]'

echo "slicing [250,:,:]"
python -m timeit \
    -s 'import numpy' \
    -s 'arr = numpy.random.rand(300,300,300)' \
    'subset = arr[250,:,:]'

echo "slicing [100:200,:,:]"
python -m timeit \
    -s 'import numpy' \
    -s 'arr = numpy.random.rand(300,300,300)' \
    'subset = arr[100:200,:,:]'

echo "slicing [100:200,:,1]"
python -m timeit \
    -s 'import numpy' \
    -s 'arr = numpy.random.rand(300,300,300)' \
    'subset = arr[100:200,:,1]'

echo "slicing [100:200,100:200,1]"
python -m timeit \
    -s 'import numpy' \
    -s 'arr = numpy.random.rand(300,300,300)' \
    'subset = arr[100:200,100:200,1]'

fi


echo "SLICING from memory"


echo "slicing [:]"
python -m timeit \
    -s 'from netCDF4 import Dataset' \
    -s 'nc = Dataset("/scratch3/NCEPDEV/mdl/Riley.Conroy/test.nc", mode="r", format="NETCDF4")' \
    'subset = nc.variables["testVar0"][:]'

echo "slicing [150,:,:]"
python -m timeit \
    -s 'from netCDF4 import Dataset' \
    -s 'nc = Dataset("/scratch3/NCEPDEV/mdl/Riley.Conroy/test.nc", mode="r", format="NETCDF4")' \
    'subset = nc.variables["testVar0"][150,:,:]'

echo "slicing [:,150,:]"
python -m timeit \
    -s 'from netCDF4 import Dataset' \
    -s 'nc = Dataset("/scratch3/NCEPDEV/mdl/Riley.Conroy/test.nc", mode="r", format="NETCDF4")' \
    'subset = nc.variables["testVar0"][:,150,:]'
 
echo "slicing [:,:,150]"
python -m timeit \
    -s 'from netCDF4 import Dataset' \
    -s 'nc = Dataset("/scratch3/NCEPDEV/mdl/Riley.Conroy/test.nc", mode="r", format="NETCDF4")' \
    'subset = nc.variables["testVar0"][:,:,150]'

echo "slicing [50:250,:,150]"
python -m timeit \
    -s 'from netCDF4 import Dataset' \
    -s 'nc = Dataset("/scratch3/NCEPDEV/mdl/Riley.Conroy/test.nc", mode="r", format="NETCDF4")' \
    'subset = nc.variables["testVar0"][50:250,:,150]'

echo "slicing [50:250,100:200,150]"
python -m timeit \
    -s 'from netCDF4 import Dataset' \
    -s 'nc = Dataset("/scratch3/NCEPDEV/mdl/Riley.Conroy/test.nc", mode="r", format="NETCDF4")' \
    'subset = nc.variables["testVar0"][50:250,100:200,150]'

echo "slicing [50:250,100:200,150:250]"
python -m timeit \
    -s 'from netCDF4 import Dataset' \
    -s 'nc = Dataset("/scratch3/NCEPDEV/mdl/Riley.Conroy/test.nc", mode="r", format="NETCDF4")' \
    'subset = nc.variables["testVar0"][50:250,100:200,150:250]'


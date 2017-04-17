#!/usr/bin/env python
import sys
from netCDF4 import Dataset
import pdb
file1 = sys.argv[1]
file2 = sys.argv[2]
printErr = False
if len(sys.argv) <= 3:
    printErr = True

print 'reading', file1
nc1 = Dataset(file1, mode='r', format="NETCDF4")
print 'reading', file2
nc2 = Dataset(file2, mode='r', format="NETCDF4")

print 'which variable do you want to check?'
ans = raw_input()
ans_arr = []
if ans == 'all':
    ans_arr = nc1.variables.keys()
else:
    ans_arr = [ans]
for var in ans_arr:
    big_counter = 0
    counter = 0
    different = 0
    num_points = 0
    num_bad_points = 0
    # if nc1.variables[var].dtype is np.dtype('float32'):

    for s in range(3000):

        var1 = nc1.variables[var][s + different]
        var2 = nc2.variables[var][s]
        #time = nc1.variables['observation_time']
        while nc1.variables['METAR_station_name_instant_'][s + different][0] != nc2.variables['METAR_station_name_instant_'][s][0] \
                or \
                nc1.variables['METAR_station_name_instant_'][s + different][1] != nc2.variables['METAR_station_name_instant_'][s][1] \
                or \
                nc1.variables['METAR_station_name_instant_'][s + different][2] != nc2.variables['METAR_station_name_instant_'][s][2] \
            or \
                nc1.variables['METAR_station_name_instant_'][s + different][3] != nc2.variables['METAR_station_name_instant_'][s][3]:
            print 'Different'
            different += 1
            var1 = nc1.variables[var][s + different]
        if printErr:
            print nc1.variables['METAR_station_name_instant_'][s + different], nc2.variables['METAR_station_name_instant_'][s]
        if len(var1) != len(var2):
            if printErr:
                print 'Error: The two variables dont have the same length'
                print len(var1)
                print len(var2)

        for hour, (i, j) in enumerate(zip(var1, var2)):
            num_points += 1
            if i != j:
                counter += 1
                num_bad_points += 1
                if printErr:
                    print i, 'not equal to', j
                    print 'at index', str(hour)
                    print 'at station', nc1.variables['METAR_station_name_instant_'][s]
        if counter > 0:
            big_counter += 1
        counter = 0

    print var
    print 3000 - big_counter, "of 3000 stations ok"
    print "number of different", different
    print 100 - (float(num_bad_points) / float(num_points)), "accuracy"
    raw_input("continue?")

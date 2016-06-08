#!/contrib/anaconda/2.3.0/bin/python
#
# This example creates an HDF5 file compound.h5 and an empty datasets /DSC in it.
#
import h5py
import numpy as np
#
# Create a new file using default properties.
#
file = h5py.File('compound.h5','w')
#
# Create a dataset under the Root group.
#
#comp_type = np.dtype([('Orbit', 'i'), ('Location', np.str_, 6), ('Temperature (F)', 'f8'), ('Pressure (inHg)', 'f8')])
comp_type = np.dtype([('Cycle', 'i'), ('Station', np.str_, 4), ('Valid Hour', 'i'), ('Temperature', 'i')])
dataset = file.create_dataset("GFS",(4,), comp_type)
data = np.array([(0, "KDCA", 0, 32.0), (0, "KBWI", 0, 80.0), (6, "KDCA", 3, 34.0), (6, "KBWI", 3, 82.0)], dtype = comp_type)
dataset[...] = data
#
# Close the file before exiting
#
file.close()
file = h5py.File('compound.h5', 'r')
dataset = file["GFS"]
print "Reading Orbit and Location fields..."
orbit = dataset['Cycle']
print "Cycle: ", orbit
location = dataset['Station']
print "Station: ", location
data = dataset[...]
print "Reading all records:"
print data
print "Second element of the third record:", dataset[2, 'Station']
file.close()


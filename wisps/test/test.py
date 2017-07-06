import sys
import pdb
import matplotlib.pyplot as plt
import numpy as np
from netCDF4 import Dataset
from scipy.interpolate import griddata


filename = sys.argv[1]
print "opening", filename
mmk = Dataset(filename, 'r')
#temp = mmk['TMP_1000mb']
for i in mmk.variables.keys():

    print i
    temp = mmk[i]
    try:
        x = mmk['x'][:]
        y = mmk['y'][:]
    except:
        x = mmk['GFS_xProj_instant__1'][:]
        y = mmk['GFS_xProj_instant__'][:]
    xx, yy = np.meshgrid(x,y)
    xxx = xx.flatten()
    yyy = yy.flatten()
    xy = np.dstack((xxx,yyy))[0]
    points = xy
    try:
        #values = temp[0,:]
        values = temp[:,:,0,0]
    except:
        continue
    values = values.flatten()
    
    maxX = x[-1]
    maxY = y[-1]
    xix, xiy = np.mgrid[0:maxX:500j, 0:maxY:500j]
    
    
    try:
        grid_z0 = griddata(points, values, (xix,xiy), method='linear')
    except:
        continue
    plt.plot(points[:,0], points[:,1], 'k.', ms=1)
    plt.imshow(np.rot90(grid_z0), extent=(0,maxX,0,maxY))
    plt.show()
    
    

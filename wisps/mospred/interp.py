import sys
import os
relative_path = os.path.abspath(
    os.path.dirname(os.path.realpath(__file__)) + "/..")
sys.path.insert(0, relative_path)
import registry.util as cfg
import pdb
import matplotlib.pyplot as plt
import numpy as np
from netCDF4 import Dataset
from scipy.interpolate import griddata
from pyproj import Proj




def interp(x, y, model_values, station_lat, station_lon, method='linear'):
    """
    x - the x coordinate values in projected grid
    y - the y coordinate values in projected grid
    model_values - grid point values for observations
    station_lat - 1 or 2 dimensional array of latitude points
    station_lon - 1 or 2 dimensional array of longitude points
    """

    model_values_1d = model_values.flatten()
    # Create 2d grid of x and y coordinates
    # e.g. xx will have shape (len(x),len(y))
    xx, yy = np.meshgrid(x,y)
    # Must make then make them 1d
    x_1d = xx.flatten()
    y_1d = yy.flatten()

    # Stack then and transpose. griddata expects shape (n, D)
    # Where n in size of array and D is number of dimensions... or 2
    points = np.array((x_1d, y_1d)).T

    # The point(s) at which to interpolate
    xi_x,xi_y = reproject(station_lon, station_lat)

    try:
        grid_z0 = griddata(points, model_values_1d, (xi_x,xi_y), method='linear')
    except ValueError:
        
        print "shape of points", points.shape
        print "shape of model values", model_values_1d.shape
        raise
    except:
        raise

    return grid_z0

    

def reproject(lon=None, lat=None):
    """
    Given collection of lat and lon, reproject into appropriate grid space.
    """
    # Get projection information
    assert lon is not None and lat is not None
    control = cfg.read_mospred_control()
    projparams = control['projparams']
    p = Proj(projparams=projparams)
    x,y = p(lon, lat )
    return (x,y)



def test(filename):
    #filename = sys.argv[1]
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
            y = mmk['GFS_yProj_instant__'][:]
            x = mmk['GFS_xProj_instant__'][:]
        xx, yy = np.meshgrid(x,y)
        xxx = xx.flatten()
        yyy = yy.flatten()
        xy = np.dstack((xxx,yyy))[0]
        points = xy
        pdb.set_trace()
        try:
            #values = temp[0,:]
            values = temp[:,:,0,0]
        except Exception as e:
            print e
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
        
        

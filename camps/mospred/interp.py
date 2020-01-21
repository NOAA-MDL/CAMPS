import sys
import os
import logging
import pdb
import numpy as np
from netCDF4 import Dataset
from scipy.interpolate import griddata
from pyproj import Proj

from ..registry import util as cfg
from . import util
from ..core.Camps_data import Camps_data


"""Module: interp.py

Methods:
    interp_setup
    interp
    bilinear_interp
    budget_interp
    get_projparams
    reproject
    test
"""


def interp_setup(w_obj, xi_x, xi_y, interp_method):
    """Performs interpolation of gridded model data onto stations.
    Interpolation method is set in the predictors conrol file.
    """
    #--------------------------------------------------------------------------
    # Get some relevant information for interpolation
    #--------------------------------------------------------------------------
    # Extract x,y variables
    x = w_obj.location.get_x()
    y = w_obj.location.get_y()
    # Extract model_values
    model_values = w_obj.data
    if len(model_values.shape) > 2: 
        model_values = model_values[:,:,0]
    #--------------------------------------------------------------------------

    #--------------------------------------------------------------------------
    # Perform interpolation
    #--------------------------------------------------------------------------
    if 'bilinear' in interp_method:
        data = bilinear_interp(x, y, model_values, xi_x, xi_y)
        w_obj.add_process('BiLinInterp')
    elif 'budget' in interp_method:
        data = budget_interp(model_values,np.hstack((xi_x[:,None],xi_y[:,None])),x[1],y[1])
        w_obj.add_process('BudgetInterp')
    elif 'linear' in interp_method:
        data = interp(x,y, model_values, xi_x,xi_y)
    else: 
        logging.warning('Must pass valid interpolation method')
    #--------------------------------------------------------------------------
    # Add interpolated data and info to CAMPS data object
    #--------------------------------------------------------------------------
    station_dim = cfg.read_dimensions()['nstations']
    w_obj.dimensions = [station_dim]
    w_obj.data = data
    #--------------------------------------------------------------------------

    return w_obj


def interp(x, y, model_values, xi_x, xi_y):
    """Performs a simple linear interpolation using griddata function
    x - the x coordinate values in projected grid
    y - the y coordinate values in projected grid
    model_values - grid point values for observations
    station_lat - 1 or 2 dimensional array of latitude points
    station_lon - 1 or 2 dimensional array of longitude points
    """

    #--------------------------------------------------------------------------
    # Set up model data and x, y points in 1-d format
    #--------------------------------------------------------------------------

    # Flatten data array
    model_values_1d = model_values.flatten()

    # Create 2d grid of x and y coordinates
    # e.g. xx will have shape (len(x),len(y))
    xx, yy = np.meshgrid(x,y)

    # Must make then make them 1d
    x_1d = xx.flatten()
    y_1d = yy.flatten()

    # Stack and transpose. griddata expects shape (n, D)
    # Where n in size of array and D is number of dimensions... or 2
    points = np.array((x_1d, y_1d)).T

    # The point(s) at which to interpolate in grid space.
    #xi_x,xi_y = reproject(projparams, station_lon, station_lat)

    #--------------------------------------------------------------------------
    # Perform interpolation onto stations
    #--------------------------------------------------------------------------
    try:
        grid_z0 = griddata(points, model_values_1d, (xi_x, xi_y), method='linear')
    except ValueError:
        logging.error("Could not complete griddata routine.")
        logging.error("Shape of points" + str( points.shape))
        logging.error("shape of model values" + str(model_values_1d.shape))
        raise
    except:
        raise
    #--------------------------------------------------------------------------

    return grid_z0


def bilinear_interp(x,y,model_values,xi_x,xi_y):
    """Performs the MOS bilinear interpolations scheme from grid to stations"""

    #get distances between grid points and data points
    dx = xi_x.round(0)-xi_x
    dy = xi_y.round(0)-xi_y
    #convert to indices for data points
    xi = (xi_x/x[1]).astype(int)
    yi = (xi_y/y[1]).astype(int)
    #get 'next' index in each direction
    xi1 = xi+1
    yi1 = yi+1
    #adjust end points of 'next' index
    xi1[xi1>model_values.shape[1]-1] = model_values.shape[1]-1
    yi1[yi1>model_values.shape[0]-1] = model_values.shape[0]-1
    #Perform bilinear interpolation
    grid_z0 = model_values[yi,xi] + (model_values[yi,xi1]-model_values[yi,xi])*dx + (model_values[yi1,xi]-model_values[yi,xi])*dy + (model_values[yi,xi]+model_values[yi1,xi1]-model_values[yi1,xi]-model_values[yi,xi1])*dx*dy

    return grid_z0


def budget_interp(a,coords,ref_x,ref_y):
    """Port of MOS2K routine intrp.f which performs interpolation for precipitation
    amount fields. This is also known as "budget" interpolation, but might not be
    1:1 exact as NCEP's IPLIB budget interpolation routine, polates3.f90
    """

    if len(coords.shape) == 1: coords = coords.reshape(1,coords.shape[0],order='F')
    nx = a.shape[0]
    ny = a.shape[1]
    awork = np.copy(a)

    #print " ===== INSIDE FUNCTION BUDGET_INTERP ===== "
    #print "(1) A = ",np.transpose(awork)
    #print "(2) AWORK = ",np.transpose(awork)
    #print "(3) AWORK = A? ",np.array_equal(a,awork)

    it = np.nditer([a,awork],flags=['multi_index','f_index'],op_flags=[['readonly'],['readwrite']])
    for a1,aw1 in it:
        i = it.multi_index[0]
        j = it.multi_index[1]
        asum = 0.
        acount = 0
        if a1[...] <= 0.0:
            if j+1 >= 0 and j+1 <= ny-1:
                asum += a[i,j+1]
                acount += 1
            if j-1 >= 0 and j-1 <= ny-1:
                asum += a[i,j-1]
                acount += 1
            if i+1 >= 0 and i+1 <= nx-1:
                asum += a[i+1,j]
                acount += 1
            if i-1 >= 0 and i-1 <= nx-1:
                asum += a[i-1,j]
                acount += 1
            if acount > 0:
                aw1[...] = -1.0*(asum/np.float32(acount))

    #print "(4) AWORK UPDATED= ",np.transpose(awork)
            
    data = np.zeros((coords.shape[0]),dtype=np.float32,order='F')
    xcoords = coords[:,1]
    ycoords = coords[:,0]
    it = np.nditer([xcoords,ycoords,data],flags=['multi_index','f_index'],op_flags=[['readonly'],['readonly'],['readwrite']])
    for x1,y1,d1 in it:
        #convert to indices for data points
        i = (x1/ref_x).astype(int)
        j = (y1/ref_y).astype(int)
        dx = x1-np.float32(x1)
        dy = y1-np.float32(y1)
        if dx == 0.0 and dy == 0.0:
            d1[...] = a[i,j]
        else:
            d1[...] = awork[i,j]+\
                   ((awork[i+1,j]-awork[i,j])*dx)+\
                   ((awork[i,j+1]-awork[i,j])*dy)+\
                   (awork[i,j]+awork[i+1,j+1]-awork[i,j+1]-awork[i+1,j])*dx*dy
    data = np.where(data<0.0,0.0,data)

    return data


def get_projparams(filepath):
    """Gets projection metadata for variable and formats it correctly
    as a dictionary, to be passed into Proj function.
    """ 

    with Dataset(filepath, mode='r', format="NETCDF4") as nc:
        vnames = nc.variables.keys()
        pname = [n for n in vnames if 'grid' in n]
        var = nc.variables[pname[0]]
        pobj = Camps_data(pname, autofill=False)
        # Fill metadata dict
        metadata_exceptions = ['_FillValue']
        metadata_keys = var.ncattrs()
        for key in metadata_keys:
            if key not in metadata_exceptions:
                value = var.getncattr(key)
                pobj.add_metadata(key, value)

        projparams = {}
        # Get lower left grid info
        LL_lat = pobj.Lat1
        LL_lon = pobj.Lon1
        # Set keys from file
        projparams['a'] = pobj.radius
        projparams['b'] = pobj.radius
        projparams['lon_0'] = pobj.orientation
        projparams['lat_ts'] = pobj.stnd_parallel
        # Set projection specific keys (put in yaml file later??)
        if pobj.grid_mapping_name == 'polar_stereographic':
            projparams['to_meters'] = True
            projparams['x_0'] = 8001120.943743927
            projparams['y_0'] = 8001120.943743927
            projparams['proj'] = 'stere'
            projparams['lat_0'] = 90.0

    return projparams, LL_lat, LL_lon


def reproject(projparams, LL_lat, LL_lon, lon=None, lat=None):
    """Given collection of lat and lon, reproject into appropriate grid space."""

    # Get projection information
    #pdb.set_trace()
    assert lon is not None and lat is not None
    p = Proj(projparams=projparams)
    x,y = p(lon, lat)
    #LL_x,LL_y = p(LL_lon, LL_lat)
    #x_corr = np.array(x) - LL_x
    #y_corr = np.array(y) - LL_y 

    return (np.array(x),np.array(y))

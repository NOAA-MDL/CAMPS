import sys
import os
import logging
import pdb
import numpy as np
from netCDF4 import Dataset
from scipy.interpolate import griddata
from pyproj import Proj

from ..registry import util as cfg
from ..core.Camps_data import Camps_data


"""Module: interp.py

Methods:
    interp_setup
    interp
    bilinear_interp
    budget_interp
    biquadratic_interp
    nearest_neighbor_interp
    get_projparams
    reproject
    test
"""


def interp_setup(w_obj, xi_x, xi_y, interp_method):
    """Performs interpolation of gridded model data onto stations.
    Interpolation method is set in the predictors conrol file.
    """

    # Extract x,y variables
    x = w_obj.location.get_x()
    y = w_obj.location.get_y()

    # Extract model_values
    model_values = w_obj.data
    if len(model_values.shape) > 3:
        model_values = model_values[:,:,:,0]

    # Convert station x and y to grid referenced x and y
    xind = xi_x
    yind = xi_y
    #--------------------------------------------------------------------------
    # Perform interpolation
    #--------------------------------------------------------------------------
    if 'bilinear' in interp_method:
        data = bilinear_interp(model_values, xind, yind)
        w_obj.add_process('BiLinInterp')
    elif 'budget' in interp_method:
        data = budget_interp(model_values.harden_mask(),xind,yind)
        w_obj.add_process('BudgetInterp')
    elif 'biquadratic' in interp_method:
        data = biquadratic_interp(model_values, xind, yind)
        w_obj.add_process('BiQuadInterp')
    elif 'nearest' in interp_method:
        data = nearest_neighbor_interp(model_values, xind, yind)
        w_obj.add_process('NearestInterp')
    elif 'linear' in interp_method:
        data = interp(x,y, model_values.harden_mask(), xi_x,xi_y)
        w_obj.add_process('LinInterp')
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

    # Form the location array for stations
    # and form the totally maske array to be returned
    # when no data is available or griddata routine 
    # returns a ValueError exception.
    stn_locs = np.array((xi_x, xi_y)).T
    n_stns = stn_locs.shape[0]
    values = np.ones((n_stns,), dtype=np.int) * 9999.
    no_values_array = np.ma.array(values, mask=True)

    # Flatten data array
    mask = np.ma.getmaskarray(model_values)
    data = np.ma.getdata(model_values)
    model_values_1d = data[~mask].flatten()
    if model_values_1d.size == 0:
        return no_values_array

    # Create 2d grid of x and y coordinates
    # e.g. xx will have shape (len(x),len(y))
    xx, yy = np.meshgrid(x,y)

    # Must make then make them 1d
    x_1d = xx[~mask].flatten()
    y_1d = yy[~mask].flatten()

    # Stack and transpose grid x and y. griddata expects shape (n, D)
    # Where n in size of array and D is number of dimensions...
    points = np.array((x_1d, y_1d)).T

    #--------------------------------------------------------------------------
    # Perform interpolation onto stations
    #--------------------------------------------------------------------------
    try:
        grid_z0 = griddata(points, model_values_1d, stn_locs, method='linear')
    except ValueError:
        logging.error("Could not complete griddata routine.")
        logging.error("Shape of points" + str( points.shape))
        logging.error("shape of model values" + str(model_values_1d.shape))
        raise
    except:
        raise
    #--------------------------------------------------------------------------

    return np.ma.array(grid_z0)


def bilinear_interp(model_values,xind,yind):
    """Performs a bilinear interpolation scheme from a grid to stations."""

    # Convert to indices for data points and get distances
    # between grid points and data points
    xi = xind.astype(int)
    yi = yind.astype(int)
    dx = xind-xi
    dy = yind-yi

    # Get 'next' index in each direction
    xi1 = xi+1
    yi1 = yi+1

    # Adjust end points of indices
    xi[xi<0] = 0
    yi[yi<0] = 0
    xi[xi>model_values.shape[2]-2] = model_values.shape[2]-2
    yi[yi>model_values.shape[1]-2] = model_values.shape[1]-2

    # Get 'next' index in each direction
    xi1 = xi+1
    yi1 = yi+1

    # Perform bilinear interpolation
    data = model_values[:,yi,xi] + \
              (model_values[:,yi,xi1]-model_values[:,yi,xi])*dx + \
              (model_values[:,yi1,xi]-model_values[:,yi,xi])*dy + \
              (model_values[:,yi,xi]+model_values[:,yi1,xi1]-model_values[:,yi1,xi]-model_values[:,yi,xi1])*dx*dy

    return data


def budget_interp(a,xind,yind):
    """Part of MOS2K routine intrp.f which performs interpolation for precipitation
    amount fields. This is also known as "budget" interpolation, but might not be
    1:1 exact as NCEP's IPLIB budget interpolation routine, polates3.f90
    """

    # IMPORTANT: 2D grids in CAMPS are ordered j/y,i/x
    ny = a.shape[1]
    nx = a.shape[2]

    adata = np.ma.getdata(a)
    amask = np.ma.getmaskarray(a)

    awork = np.ma.copy(a)
    awork.soften_mask()
    awdata = np.ma.getdata(awork)
    awmask = np.ma.getmaskarray(awork)

    # Pre-process input 2D grid
    it = np.nditer([adata,awdata],flags=['multi_index',],op_flags=[['readonly'],['readwrite']])
    for a1,aw1 in it:
        d = it.multi_index[0]
        j = it.multi_index[1]
        i = it.multi_index[2]
        asum = 0.
        acount = 0
        if a1[...] <= 0.0:
            if j+1 in range(ny):
                asum += adata[d,j+1,i]
                acount += 1
            if j-1 in range(ny):
                asum += adata[d,j-1,i]
                acount += 1
            if i+1 in range(nx):
                asum += adata[d,j,i+1]
                acount += 1
            if i-1 in range(nx):
                asum += adata[d,j,i-1]
                acount += 1
            if acount > 0:
                aw1[...] = -1.0*(asum/np.float32(acount))

    # Setup output data array using xind shape info.
    # Pass pre-processed data array into bilinear interpolation function
    data = bilinear_interp(np.ma.array(awdata,mask=awmask), xind, yind)
    data[data<0.0] = 0.0
    return data
    

def biquadratic_interp(model_values,xind,yind):

    #Convert to indices for data points and get distances
    #between grid points and data points
    ndays = model_values.shape[0]
    dx = xind.round(0)-xind
    dy = yind.round(0)-yind
    xi = xind.astype(int)
    yi = yind.astype(int)

    #Adjust end points of indices
    xi[xi<0] = 0
    yi[yi<0] = 0
    xi[xi>model_values.shape[2]-2] = model_values.shape[2]-2
    yi[yi>model_values.shape[1]-2] = model_values.shape[1]-2

    #Get several 'adjacent' indices.
    xi1 = xi+1
    yi1 = yi+1
    yi2 = yi+2
    yiM1 = yi-1

    FCT = (dy**2-dy)/4
    FET = (dx**2-dx)/4
    # For points not along the grid boundary, perform biquadratic interpolation
    inner_ind = np.where((xi!=0) & (yi!=0) & (yi!=model_values.shape[0]-2) & (xi!=model_values.shape[1]-2))[0]
    D = []
    for j in range(4):
        X = xi[inner_ind] - 1 + j
        M = model_values[:,yi[inner_ind],X] + (model_values[:,yi1[inner_ind],X] - model_values[:,yi[inner_ind],X])*dy[inner_ind] + (model_values[:,yiM1[inner_ind],X]+model_values[:,yi2[inner_ind],X]-model_values[:,yi[inner_ind],X]-model_values[:,yi1[inner_ind],X])*FCT[inner_ind]
        D.append(M)

    data = np.ma.ones((ndays,xi.size))*9999
    data[:,inner_ind] = D[1]+(D[2]-D[1])*dx[inner_ind]+(D[0]+D[3]-D[1]-D[2])*FET[inner_ind]

    # For points along the grid boundary, perform bilinear interpolation
    bound_ind = np.where((xi==0) | (yi==0) | (xi==model_values.shape[1]-2) | (yi==model_values.shape[0]-2))[0]
    data[:,bound_ind] = model_values[:,yi[bound_ind],xi[bound_ind]] + \
    (model_values[:,yi[bound_ind],xi1[bound_ind]] - model_values[:,yi[bound_ind],xi[bound_ind]])*dx[bound_ind] + \
    (model_values[:,yi1[bound_ind],xi[bound_ind]] - model_values[:,yi[bound_ind],xi[bound_ind]])*dy[bound_ind] + \
    (model_values[:,yi[bound_ind],xi[bound_ind]] + model_values[:,yi1[bound_ind],xi1[bound_ind]] - \
    model_values[:,yi1[bound_ind],xi[bound_ind]] - model_values[:,yi[bound_ind],xi1[bound_ind]])*dx[bound_ind]*dy[bound_ind]

    return data


def nearest_neighbor_interp(model_values,xind,yind):

    # Round index values to nearest grid point
    xi = np.round(xind).astype(int)
    yi = np.round(yind).astype(int)

    ndays = model_values.shape[0]

    # Perform nearest neighbor interpolation, leaving points outside of grid boundary as missing.
    data = np.ma.ones((ndays,xi.size))*9999
    valid_ind = np.where((xi>=0) & (yi>=0) & (xi<model_values.shape[1]) & (yi<model_values.shape[0]))[0]
    data[:,valid_ind] = model_values[:,yi[valid_ind],xi[valid_ind]]

    return data


def get_projparams(filepath):
    """Gets projection metadata for variable and formats it correctly
    as a dictionary, to be passed into Proj function.
    """

    with Dataset(filepath, mode='r', format="NETCDF4") as nc:
        vnames = list(nc.variables.keys())
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
        LL_lat = nc.variables['latitude'][0,0]
        LL_lon = nc.variables['longitude'][0,0]
        dx = nc.variables['x'].grid_spacing
        dy = nc.variables['y'].grid_spacing

    projparams = {}
    for item in pobj.PROJ_string.split(" "):
        k,v = item.replace('+','').split('=')
        projparams[k] = float(v) if k != 'proj' else v

    return projparams, LL_lat, LL_lon, dx, dy


def reproject(projparams, LL_lat, LL_lon, dx, dy, lon=None, lat=None):
    """Given collection of lat and lon, reproject into appropriate grid space."""

    # Get projection information
    assert lon is not None and lat is not None
    p = Proj(projparams=projparams)
    x,y = p(lon,lat)

    return (np.array(x/dx),np.array(y/dy))

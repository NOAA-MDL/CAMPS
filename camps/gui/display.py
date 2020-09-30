import numpy as np
import matplotlib as mpl
mpl.use('TkAgg')  # or whatever other backend that you want
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import logging
try:
    from mpl_toolkits.basemap import Basemap
except ImportError as e:
    logging.warning("not importing basemap, not installed")
    pass
from matplotlib.path import Path
import random
import re
import sys
import os
import datetime
from netCDF4 import Dataset

relative_path = os.path.abspath(
    os.path.dirname(os.path.realpath(__file__)) + "/..")
sys.path.insert(0, relative_path)

import registry


def display(grid, filename=None, axis=True):
    img = plt.imshow(grid,origin='lower', cmap=cm.gist_rainbow, vmin=0, vmax=1)
    img.set_cmap('tab20b')
    if not axis:
        plt.axis('off')
    if filename is None:
        plt.savefig('img'+str(random.randint(1,30))+'.png')
    else:
        plt.savefig(filename + '.png', bbox_inches='tight')
    plt.show()




def map_set(in_data,variable,time,plot_type='grid',bounds='Full',LCOlon=None,UCOlon=None,LCOlat=None,UCOlat=None,Thresh=None,**kwargs):
    ######################################################################################################
    # map_set takes a netcdf file or netcdf Dataset object and retrieves data and projection information.
    # This information is then given to the displaymap function to plot the data on a geographical map.
    #
    # Version 2.3:
    #    Inputs are:
    #       in_data: (Required) Can either be a netcdf Dataset object or a str indicating the name of a
    #                netcdf file to be opened
    #
    #       variable: (Required) The variable in "in_data" to be plotted.
    #
    #       time: (Required) an integer value indicating the forecast reference time of the data to be
    #             plotted. Must match a time found in in_data.
    #
    #       bounds: a string indicating the expanse of "in_data" to be plotted. Default is "Full",
    #               indicating the entire lat/lon grid provided. Other options are "SW","NW","NE", & "SE"
    #               which would plot the bottom left, top left, top right, and bottom right corners of the
    #               full field, respectively.
    #
    #       Alternatively, custom bounds can be provided:
    #       LCOlon/LCOlat: Lower Corner Longitude and Latitude. The coordinates for the lower left corner
    #                      of the desired grid.
    #
    #       UCOlon/UCOlat: Upper Corner Longitude and Latitude. The coordinates for the upper right corner
    #                      of the desired grid.
    #       plot_type: The type of desired output plot. Valid values are 'grid' or 'station'. A grid plot
    #                  will create either a contour or filled contour plot of the given variable. A station
    #                  plot will create a plot of given station data. This argument is used in conjunction
    #                  with the **kwargs "grid" and "stations", described below.
    #
    #       Thresh:  Threshold(s) to be used for contour levels. Can be either an Integer, a list or tuple
    #                of length >1. If an integer is given, contour levels will be evenly spaced from Thresh
    #                to the maximum value of variable. If a list or tuple of length 2 is given, contour
    #                levels will be evenly spaced between the first and second items of Thresh. If a list
    #                or tuple of length >2 is given, contour levels will be set equal to the provided
    #                values. All data below first level will be masked. Default: Thresh=0
    #
    #       **kwargs are passed on to displaymap. Accepted additional arguments are:
    #       filename: If set, resulting image will be saved as a .png file. If None, resulting image will
    #                 be displayed. Default is None.
    #
    #        grid: A value of Fill will create a filled contour plot. A value of Contour will create a
    #              regular contour plot. A value of None will create a plot based solely on station data.
    #              Note: stations argument must also be 'True' for stations data plot.
    #              Default: Fill
    #
    #       stations: Boolean value. If True with a grid argument value of 'Fill' or 'Contour', data value
    #                 at point of stations is plotted on grid. If True with a grid argument value of 'None',
    #                 station data will be plotted. If False, no station data will be plotted. Which stations
    #                 are plotted is based upon scale of grid. If grid is None, stations must be True.
    #                 Default: True
    #
    #
    ######################################################################################################
    '''
     map_set takes a netcdf file or netcdf Dataset object and retrieves data and projection information.
        This information is then given to the displaymap function to plot the data on a geographical map.

        Inputs are:
           in_data: (Required) Can either be a netcdf Dataset object or a str indicating the name of a
                    netcdf file to be opened

           variable: (Required) The variable in "in_data" to be plotted.

           time: (Required) an integer value indicating the forecast reference time of the data to be
                 plotted. Must match a time found in in_data.

           bounds: a string indicating the expanse of "in_data" to be plotted. Default is "Full",
                   indicating the entire lat/lon grid provided. Other options are "SW","NW","NE", & "SE"
                   which would plot the bottom left, top left, top right, and bottom right corners of the
                   full field, respectively.

           Alternatively, custom bounds can be provided:
           LCOlon/LCOlat: Lower Corner Longitude and Latitude. The coordinates for the lower left corner
                          of the desired grid.

           UCOlon/UCOlat: Upper Corner Longitude and Latitude. The coordinates for the upper right corner
                          of the desired grid.
           plot_type: The type of desired output plot. Valid values are 'grid' or 'station'. A grid plot
                      will create either a contour or filled contour plot of the given variable. A station
                      plot will create a plot of given station data. This argument is used in conjunction
                      with the **kwargs "grid" and "stations", described below.

           Thresh:  Threshold(s) to be used for contour levels. Can be either an Integer, a list or tuple
                    of length >1. If an integer is given, contour levels will be evenly spaced from Thresh
                    to the maximum value of variable. If a list or tuple of length 2 is given, contour
                    levels will be evenly spaced between the first and second items of Thresh. If a list
                    or tuple of length >2 is given, contour levels will be set equal to the provided
                    values. All data below first level will be masked. Default: Thresh=0

           **kwargs are passed on to displaymap. Accepted additional arguments are:
           filename: If set, resulting image will be saved as a .png file. If None, resulting image will
                     be displayed. Default is None.

           grid: A value of Fill will create a filled contour plot. A value of Contour will create a
                 regular contour plot. A value of None will create a plot based solely on station data.
                 Note: stations argument must also be 'True' for stations data plot.
                 Default: Fill

           stations: Boolean value. If True with a grid argument value of 'Fill' or 'Contour', data value
                     at point of stations is plotted on grid. If True with a grid argument value of 'None',
                     station data will be plotted. If False, no station data will be plotted. Which stations
                     are plotted is based upon scale of grid. If grid is None, stations must be True.
                     Default: True

    '''
    #-----------------------------------------------------------------------------
    # Several checks to be sure input arguments are valid
    #-----------------------------------------------------------------------------
    # Check to see that input data is either a string (filename) or a Dataset object
    try:
        if isinstance(in_data,str):
            F = Dataset(in_data)
        elif isinstance(in_data,Dataset):
            F = in_data
    except:
        raise ValueError("IN_DATA is not valid. Must either be a string type filename or a netCDF Dataset object")

    # Check to be sure that the desired variable exists in the file. If not errors with list of available variables
    try:
        data_info = F.variables[variable]
    except:
        raise KeyError("VARIABLE "+str(variable)+" NOT FOUND. AVAILABLE VARIABLES ARE: "+str(list(F.variables.keys())))

    # Retrieve data and time information
    S = data_info.shape
    times = F.variables['FcstRefTime'][:]
    Utimes = np.array([datetime.datetime.fromtimestamp(t).strftime('%Y%m%d%H') for t in times]).astype(int)
    # Check for desired time in Forecast Reference Time. If not available, error with list of available times.
    try:
        itime = np.where(Utimes==time)[0][0]
    except IndexError:
        raise IndexError("TIME "+str(time)+" NOT VALID. VALID TIMES ARE: "+str(Utimes[:]))

    # Currently checks for "grib_gds" for projection information of gridded data. Can be changed as needed.
    # If no projection information is available. Sets some default information.
    try:
        gds = F.variables['grib_gds'][:]
        lon_0 = (float(gds[6])/1000+180)%360-180
        lat_0 = float(gds[11])/1000
        proj = gds[0]
    except:
        proj = '4'
        lon_0 = -95
        lat_0 = 25

    #--------------------------------------------------------------------------------
    # Set up lat and lon bounds based on inputs
    #--------------------------------------------------------------------------------
    lats = F.variables['latitude'][:]
    lons = F.variables['longitude'][:]
    CONUS_BOUNDS=[-130,-60,22,55]
    #If data to be plotted is gridded data. uses lat and lons to determine boundaries.
    #If station data, creates lat and lon information from CONUS_BOUNDS.
    if plot_type=='grid':
        nlat = lats.shape[0]
        nlon = lats.shape[1]
        latmid=lats[0,0]/2+lats[-1,-1]/2
        lonmid=lons[0,0]/2+lons[-1,-1]/2
    elif plot_type=='station':
        lat_vect = np.arange(CONUS_BOUNDS[2],CONUS_BOUNDS[3])
        lon_vect = np.arange(CONUS_BOUNDS[0],CONUS_BOUNDS[1])
        nlon = lon_vect.size
        nlat = lat_vect.size
        LATS = lats
        LONS = lons
        lons, lats = np.meshgrid(lon_vect,lat_vect)
        latmid=lats[0,0]/2+lats[-1,-1]/2
        lonmid=lons[0,0]/2+lons[-1,-1]/2
    dists = np.sqrt((lons-lonmid)**2+(lats-latmid)**2)
    idx = np.unravel_index(dists.argmin(),lons.shape)
    #Checks for provided lat/lon corners of desired grid. Otherwise checks the 'bounds' argument and sets
    #lat/lon corners as well as starting and ending indices to correspond with lat/lon and data arrays
    if not LCOlon or not LCOlat or not UCOlon or not UCOlat:
        if bounds=='Full':
            LCOlon = (lons[0,0]+180)%360-180
            UCOlon = (lons[-1,-1]+180)%360-180
            LCOlat = lats[0,0]
            UCOlat = lats[-1,-1]
            lonstart = 0
            lonend = None
            latstart = 0
            latend = None
        elif bounds=='SW':
            LCOlon = (lons[0,0]+180)%360-180
            UCOlon = (lons[nlat/2,nlon/2]+180)%360-180
            LCOlat = lats[0,0]
            UCOlat = lats[nlat/2,nlon/2]
            lonstart = 0
            lonend = nlon/2
            latstart = 0
            latend = nlat/2
        elif bounds=='SE':
            LCOlon = (lons[0,nlon/2]+180)%360-180
            UCOlon = (lons[nlat/2,-1]+180)%360-180
            LCOlat = lats[0,nlon/2]
            UCOlat = lats[nlat/2,-1]
            lonstart = nlon/2
            lonend = None
            latstart = 0
            latend = nlat/2
        elif bounds=='NW':
            latstart = lats.shape[0]/2
            latend = None
            lonstart = 0
            lonend = lons.shape[1]/2
            LCOlon = (lons[nlat/2,0]+180)%360-180
            UCOlon = (lons[-1,nlon/2]+180)%360-180
            LCOlat = lats[nlat/2,0]
            UCOlat = lats[-1,nlon/2]
        elif bounds=='NE':
            LCOlon = (lons[nlat/2,nlon/2]+180)%360-180
            UCOlon = (lons[-1,-1]+180)%360-180
            LCOlat = lats[nlat/2,nlon/2]
            UCOlat = lats[-1,-1]
            lonstart = nlon/2
            lonend = None
            latstart = nlat/2
            latend = None
        elif bounds=='CONUS':
            if(np.min((lons+180)%360-180)<=CONUS_BOUNDS[0] and np.max((lons+180)%360-180)>=CONUS_BOUNDS[1] and np.min(lats)<=CONUS_BOUNDS[2] and np.max(lats)>=CONUS_BOUNDS[3]):
                LCOlon = lons[np.abs(((lons+180)%360-180)-CONUS_BOUNDS[0]).argmin()]
                UCOlon = lons[np.abs(((lons+180)%360-180)-CONUS_BOUNDS[1]).argmin()]
                LCOlat = lats[np.abs(lats-CONUS_BOUNDS[2]).argmin()]
                UCOlat = lats[np.abs(lats-CONUS_BOUNDS[3]).argmin()]
                lonstart = 0
                lonend = None
                latstart = 0
                latend = None
        else:
            # If bounds argument is not valid. Errors out and gives list of valid bounds arguments
            raise ValueError("BOUNDS PARAMETER: "+str(bounds)+" IS UNKNOWN. ACCEPTABLE BOUNDS PARAMETERS ARE: Full, SW, SE, NW, NE, CONUS")
    # If lat/lon corners are given. Use them to created the bounding grid.
    elif LCOlon and LCOlat and UCOlon and UCOlat:
        lons2 = (lons+180)%360-180
        if LCOlon>=180:
            LCOlon = (LCOlon+180)%360-180
        if UCOlon>=180:
            UCOlon = (UCOlon+180)%360-180
        dists1 = np.sqrt((lons2-LCOlon)**2+(lats-LCOlat)**2)
        idx1 = np.unravel_index(dists1.argmin(),lons2.shape)
        dists2 = np.sqrt((lons2-UCOlon)**2+(lats-UCOlat)**2)
        idx2 = np.unravel_index(dists2.argmin(),lons2.shape)
        lonstart = idx1[1]
        lonend =  idx2[1]
        latstart = idx1[0]
        latend = idx2[0]
    #----------------------------------------------------
    # Gather input variables for call to displaymap
    #----------------------------------------------------
    data = data_info[:]
    # Create title for plot
    var = variable.split('_')[0]
    title = var+' forecast from '+str(time/100)+' '+str(time%100)+'Z'
    # Desired data to be plotted is pulled from data array based on desired plot type (grid or station)
    # And a call to displaymap is made based on all input parameters
    if plot_type=='grid':
        iLa = data.shape.index(nlat)
        data = np.rollaxis(data,iLa,0)
        iLo = data.shape.index(nlon)
        data = np.rollaxis(data,iLo,1)
        ile = data.shape.index(len(leads))
        data = np.rollaxis(data,ile,2)
        inds = list(range(0,len(data.shape)))
        iother = [i for i in inds if i != iLa and i != iLo and i != ile]
        idx = [slice(latstart,latend),slice(lonstart,lonend),ilead]+[slice(0,1)]*(len(S)-3)
        D = np.squeeze(data[idx])
        levels = getlevels(Thresh,D)
        displaymap(D,iproj=proj,LCOlon=LCOlon,LCOlat=LCOlat,UCOlon=UCOlon,UCOlat=UCOlat,lon=lon_0,lat=lat_0,levels=levels,title=title,**kwargs)
    if plot_type=='station':
        D = np.squeeze(data[itime,:,0])
        levels = getlevels(Thresh,D)
        displaymap(D,iproj=proj,LCOlon=LCOlon,LCOlat=LCOlat,UCOlon=UCOlon,UCOlat=UCOlat,lon=lon_0,lat=lat_0,levels=levels,statlons=LONS,statlats=LATS,title=title,**kwargs)



def displaymap(data, filename=None, iproj=4,LCOlon=-127, LCOlat=19, UCOlon=-59, UCOlat=54,lon=-95,lat=25,grid='Fill',statlons=None,statlats=None,stations=True,levels=None,title=None):
    '''
    Displaymap takes input data and projection information to display data on a geographical map

        Inputs are:
           Data: An array of data to be plotted. The dimensions must match the desired lat and lon grid.

           filename: If set, resulting image will be saved as a .png file. If None, resulting image will
                     be displayed. Default is None.

           iproj: an integer value related to the grid projection from a grib gds. The integer is read
                  into a dictionary to determine the exact projection to plot.
                  Default is 3 = Lambert Conformal Conic

           LCOlon/LCOlat: Lower Corner Longitude and Latitude. The coordinates for the lower left corner
                          of the desired grid. Default: 127W, 19N

           UCOlon/UCOlat: Upper Corner Longitude and Latitude. The coordinates for the upper right corner
                          of the desired grid. Default: 95W, 54N

           lon: A central or reference longitude used by different projections. Default: 95W

           lat: A central or reference latitude used by different projections. Default: 25N

           grid: A value of Fill will create a filled contour plot. A value of Contour will create a
                 regular contour plot. A value of None will create a plot based solely on station data.
                 Note: stations argument must also be 'True' for stations data plot.
                 Default: Fill

           stations: Boolean value. If True with a grid argument value of 'Fill' or 'Contour', data value
                     at point of stations is plotted on grid. If True with a grid argument value of 'None',
                     station data will be plotted. If False, no station data will be plotted. Which stations
                     are plotted is based upon scale of grid. If grid is None, stations must be True.
                     Default: True

           levels: A list of values to use as levels for contours. Also, data below the first value will be
                   masked. Default: An evenly spaced array from data min to data max.

    '''
    #Checks stations and grid arguments for validity
    if not stations and not grid:
        raise ValueError('grid and stations arguments cannot both be empty.')
    proj = projs[str(iproj)]
    print("LCOlon = ",LCOlon, " UCOlon = ", UCOlon, " LCOlat = ", LCOlat, " UCOlat = ", UCOlat)
    #set a "zoom_level" based on the span of lat and lon. zoom_level is used to determine how many stations
    #Would be plotted to reduce oversaturation
    if(UCOlon-LCOlon>=50 or UCOlat-LCOlat>=30):
        zoom_level = 0
    elif(UCOlon-LCOlon>=25 or UCOlat-LCOlat>=15):
        zoom_level = 1
    elif(UCOlon-LCOlon>=12 or UCOlat-LCOlat>=7):
        zoom_level = 2
    elif(UCOlon-LCOlon>=6 or UCOlat-LCOlat>=3):
        zoom_level = 3
    elif(UCOlon-LCOlon<6 or UCOlat-LCOlat<3):
        zoom_level = 4
    logging.info("ZOOM LEVEL = "+str(zoom_level))
    plt.figure(figsize=(14,7))
    #setup Basemap map
    mapplot = Basemap(llcrnrlon=LCOlon,llcrnrlat=LCOlat,urcrnrlon=UCOlon,urcrnrlat=UCOlat,lon_0=lon, lat_0=lat,resolution='l', projection=proj)
    mapplot.drawlsmask(ocean_color='#3333ff',resolution='h')
    mapplot.drawcoastlines()
    mapplot.drawstates()
    mapplot.drawcountries()
    mapplot.fillcontinents(color='grey',lake_color='#3333ff')
    parallels = np.arange(LCOlat,UCOlat+1,(UCOlat-LCOlat)/6)
    meridians = np.arange(LCOlon,UCOlon+1,(UCOlon-LCOlon)/6)
    mapplot.drawparallels(parallels,labels=[False,True,True,False],fmt='%.02f')
    mapplot.drawmeridians(meridians,labels=[True,False,False,True],fmt='%.02f')
    # Get X/Y values of lat/lons
    if grid is not None:
        lons,lats = mapplot.makegrid(data.shape[1],data.shape[0])
        X,Y = mapplot(lons,lats)
    else:
        lons,lats = mapplot.makegrid(data.shape[0],data.shape[0])
        X,Y = mapplot(lons,lats)
    # Create contour levels if not given in arguments
    if levels is None:
        levels=np.arange(np.min(data),np.max(data))
    masked_data = np.ma.masked_array(data,data<=levels[0])
    # Plot data as countours or filled contours based on 'grid' argument
    if grid=='Fill':
        mapplot.contourf(lons,lats,masked_data,levels=levels,latlon=True)
        mapplot.colorbar(size='2.5%',pad='12%')
    elif grid=='Contour':
        levels=levels[::4]
        C = mapplot.contour(lons,lats,data,levels=levels,latlon=True)
        plt.clabel(C,inline=True,fmt='%1.0f',fontsize=10,colors='k')
    # If contour is plotted and stations is True, will plot data values at locations of stations
    if grid=='Fill' or grid=='Contour':
        if stations:
            # Grab station table.
            stationfile = registry.__path__[0]+'/station.tbl'
            statfile = open(stationfile,'r')
            statlons = []
            statlats = []
            # Create list of station lat and lons from station table
            for L in statfile:
                statlons.append(float(re.split('[WE]',re.split(':',L)[7])[1]))
                if 'W' in re.split(':',L)[7]:
                    statlons[-1] = statlons[-1]*-1
                statlats.append(float(re.split('[NS]',re.split(':',L)[6])[1]))
                if 'S' in re.split(':',L)[6]:
                    statlats[-1] = statlats[-1]*-1
            statlatlon = list(zip(statlats,statlons))
            plotstats = []
            plotdata = []
            # Set a skip value based on zoom_level
            statskip = 20-4*zoom_level
            # Determine which stations are within plot bounds
            xmax = mapplot.xmax
            ymax = mapplot.ymax
            xmin = mapplot.xmin
            ymin = mapplot.ymin
            xs,ys = mapplot(statlons,statlats)
            xys = list(zip(xs,ys))
            xy_valid = [xy for xy in xys if xy[0]>xmin and xy[0]<xmax and xy[1]>ymin and xy[1]<ymax]
            for i,xy in enumerate(xy_valid):
                dists = np.sqrt((X-xy[0])**2+(Y-xy[1])**2)
                idx = np.unravel_index(dists.argmin(),data.shape)
                datapoint = data[idx]
                if datapoint>levels[0]:
                    plotstats.append(mapplot(xy[0],xy[1]))
                    plotdata.append(datapoint)
                    # Skip stations based on statskip and then plot value of data at location of station
                    if(len(plotstats)%statskip==0):
                        plt.text(xy[0],xy[1],"{:.3f}".format(datapoint),horizontalalignment='center',verticalalignment='center',weight='bold',fontsize=8,color='w')
    # When grid is none. Data is treated as station data and plotted.
    elif grid is None:
        # Checks to be sure stations is True
        if stations:
            # Checks to be sure lat/lon of station locations is given
            if statlats is None or statlons is None:
                raise ValueError('latitude and/or longitude locations of stations are unknown')
            # Set a skip value based on zoom_level
            statskip = 20-4*zoom_level
            xmax = mapplot.xmax
            ymax = mapplot.ymax
            xmin = mapplot.xmin
            ymin = mapplot.ymin
            xs,ys = mapplot(statlons,statlats)
            xys = list(zip(xs,ys))
            xy_valid, data_valid = [],[]
            # Determine which stations are within plot bounds
            for i,xy in enumerate(xys):
                if (xy[0]>xmin and xy[0]<xmax and xy[1]>ymin and xy[1]<ymax):
                    xy_valid.append(xy),data_valid.append(data[i])
            xy_sort = sorted(xy_valid,key=lambda tup: tup[0])
            data_sort = [d for _,d in sorted(zip(xy_valid,data_valid))]
            dists = np.sqrt((np.array(list(zip(*xy_sort))[0][0:-1])-np.array(list(zip(*xy_sort))[0][1:]))**2+(np.array(list(zip(*xy_sort))[1][0:-1])-np.array(list(zip(*xy_sort))[1][1:]))**2)
            xy_apart = [xy[0] for xy in np.array(xy_sort)[np.argwhere(dists>.5)]]
            data_apart = [d[0] for d in np.array(data_sort)[np.argwhere(dists>.5)]]
            # Plot station values on map, skipping values based on skip value
            for i,xy in enumerate(xy_apart[0::statskip]):
                plt.text(xy[0],xy[1],"{:.3f}".format(data_apart[i]),horizontalalignment='center',verticalalignment='center',weight='bold',fontsize=8,color='w')
        if not stations:
            raise ValueError('stations cannot be False while grid is None.')
    # Place title
    plt.title(title,fontsize=10)
    # If filename is given, then save image. Otherwise, show image
    if filename:
        plt.savefig(filename)
        plt.close()
    else:
        plt.show()


def getlevels(thresh,data):
    # Creates a list of contour levels based on range of data values and provided threshold value(s).
    # If no threshold is given, the max and min values of data are used to create a list of levels.
    # If the given threshold is an integer, use it as the lower bound and use data's max as the
    # upper bound. If threshold is a length 2 list or tuple, use it as the upper and lower bounds.
    # If threshold is a list or tuple of length more than 2, use it as the contour levels as is.
    if not thresh:
        lbound = np.min(data)
        ubound = np.max(data)
        levels = np.arange(lbound,ubound+float(ubound)/10)
    elif isinstance(thresh,int):
        lbound = thresh
        ubound = np.max(data)
        levels = np.arange(lbound,ubound+float(ubound)/10,float(ubound)/10)
    elif isinstance(thresh,list) or isinstance(thresh,tuple):
        if(len(thresh)==2):
            lbound = thresh[0]
            ubound = thresh[-1]
            levels = np.arange(lbound,ubound+float(ubound)/10,float(ubound)/10)
        if(len(thresh)>2):
            levels = list(thresh)
    return levels



projs = {
'0' : 'cyl',
'1' : 'merc',
'2' : 'gnom',
'3' : 'lcc',
'4' : 'cyl',
'5' : 'npstere',
'13' : 'lcc',
'50' : '',
'90' : 'ortho'
}

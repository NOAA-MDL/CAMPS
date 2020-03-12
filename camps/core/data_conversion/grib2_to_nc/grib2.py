#!/usr/bin/env python
import sys
import os
import pygrib
import pdb
import re
import logging
import numpy as np
from datetime import timedelta
import time as modTime
from datetime import datetime

from ....core import Camps_data
from ....core import writer as writer
from ....core import Time as Time
from ....registry import util as yamlutil

"""Module: grib2.py

Methods:
    convert_grib2
    get_projection_data
    get_forecast_hash
    get_levelless_forecast_hash
    sort_by_lead_time
    get_output_filename
    get_fcst_time
    get_PhenomenonTime
    get_LeadTime
    get_ValidTime
    get_ResultTime
    get_ForecastReferenceTime
"""



def convert_grib2(control):
    """ Converts grib2 file messages into Camps Data Objects and writes
    to netCDF.
    """

    #Grab some information from control file
    filename = control['input']
    outpath = control['outpath']
    max_lead_times = control['maximum_lead_hours']

    #Open the grib file
    logging.info("Reading grib file")
    start = modTime.time()
    grbs = pygrib.open(filename)
    end = modTime.time()
    time_tot = end - start
    logging.info("Time to read " + str(filename) + " was " + str(time_tot) + " seconds.")

    # Sort the grib messages by lead time,
    # where each index is a forecast hour (lead time)
    lead_times = sort_by_lead_time(grbs,max_lead_times)

    # Save temporary grb to easily access common information
    grbs.seek(0)
    tmp_grb = grbs.next()

    #---------------------------------------------------------------------------
    # Save grb information that will be shared between variables
    #---------------------------------------------------------------------------

    # Time information
    run_time = tmp_grb.hour
    year = tmp_grb.year
    month = tmp_grb.month

    # Convert to run_time to seconds
    fcst_time = run_time

    # Grid information -- Construct metadata dictionary
    grid_meta_dict = {}
    grid_meta_dict['OM__observedProperty'] = 'projection'
    grid_meta_dict['grid_mapping_name'] = tmp_grb.gridType
    grid_meta_dict['radius'] = tmp_grb.radius
    grid_meta_dict['Lat1'] = tmp_grb.latitudeOfFirstGridPointInDegrees
    grid_meta_dict['Lon1'] = tmp_grb.longitudeOfFirstGridPointInDegrees
    grid_meta_dict['stnd_parallel'] = tmp_grb.LaDInDegrees
    grid_meta_dict['orientation'] = tmp_grb.orientationOfTheGridInDegrees
    grid_meta_dict['Dx'] = tmp_grb.DxInMetres
    grid_meta_dict['Dy'] = tmp_grb.DyInMetres
    grid_meta_dict['Nx'] = tmp_grb.Nx
    grid_meta_dict['Ny'] = tmp_grb.Ny

    # Get the projection x, y data in meters
    x_proj_data, y_proj_data = get_projection_data(tmp_grb)

    #---------------------------------------------------------------------------
    # Loop through each forecast hour
    # Group variable data by leadtime for easy stacking later
    # Create dictionaries containing stacked data and relevant metadata for
    # each variable
    #---------------------------------------------------------------------------
    logging.info("Creating Camps-data objects for variables at each projection")

    # Declare some lists/dictionaries
    all_objs = []  #collection of Camps_data objects
    data_dict = {} #dictionary to hold variable metadata

    # Main loop over maximum possible lead times
    for hour in range(max_lead_times):

        #Get pointer to the variable dictionary at current lead time.
        vars_dict = lead_times[hour]

        #Skip current lead time if there are no grb messages for the hour.
        if vars_dict is None:
            continue

        #Loop through each grb message variable for given forecast hour
        logging.info("Creating variables for lead time:"+str(hour))
        for name, values in vars_dict.iteritems():

            stacked = []  #Array to hold stacked grids for every day
            valid = []  #Holds valid time data
            #Looping over grb message strings for variable (usually just one)
            for grb in values:
                #Add to the validTime array
                valid.append(str(grb.validityDate) +
                             str(grb.validityTime).zfill(4))
                #Add the 2D actual model data
                stacked.append(grb.values)
            stacked = np.dstack(stacked) #stack 3rd dimension (makes variable shape len 3)
            valid = np.array(valid)
            #Save the grb message for use later
            example_grb = values[0]

            #If it's only one cycle, add a 1 dimensional time component
            #I'm not sure this is necessary...doing np.dstack will make stacked
            #3 dimensional.  The only time this would be triggered is if our
            #data was somehow 1D to start...which wouldn't make sense. Remove??
            if len(stacked.shape) == 2:
                new_shape = list(stacked.shape)
                new_shape.append(1)
                stacked = np.reshape(stacked, new_shape)

            #Check to see if we have already encountered the current variable
            if name in data_dict:
                #If we have already seen this variable,
                #append data and time info to dictionary
                data_dict[name]['data'].append(stacked)
                data_dict[name]['lead_time'].append(example_grb.endStep)
                data_dict[name]['valid_time'].append(valid)

            #If we have not encountered variable before, create new dictionary key
            else:
                #Populate dictionary for variable
                data_dict[name] = {
                    'data': [stacked],
                    'lead_time': [example_grb.endStep],
                    'valid_time': [valid],
                    'projection': example_grb.gridType,
                    'example_grb' : example_grb,
                    'units' : example_grb.units,
                    'level_units' : example_grb.unitsOfFirstFixedSurface,
                    'dtype' : np.dtype('float32') #We may want to make this conditional later
                    }

                #Defined at a vertical level or vertical layer
                if  example_grb.topLevel == example_grb.bottomLevel:
                    data_dict[name]['level'] = (example_grb.level,)
                else:
                    data_dict[name]['level'] = (example_grb.topLevel, example_grb.bottomLevel)

                #Defined for a time span or time instant
                if 'lengthOfTimeRange' in example_grb.keys():
                    data_dict[name]['period'] = example_grb.lengthOfTimeRange
                else:
                    data_dict[name]['period'] = 0


    #---------------------------------------------------------------------------
    # Format and Write values to NetCDF file
    #---------------------------------------------------------------------------

    #Get standard dimension names
    dimensions = yamlutil.read_dimensions()
    lat = dimensions['lat']
    lon = dimensions['lon']
    lead_time_dim = dimensions['lead_time']
    time = dimensions['time']
    x_proj = dimensions['x_proj']
    y_proj = dimensions['y_proj']

    #Save first grb msg in collection of grb messages
    values = lead_times[0].values()[0]

    #Iterate over the dictionaries of grb variable information and create
    #objects for each. Stacking and formatting data where necessary.
    for name, grb_dict in data_dict.iteritems():
        example_grb = grb_dict['example_grb']

        #Get a generic name for the variable to instantiate the object
        name = get_levelless_forecast_hash(example_grb)
        logging.info(name)

        #Create object for variable
        obj = Camps_data(name)

        #Check to see if variable is in netcdf.yaml file and thus in db
        if len(obj.metadata) == 0: #if not in db we cannot write -- skip variable
            logging.warning('variable %s not in netcdf.yaml, not writing to file'%(name))
            continue

        # Stack data by lead time
        stacked = grb_dict['data']
        stacked = np.array(stacked)
        stacked = np.moveaxis(stacked,[0,1,2,3],[-3,-2,-1,-4])

        #Convert lead_time to an array in seconds
        lead_time = grb_dict['lead_time']
        lead_time = np.array([x * Time.ONE_HOUR for x in lead_time])

        #Stack the valid_time array -- will be 2D
        valid_time = np.vstack(grb_dict['valid_time'])

        #Loop over valid time array and convert to epoch_time
        for i, arr in enumerate(valid_time):
            for j, val in enumerate(arr):
                valid_time[i, j] = Time.epoch_time(val)
        valid_time = valid_time.astype(int)

        #Add processes to object based on the control file settings
        if control.processes: [ obj.add_process(p) for p in control.processes ]

        #Adding forecast model cycle time to object
        obj.add_fcstTime(fcst_time)

        #Set dimensions of variable data in object
        obj.dimensions = [time, lead_time_dim, y_proj, x_proj]

        #Add projection type to variable metadata
        obj.add_metadata('grid_mapping', grb_dict['projection'])

        #Add Vertical coordinate(s)
        vert_coords = grb_dict['level']
        vert_units = grb_dict['level_units']
        if 'Pa' in vert_units:
            vert_type = 'plev'
        else:
            vert_type = 'elev'

        ### TODO: Find which key codes for the 'cell_method' of the vertical level and add below back
        #if len(vert_coords) > 1:
        #    obj.add_coord(vert_coords[0], vert_coords[1], vert_type)
        #elif len(vert_coords) == 1:
        obj.add_coord(vert_coords[0], vert_type=vert_type)
        #Add units
        obj.metadata['units'] = grb_dict['units']

        if grb_dict['period'] > 0:
            obj.metadata['hours'] = grb_dict['period']

        #Add data to object
        dtype = grb_dict['dtype'] #set data type
        try:
            obj.add_data(stacked)
            obj.change_data_type(dtype)
            all_objs.append(obj) #append the variable object to list of objects
        except:
            logging.warning('not an numpy array')

        #Add PhenomenonTime or PhenomenonTimePeriod
        period = (example_grb.endStep - example_grb.startStep)*Time.ONE_HOUR
        if period > 0:
            phenom_timePd = valid_time-period
            phenom_timePd = np.dstack((phenom_timePd,valid_time))
            ptime = Time.PhenomenonTimePeriod(data=phenom_timePd)
        else:
            ptime = Time.PhenomenonTime(data=valid_time)
        obj.time.append(ptime)

        #Add ResultTime
        rtime = get_ResultTime(values)
        obj.time.append(rtime)

        #Add ForecastReferenceTime
        ftime = get_ForecastReferenceTime(values)
        obj.time.append(ftime)

        #Add ValidTime
        #Will be dimensioned so for each leadtime there is a new valid time
        vstart = np.full(valid_time.shape,ftime.data.copy(),dtype='int')
        vend = valid_time.copy()
        valid_time = np.dstack((vstart, vend))
        vtime = Time.ValidTime(data=valid_time)
        obj.time.append(vtime)

        #Add LeadTime
        ltime = get_LeadTime(lead_time)
        obj.time.append(ltime)

    #Make longitude and latitude variables
    lat = Camps_data('latitude')
    lon = Camps_data('longitude')
    lat.dimensions = ['y', 'x']
    lon.dimensions = ['y', 'x']
    lat_lon_data = tmp_grb.latlons()
    lat.data = lat_lon_data[0]
    lon.data = lat_lon_data[1]
    all_objs.append(lat)
    all_objs.append(lon)

    #Make x and y projection variables
    x_obj = Camps_data('x')
    x_obj.dimensions = ['x']
    x_obj.data = x_proj_data
    all_objs.append(x_obj)

    y_obj = Camps_data('y')
    y_obj.dimensions = ['y']
    y_obj.data = y_proj_data
    all_objs.append(y_obj)

    #Make the grid information a variable
    proj = Camps_data(grid_meta_dict['grid_mapping_name']+'_grid',autofill=False) # Instantiate the object

    #Declare feature of interest
    proj.properties['feature_of_interest'] = True

    #Add metadata dict
    proj.metadata = grid_meta_dict

    #Append object to list of objects
    all_objs.append(proj)

    outfile = outpath + get_output_filename(year, month, run_time)
    writer.write(all_objs, outfile, write_to_db=True)


def get_projection_data(grb):
    """Retrieves the projection data from grb"""

    x_proj = np.zeros(grb.Nx)
    y_proj = np.zeros(grb.Ny)

    prev_val = 0
    for i in range(grb.Nx):
        x_proj[i] = prev_val
        prev_val = prev_val + grb.DxInMetres

    prev_val = 0
    for i in range(grb.Ny):
        y_proj[i] = prev_val
        prev_val = prev_val + grb.DyInMetres

    return (x_proj,y_proj)


def get_forecast_hash(grb):
    """Returns a semi-unique identifier, including vertical level
    information, for each variable.
    """

    #Exception of variable defined over a time period.
    if 'lengthOfTimeRange' in grb.keys():
        fcst_hash = str(grb.name) + '_' \
            + str(grb.lengthOfTimeRange) + 'hr' + '_' \
            + str(grb.stepTypeInternal) + '_'\
            + str(grb.level)
        return fcst_hash

    #Exception of variable defined over a vertical layer.
    if grb.name == 'Volumetric soil moisture content':
        fcst_hash = str(grb.name) + '_' \
            + str(grb.stepTypeInternal) + '_'\
            + str(grb.scaledValueOfFirstFixedSurface) + '-'\
            + str(grb.scaledValueOfSecondFixedSurface)
        return fcst_hash

    #Exception of variable with unknown name.
    if grb.name == 'unknown':
        logging.warning("'Unknown' found")

    #Standard hash name
    fcst_hash = str(grb.name) + '_' \
        + str(grb.stepTypeInternal) + '_'\
        + str(grb.level)
    return fcst_hash


def get_levelless_forecast_hash(grb):
    """Returns a semi-unique identifier without any vertical level
    information for each variable.
    """

    #Exception of variable defined over a time period.
    if 'lengthOfTimeRange' in grb.keys():
        fcst_hash = str(grb.name) + '_' \
            + str(grb.lengthOfTimeRange) + 'hr' + '_' \
            + str(grb.stepTypeInternal)
        return fcst_hash

    #Exception of variable defined over a vertical layer.
    if grb.name == 'Volumetric soil moisture content':
        fcst_hash = str(grb.name) + '_' \
            + str(grb.stepTypeInternal) + '_'\
            + str(grb.scaledValueOfFirstFixedSurface) + '-'\
            + str(grb.scaledValueOfSecondFixedSurface)
        return fcst_hash

    #Exception of variable with unknown name.
    if grb.name == 'unknown':
        logging.warning('Unknown found')

    # Standard levelless hash name
    fcst_hash = str(grb.name) + '_' \
        + str(grb.stepTypeInternal)

    return fcst_hash


def sort_by_lead_time(grbs, max_lead_times):
    """Sort a collection of gribs by lead time.
    Returns array where each index represents the forecast hour.
    Each array index contains a dictionary representing
    all variables for each lead time.
    Each dictionary entry contains an array of grbs.
    """

    # Time processing through this code.
    start = modTime.time()

    # Init lead_time array
    lead_times = [None] * (max_lead_times + 1)
    logging.info("organizing grbs into lead times.")
    for i,grb in enumerate(grbs):
        # If the grb forecast time is greater than the set max lead time then we skip
        # otherwise the program fails
        # if grb.forecastTime > max_lead_times:
        if grb.endStep > max_lead_times:
            logging.warning('grb forecastTime greater than max lead time')
            continue

        if i % 1000 == 0:
            logging.debug('Sorted' + str(i) + "grb records")

        # Initialize dictionary at forecast hour if necessary
        if lead_times[grb.endStep] is None:
            lead_times[grb.endStep] = {}

        # fcst_hash is a way to find related grbs. e.g. group all wind speeds at 500mb.
        fcst_hash = get_forecast_hash(grb)

        # Pull out the grb dictionary at current lead time.
        # vars_dict is a ptr to a lead_times dict
        vars_dict = lead_times[grb.endStep]

        # Initialize new variable dict if it's the first variable at this lead time.
        if fcst_hash not in vars_dict:
            vars_dict[fcst_hash] = [grb]
        else:
            vars_dict[fcst_hash].append(grb)

    end = modTime.time() #Note time process ended.
    logging.info("Elapsed time to sort: " + str(end-start) + "seconds")

    return lead_times


def get_output_filename(year, month, run_time):
    """Returns the netcdf filename of gfs model data"""

    year = str(year)
    month = str(month).zfill(2)
    run_time= str(run_time).zfill(2)

    return 'gfs00' + year + month + run_time + '.nc'


def get_fcst_time(fcst_time_str):
    """Returns only the forecast hour from the grib string.
    Also returns boundedTime information if it exists, assuming
    that it consists of two entries: start and end time.
    """

    matches = re.findall(r'\d+', fcst_time_str)
    if len(matches) == 0:
        raise IOError("fcst_time_str doesn't contain a numbered hour")
    if len(matches) > 3:
        raise IOError("fcst_time_str contains too many numbers")

    if len(matches) == 1:
        bounded = False
        return (bounded, matches[0])

    if len(matches) == 2:
        bounded = True
        return (bounded, matches[1])


def get_PhenomenonTime(grbs, deep_check=False):
    """Get the Phenomenon Times for a collection of related grbs"""

    #Not yet executed.
    #if deep_check:
    #    #Search all grbs to ensure the stride is consistent and dates are in order
    #    pass

    start_date = str(grbs[0].dataDate)
    start_hour = str(grbs[0].hour).zfill(2)
    end_date = str(grbs[-1].dataDate)
    end_hour = str(grbs[-1].hour).zfill(2)

    #lead time or forecast projection
    ftime = timedelta(hours=grbs[0].endStep)

    start = Time.str_to_datetime(start_date + start_hour)
    end = Time.str_to_datetime(end_date + end_hour)
    start = start + ftime
    end = end + ftime
    stride = Time.ONE_DAY

    return Time.PhenomenonTime(start_time=start, end_time=end, stride=stride)


def get_LeadTime(lead_time_data, deep_check=False):
    """Get the Lead Times from a collection of related grbs"""

    return Time.LeadTime(data=lead_time_data)


def get_ValidTime(grbs, deep_check=False):
    """Get the Valid Times for a collection of related grbs"""

    #Refer to grb attribute: validityDate and validityTime
    start_date = str(grbs[0].dataDate)
    start_hour = str(grbs[0].hour).zfill(2)
    end_date = str(grbs[-1].dataDate)
    end_hour = str(grbs[-1].hour).zfill(2)

    start = start_date + start_hour
    end = end_date + end_hour
    stride = Time.ONE_DAY
    #offset here is the lead time
    offset = timedelta(seconds=(grbs[0].endStep * Time.ONE_HOUR))

    return Time.ValidTime(start_time=start, end_time=end, stride=stride, offset=offset)


def get_ResultTime(grbs, deep_check=False):
    """Get the Result Times for a collection of related grbs"""

    start_date = str(grbs[0].dataDate)
    start_hour = str(grbs[0].hour).zfill(2)
    end_date = str(grbs[-1].dataDate)
    end_hour = str(grbs[-1].hour).zfill(2)

    start = start_date + start_hour
    end = end_date + end_hour
    stride = Time.ONE_DAY

    return Time.ResultTime(start_time=start, end_time=end, stride=stride)


def get_ForecastReferenceTime(grbs, deep_check=False):
    """Get the ForecastReference Times for a collection of related grbs"""

    #Not yet executed.
    #if deep_check:
    #    # Search all grbs to ensure the stride is consistent and dates are in order
    #    pass

    start_date = str(grbs[0].dataDate)
    start_hour = str(grbs[0].hour).zfill(2)
    end_date = str(grbs[-1].dataDate)
    end_hour = str(grbs[-1].hour).zfill(2)

    start = start_date + start_hour
    end = end_date + end_hour
    stride = Time.ONE_DAY

    return Time.ForecastReferenceTime(start_time=start, end_time=end, stride=stride)

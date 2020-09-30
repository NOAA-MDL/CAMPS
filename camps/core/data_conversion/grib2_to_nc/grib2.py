from datetime import datetime,timedelta
import sys
import os
import pygrib
import pyproj
import pdb
import re
import logging
import numpy as np
import time

from ....core import Camps_data
from ....core import writer
from ....core import Time
from ....registry import util as yamlutil

"""Module: grib2.py

Methods:
    convert_grib2
    get_projection_data
    get_forecast_hash
    get_levelless_forecast_hash
    sort_by_lead_time
"""


GRIB2_MAXIMUM_LEAD_HOURS = 400


def convert_grib2(control):
    """ Converts grib2 file messages into Camps Data Objects and writes
    to netCDF.
    """

    #Grab some information from control file
    filename = control['input']
    output = control['output']

    #Open the grib file
    logging.info("Reading grib file")
    start = time.time()
    grbs = pygrib.open(filename)
    end = time.time()
    time_tot = end - start
    logging.info("Time to read " + str(filename) + " was " + str(time_tot) + " seconds.")

    # Sort the grib messages by lead time,
    # where each index is a forecast hour (lead time)
    lead_times = sort_by_lead_time(grbs,GRIB2_MAXIMUM_LEAD_HOURS)

    # Save temporary grb to easily access common information
    grbs.seek(0)
    tmp_grb = next(grbs)

    #---------------------------------------------------------------------------
    # Save grb information that will be shared between variables
    #---------------------------------------------------------------------------

    # Time information
    run_time = tmp_grb.hour
    year = tmp_grb.year
    month = tmp_grb.month

    #############################################################################
    # Set up time array
    rstart = control['start']
    rend = control['end']
    dates = np.arange(datetime.strptime(rstart, '%Y%m%d%H%M'),datetime.strptime(rend, '%Y%m%d%H%M') + timedelta(days=1),timedelta(days=1))
    dates_str = [d.astype(datetime).strftime('%Y%m%d') for d in dates]
    full_start = rstart[0:8]+str(run_time).zfill(2)
    full_end = rend[0:8]+str(run_time).zfill(2)
    #############################################################################

    # Convert to run_time to seconds
    fcst_time = run_time

    # Grid information -- Construct metadata dictionary
    grid_meta_dict = {}
    if tmp_grb.gridType == "lambert":
        isProjected = True
        dx = tmp_grb.Dx/1000.0
        dy = tmp_grb.Dy/1000.0
        grid_meta_dict['OM__observedProperty'] = 'projection'
        grid_meta_dict['grid_mapping_name'] = "lambert_conformal_conic" # CF-conventions name
        grid_meta_dict['standard_parallel'] = tmp_grb.LaDInDegrees
        grid_meta_dict['longitude_of_central_meridian'] = tmp_grb.LoVInDegrees
        grid_meta_dict['latitude_of_projection_origin'] = tmp_grb.LaDInDegrees
    elif tmp_grb.gridType == "mercator":
        isProjected = True
        dx = tmp_grb.Di/1000.0
        dy = tmp_grb.Dj/1000.0
        grid_meta_dict['OM__observedProperty'] = 'projection'
        grid_meta_dict['grid_mapping_name'] = "mercator" # CF-conventions name
        grid_meta_dict['standard_parallel'] = tmp_grb.LaDInDegrees
        grid_meta_dict['longitude_of_projection_origin'] = tmp_grb.projparams['lon_0']
        grid_meta_dict['scale_factor_at_projection_origin'] = 1
    elif tmp_grb.gridType == "polar_stereographic":
        isProjected = True
        dx = tmp_grb.Dx/1000.0
        dy = tmp_grb.Dy/1000.0
        grid_meta_dict['OM__observedProperty'] = 'projection'
        grid_meta_dict['grid_mapping_name'] = "polar_stereographic" # CF-conventions name
        grid_meta_dict['straight_vertical_longitude_from_pole'] = tmp_grb.orientationOfTheGridInDegrees
        grid_meta_dict['latitude_of_projection_origin'] = 90.0
        grid_meta_dict['standard_parallel'] = tmp_grb.LaDInDegrees
        grid_meta_dict['scale_factor_at_projection_origin'] = 1
    elif tmp_grb.gridType == "regular_ll":
        isProjected = False
        grid_meta_dict['OM__observedProperty'] = 'projection'
        grid_meta_dict['grid_mapping_name'] = "latitude_longitude" # CF-conventions name


    # Get the projection x, y data in meters
    if isProjected:
        projstring,x_proj_data,y_proj_data = get_projection_data(tmp_grb)
        grid_meta_dict['PROJ_string'] = projstring

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
    for hour in range(GRIB2_MAXIMUM_LEAD_HOURS):

        #Get pointer to the variable dictionary at current lead time.
        vars_dict = lead_times[hour]

        #Skip current lead time if there are no grb messages for the hour.
        if vars_dict is None:
            continue

        #Loop through each grb message variable for given forecast hour
        logging.info("Creating variables for lead time:"+str(hour))
        for name, values in vars_dict.items():
            valid_dt = []  #Holds valid time data

            ##################################################################
            # Create stacked array full of missing data
            stacked = [np.full((tmp_grb.Ny,tmp_grb.Nx),9999.0) for t in range(len(dates_str))]

            # Get the leadtime we are on currently
            lead = values[0].endStep

            # Loop over days and create the actual full date value with time added for current leadtime
            dates_dt = []
            for d in dates_str:
                new_date_dt = datetime.strptime(d,'%Y%m%d') + timedelta(hours=lead)
                dates_dt.append(new_date_dt.strftime('%Y%m%d%H%M'))
            dates_dt = np.array(dates_dt)

            # Get the datetime strings where there is real data
            for grb in values:
                valid_dt.append(str(grb.validityDate) +
                             str(grb.validityTime).zfill(4))
            #Get indices where real times matc our expected times
            valid = []
            indices = []
            valid_values = []
            for i,v in enumerate(valid_dt):
                index = np.where(v == dates_dt)[0]
                if len(index) == 0:
                    continue
                valid.append(v)
                indices.append(index[0])
                valid_values.append(values[i])

            #indices = [np.where(v == dates_dt)[0] for v in valid]

            # Fill in stacked array based on these indices
            for i,v in enumerate(valid_values):
                stacked[indices[i]] = v.values
            ###################################################################

            stacked = np.dstack(stacked) #stack 3rd dimension (makes variable shape len 3)
            #Save the grb message for use later
            example_grb = valid_values[0]

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
                data_dict[name]['valid_time'].append(dates_dt)

            #If we have not encountered variable before, create new dictionary key
            else:
                #Populate dictionary for variable
                data_dict[name] = {
                    'data': [stacked],
                    'lead_time': [example_grb.endStep],
                    'valid_time': [dates_dt],
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
                if 'lengthOfTimeRange' in list(example_grb.keys()):
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
    nctime = dimensions['time']
    x_proj = dimensions['x_proj']
    y_proj = dimensions['y_proj']

    #Iterate over the dictionaries of grb variable information and create
    #objects for each. Stacking and formatting data where necessary.
    for name, grb_dict in data_dict.items():
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
        obj.dimensions = [nctime, lead_time_dim, y_proj, x_proj]

        # Add "grid_mapping" attribute. NOTE: The attribute value must be the variable
        # name of the grid mapping variable.
        obj.add_metadata('grid_mapping', grid_meta_dict['grid_mapping_name']+'_grid')

        #Add Vertical coordinate(s)
        vert_coords = grb_dict['level']
        vert_units = grb_dict['level_units']
        if 'Pa' in vert_units:
            vert_type = 'plev'
        else:
            vert_type = 'elev'
        obj.add_coord(vert_coords[0], vert_type=vert_type)

        #Add units
        obj.metadata['units'] = grb_dict['units']

        #Add period info
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
        rtime = Time.ResultTime(start_time=full_start, end_time=full_end, stride=Time.ONE_DAY)
        obj.time.append(rtime)

        #Add ForecastReferenceTime
        ftime = Time.ForecastReferenceTime(start_time=full_start, end_time=full_end, stride=Time.ONE_DAY)
        obj.time.append(ftime)

        #Add ValidTime
        #Will be dimensioned so for each leadtime there is a new valid time
        vstart = np.full(valid_time.shape,ftime.data.copy(),dtype='int')
        vend = valid_time.copy()
        valid_time = np.dstack((vstart, vend))
        vtime = Time.ValidTime(data=valid_time)
        obj.time.append(vtime)

        #Add LeadTime
        ltime = Time.LeadTime(data=lead_time)
        #ltime = get_LeadTime(lead_time)
        obj.time.append(ltime)

    # Make longitude and latitude variables
    lat = Camps_data('latitude')
    lon = Camps_data('longitude')
    lat.dimensions = ['y', 'x']
    lon.dimensions = ['y', 'x']
    lat_lon_data = tmp_grb.latlons()
    lat.data = lat_lon_data[0]
    lon.data = np.where(lat_lon_data[1]>180.0,-1.*(360.-lat_lon_data[1]),lat_lon_data[1])
    all_objs.append(lat)
    all_objs.append(lon)

    # Make x and y projection variables
    if isProjected:
        x_obj = Camps_data('x')
        x_obj.dimensions = ['x']
        x_obj.add_metadata('grid_spacing',dx)
        x_obj.data = x_proj_data
        all_objs.append(x_obj)

        y_obj = Camps_data('y')
        y_obj.dimensions = ['y']
        y_obj.add_metadata('grid_spacing',dy)
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

    writer.write(all_objs, output, write_to_db=True)


def get_projection_data(grb):
    """Retrieves the projection data from grb"""

    # Use pyproj parameters from pygrib
    projstring = ""
    for k,v in grb.projparams.items():
        projstring+="+"+k+"="+str(v)+" "
    p = pyproj.Proj(projstring)
    latslons = grb.latlons()
    x,y = p(latslons[1],latslons[0])
    x_proj = x[0,:]
    y_proj = y[:,0]
    projstring+="+x_0="+str(abs(x[0,0]))+" +y_0="+str(abs(y[0,0]))
    del x,y
    return projstring,x_proj,y_proj


def get_forecast_hash(grb):
    """Returns a semi-unique identifier, including vertical level
    information, for each variable.
    """

    #Exception of variable defined over a time period.
    if 'lengthOfTimeRange' in list(grb.keys()):
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
    if 'lengthOfTimeRange' in list(grb.keys()):
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


def sort_by_lead_time(grbs, GRIB2_MAXIMUM_LEAD_HOURS):
    """Sort a collection of gribs by lead time.
    Returns array where each index represents the forecast hour.
    Each array index contains a dictionary representing
    all variables for each lead time.
    Each dictionary entry contains an array of grbs.
    """

    # Time processing through this code.
    start = time.time()

    # Init lead_time array
    lead_times = [None] * (GRIB2_MAXIMUM_LEAD_HOURS + 1)
    logging.info("organizing grbs into lead times.")
    for i,grb in enumerate(grbs):
        # If the grb forecast time is greater than the set max lead time then we skip
        # otherwise the program fails
        # if grb.forecastTime > GRIB2_MAXIMUM_LEAD_HOURS:
        if grb.endStep > GRIB2_MAXIMUM_LEAD_HOURS:
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

    end = time.time() #Note time process ended.
    logging.info("Elapsed time to sort: " + str(end-start) + "seconds")

    return lead_times

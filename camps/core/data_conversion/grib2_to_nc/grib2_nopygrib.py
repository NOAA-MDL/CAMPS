#!/usr/bin/env python

# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
import os
import struct
import sys
import time as modTime

# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
file_dir = os.path.dirname(os.path.realpath(__file__))
relative_path = "/.."
path = os.path.abspath(file_dir + relative_path)
sys.path.insert(0, path)

from core.Wisps_data import Wisps_data
from datetime import timedelta
import core.writer as writer
import core.Time as Time
import registry.util as yamlutil
import logging
import ncepgrib2
import numpy as np
import pdb


# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
max_lead_times = 400

# ----------------------------------------------------------------------------------------
# Define GRIB2 table 4.4 - Indicator of Unit of Time Range.  Here the dictionary keys are
# the code values and values of scale factors to resolve back to units of hours.
#
# GRIB2 Table 4.4 Defined here:
# http://www.nco.ncep.noaa.gov/pmb/docs/grib2/grib2_table4-4.shtml
# ----------------------------------------------------------------------------------------
_grib2_table_4_4 = { 0: 60.,
                     1: 1.,
                     2: float(1.0/24.0),
                     3: float(1.0/720.0),
                     4: float(1.0/(365.0*24.0)),
                     5: float(1.0/(10.0*365.0*24.0)),
                     6: float(1.0/(30.0*365.0*24.0)),
                     7: float(1.0/(100.0*365.0*24.0)),
                     8: 1.,
                     9: 1.,
                     10: 3.,
                     11: 6.,
                     12: 12.,
                     13: 3600. }
for n in range(14,256):
    _grib2_table_4_4[n] = 1.

# ----------------------------------------------------------------------------------------
# Function: process_control_file
# ----------------------------------------------------------------------------------------
def process_control_file(control=None):
    """Reads grib2 files, changes the map projection and
    grid extent, and packages the gribs into a single grib2 file
    """
    # Read grib control file.
    # If the configuration--a dictionary--is
    # not passed in as an argument, then use the default control file.
    if control is None:
        control = yamlutil.read_grib2_control()

    # Read parameters from control
    ctrl_log = control["log"]
    ctrl_debuglevel = control["debug_level"]
    ctrl_input = control["input"]
    ctrl_output = control["output"]
    # [FUTURE] ctrl_interpolate["interpolate"] # True or False

    # Check if input strings are directories or files. Handle Accordingly
    input_expanded = []
    logging.debug("CONTROL INPUT: ")
    for i in ctrl_input:
        logging.debug(i)
        if os.path.isdir(i):
            for dirpath, dirnames, filenames in os.walk(i):
                input_expanded.extend(map(lambda f: dirpath+f,filenames))
        if os.path.isfile(i):
            input_expanded.append(i)

    # Now that be have all input files list, lets test to see if they are GRIB2 file.
    # For this we will read the first 16 bytes of each file.
    input_expanded_filtered = []
    for f in input_expanded:
        with open(f,"rb") as fo:
            ctemp = "".join(struct.unpack("cccc",fo.read(4)))
            fo.seek(7)
            ctemp += "".join(str(struct.unpack("b",fo.read(1))[0]))
            if ctemp == "GRIB2":
                input_expanded_filtered.append(f)

    # Write all input files to log
    for f in input_expanded_filtered:
        logging.info("INPUT GRIB2 FILE: "+f)

    return input_expanded_filtered

# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
def read_grib2_match_file(control=None):
    if control:
	matchfile = yamlutil.get_config_path(control['grib2_match_file'])
        with open(matchfile,"r") as fo:
            matchlist = fo.read().splitlines()
    else:
        pass # FOR NOW
    return matchlist

# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
def construct_gumi(g2in):
    _a = str(g2in.identification_section[0])
    _b = str(g2in.identification_section[1])
    _c = str(g2in.product_definition_template[4])
    _d = str(g2in.discipline_code)
    _e = str(g2in.product_definition_template_number)
    _f = str(g2in.product_definition_template[0])
    _g = str(g2in.product_definition_template[1])
    _h = str(g2in.product_definition_template[9])
    _i = str(g2in.product_definition_template[10])
    _j = str(g2in.product_definition_template[11])
    _k = str(g2in.product_definition_template[12])
    _l = str(g2in.product_definition_template[13])
    _m = str(g2in.product_definition_template[14])
    _n = str(g2in.product_definition_template[7])
    _o = str(g2in.product_definition_template[8])

    _gumi = "-".join([_a,_b,_c,_d,_e,_f,_g,_h,_i,_j,_k,_l,_m,_n,_o])

    return  _gumi

# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
def reduce_gumi(gumi):
    return "-".join(gumi.split("-")[3:13])

# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
def get_wisps_name(lookup_table, name):
    """
    Given a lookup table (dict) and key, return a key in the netcdf.yaml file.
    """
    try:
        name = lookup_table[name]
        # unknown seemingly randomly appears.
        if 'unknown' in name:
            raise ValueError("unknown is the name of grb. Exiting")
    except:
        logging.warning(str(name) + 'not in grib2 lookup table')
    return name


#-----------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------
def get_projection_data(grb):
    """
    Given a grib2 message, create the projection data for the grid.
    """

    nx = grb.points_in_x_direction
    ny = grb.points_in_y_direction
    dx = grb.gridlength_in_x_direction
    dy = grb.gridlength_in_y_direction
    x_proj = np.zeros(nx)
    y_proj = np.zeros(ny)
    prev_val = 0
    for i in range(nx):
        x_proj[i] = prev_val
        prev_val = prev_val + dx
    prev_val = 0
    for i in range(ny):
        y_proj[i] = prev_val
        prev_val = prev_val + dy
    return x_proj, y_proj

# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
def extract_grib2(grib2files,matchlist):
    """Extract GRIB2 Messages for archiving."""

    logging.info("Number of records in GRIB2 archive match list = "+str(len(matchlist)))

    # Iterate through all input GRIB2 Files, extract Messages to archive.
    grbs_filtered = []
    for g2f in grib2files:
        logging.info("Reading Input GRIB2 File: "+g2f)
        ngrib = len(grbs_filtered)
        start = modTime.time()
        grbs = ncepgrib2.Grib2Decode(g2f)
        end = modTime.time()
        time_tot = end - start
        logging.info("\tTime to read " + str(g2f) + " was " + str(time_tot) + " seconds.")

        # Make sure grbs is a list
        if not isinstance(grbs,list): grbs=[grbs]

        # Get GRIB2 Unique Message Identifier and reduce it
        gumi_list = []
        for g2 in grbs:
            gumi_list.append(reduce_gumi(construct_gumi(g2)))

        # Filter
        for gumi,g2 in zip(gumi_list,grbs):
            try:
                idx = matchlist.index(gumi)
                grbs_filtered.append(g2)
            except (ValueError):
                #print "Ignoring this GRIB2 Message.  Not Archived."
                pass

        logging.info("\tNumber of GRIB2 records matched = "+str(len(grbs_filtered)-ngrib))

    logging.info("Total Number of GRIB2 records matched = "+str(len(grbs_filtered)))
    return grbs_filtered

# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
def convert_grib2(control,grb2):
    """
    Converts a list of ncepgirb2.Grib2Messgage instances (i.e. GRIB2 records) into Wisps
    Data and writes to NetCDF.
    """

    # Get lead times
    lead_time_range = control['lead_time']
    print lead_time_range
    lead_times = range(lead_time_range[0],lead_time_range[1]+1,lead_time_range[2])
    print lead_times

    all_objs = []  # Collection of Wisps_data objects
    logging.info("Creating Wisps-data objects for variables at each projection")

    # Read dimensions
    dimensions = yamlutil.read_dimensions()

    # Loop through each forcast hour.
    # Will typically only do something every third forecast hour, but is not
    # limited.
    data_dict = {}
    for nlead,hour in enumerate(lead_times):

        # Loop through each variable in every forecast hour
        print "Creating variables for lead time:", hour
        for n,grb in enumerate(grb2):

            # At the first lead time, first GRIB2 Message, get the lats and lons and grid x, y
            if nlead == 0 and n == 0:
                lats,lons = grb.grid()
                x_proj_data, y_proj_data = get_projection_data(grb)

                # Add latitude to WISPS data object
                latobj = Wisps_data('latitude')
                latobj.data = lats
                latobj.dimensions = ['y','x']
                all_objs.append(latobj)

                # Add longitude to WISPS data object
                lonobj = Wisps_data('longitude')
                lonobj.data = lons
                lonobj.dimensions = ['y','x']
                all_objs.append(lonobj)

                # Add x to WISPS data object
                x_obj = Wisps_data('x')
                x_obj.dimensions = ['x']
                x_obj.data = x_proj_data
                all_objs.append(x_obj)

                # Add y to WISPS data object
                y_obj = Wisps_data('y')
                y_obj.dimensions = ['y']
                y_obj.data = y_proj_data
                all_objs.append(y_obj)

                # Add lead_time to WISPS data object
                tobj = Time.LeadTime(data=np.array(lead_times)*60*60)
                all_objs.append(tobj)


                #logging.info("Writing Latitude and Longitude variables to "+control['output'])

            # Get the Init date in YYYYMMDDHH
            grib_init_date = (grb.identification_section[5]*1000000)+\
                             (grb.identification_section[6]*10000)+\
                             (grb.identification_section[7]*100)+\
                             (grb.identification_section[8]*1)

            # Get the lead time in hours.
            if grb.product_definition_template_number == 0:
                grib_lead_time = int(_grib2_table_4_4[grb.product_definition_template[7]]*grb.product_definition_template[8])
            elif grb.product_definition_template_number == 8:
                grib_lead_time = int((_grib2_table_4_4[grb.product_definition_template[7]]*grb.product_definition_template[8])+
                                 (_grib2_table_4_4[grb.product_definition_template[25]]*grb.product_definition_template[26]))
            elif grb.product_definition_template_number == 11:
                grib_lead_time = int((_grib2_table_4_4[grb.product_definition_template[7]]*grb.product_definition_template[8])+
                                 (_grib2_table_4_4[grb.product_definition_template[28]]*grb.product_definition_template[29]))

            # Check if the lead time for this GRIB2 record is what we want to archive.
            # If not, move to the next iteration.
            if grib_lead_time != hour: continue

            #convert lead time to seconds
            fcst_time = grib_lead_time*60*60

	    # Calculate the ValidTime
	    epochtime = Time.epoch_time(str(grib_init_date))
	    valid_time = epochtime + fcst_time


	    # Add phenomenon time
	    phenom_time = valid_time
	    ptime = Time.PhenomenonTime(data=phenom_time)

	    # Add result time 
	    rtime = Time.ResultTime(data=epoch_time)
	    

            # Create a reduced GUMI string (reduced GUMI has no model or lead time info).
            # Then pass the reduced GUMI to Wisp_data for matching for a valid WISPS
            # data object.
            wisps_gumi = reduce_gumi(construct_gumi(grb))
            if wisps_gumi in yamlutil.read_variables():
                obj = Wisps_data(wisps_gumi)
                obj.data = grb.data(fill_value=9999.,masked_array=False)
                obj.dimensions.append('y')
                obj.dimensions.append('x')
                obj.dimensions.append('lead_times')
                obj.add_fcstTime(fcst_time)
		obj.time.append(ptime)
		obj.time.append(rtime)
		if control.processes: [ obj.add_process(p) for p in control.processes ] 
		#pdb.set_trace()
                #NEWobj.add_dimensions('lead_time','lon','lat')
                print obj.standard_name

                # If len all_objs is zero, then we have our first WISPS data object so
                # just append; else we need to try to match the data to an existing
                # WISPS data object.
                if len(all_objs) == 0:
                    all_objs.append(obj)
                else:
                    for nn,o in enumerate(all_objs):
                        if wisps_gumi == o.name:
                            if len(o.data.shape) == 2:
				#pdb.set_trace()
                                o.data = np.expand_dims(o.data,axis=2)
                                o.data = np.dstack((o.data,np.expand_dims(grb.data(fill_value=9999.,masked_array=False),axis=2)))
                            else:
                                o.data = np.dstack((o.data,np.expand_dims(grb.data(fill_value=9999.,masked_array=False),axis=2)))
                            break
                    else:
			all_objs.append(obj)

    # IMPORTANT: At this point, we have a list of WISPS Data objects where each object
    # should have a data attribute array that is 3 dimensional (y,x,lead_time).

    print "SIZE OF ALL_OBJS = ",len(all_objs)
    for ob in all_objs: print ob

    # Test NetCDF file output
    writer.write(all_objs,control['output'])

    exit(0)

# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# RILEY'S CODE BELOW...SOME USEABLE...SOME NOT
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------

    ##
    # Format and Write values to NetCDF file
    ##

    # Get standard dimension names
    dimensions = yamlutil.read_dimensions()
    lat = dimensions['lat']
    lon = dimensions['lon']
    lead_time_dim = dimensions['lead_time']
    time = dimensions['time']
    x_proj = dimensions['x_proj']
    y_proj = dimensions['y_proj']

    x_proj_data, y_proj_data = get_projection_data(tmp_grb)

    #convert to seconds
    fcst_time = run_time
    fcst_time = fcst_time*60*60
    values = lead_times[0].values()[0]
    for name, grb_dict in data_dict.iteritems():
        stacked = grb_dict['data']
        stacked = np.array(stacked)
        stacked = np.swapaxes(stacked, 0, 2)
        stacked = np.swapaxes(stacked, 0, 1)
        lead_time = grb_dict['lead_time']
        lead_time = np.array([x * Time.ONE_HOUR for x in lead_time])
        valid_time = np.vstack(grb_dict['valid_time'])
        for i, arr in enumerate(valid_time):
            for j, val in enumerate(arr):
                valid_time[i, j] = Time.epoch_time(val)

        valid_time = valid_time.astype(int)
        phenom_time = valid_time

        # Now get a generic name
        name = get_levelless_forecast_hash(grb_dict['example_grb'])
        logging.info(name)
        dtype = grb_dict['dtype']
        obj = Wisps_data(name)
        #obj.add_source('GFS')
        obj.add_process('GFSModProcStep1')
        obj.add_process('GFSModProcStep2')
        obj.add_fcstTime(fcst_time)
        obj.dimensions = [y_proj, x_proj, lead_time_dim, time]

        # Add Vertical coordinate(s)
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

        # Add units
        obj.metadata['units'] = grb_dict['units']

        # Add data
        try:
            obj.add_data(stacked)
            obj.change_data_type(dtype)
            all_objs.append(obj)
        except:
            logging.warning('not an numpy array')

        if example_grb.startStep != example_grb.endStep:
            # Then we know it's time bounded
            pass

        # Add PhenomononTime
        #ptime = get_PhenomenonTime(values)
        #obj.time.append(ptime)
        ptime = Time.PhenomenonTime(data=phenom_time)
        obj.time.append(ptime)


        # Add ResultTime
        rtime = get_ResultTime(values)
        obj.time.append(rtime)


        # Add ValidTime
        vstart = valid_time.copy()
        vend = valid_time.copy()
        for i,j in enumerate(vstart[0]):
            vstart[:,i] = rtime.data[i]
        valid_time = np.dstack((vstart, vend))
        vtime = Time.ValidTime(data=valid_time)
        #vtime = get_ValidTime(values)
        obj.time.append(vtime)

        # Add ForecastReferenceTime
        ftime = get_ForecastReferenceTime(values)
        obj.time.append(ftime)

        # Add LeadTime
        ltime = get_LeadTime(lead_time)
        obj.time.append(ltime)


    all_objs = write_projection_data(all_objs)

    # Make longitude and latitude variables
    lat = Wisps_data('latitude')
    lon = Wisps_data('longitude')
    lat.dimensions = ['y', 'x']
    lon.dimensions = ['y', 'x']
    lat_lon_data = tmp_grb.latlons()
    lat.data = lat_lon_data[0]
    lon.data = lat_lon_data[1]
    all_objs.append(lat)
    all_objs.append(lon)

    # Make x and y projection variables
    x_obj = Wisps_data('x')
    x_obj.dimensions = ['x']
    x_obj.data = x_proj_data
    all_objs.append(x_obj)

    y_obj = Wisps_data('y')
    y_obj.dimensions = ['y']
    y_obj.data = y_proj_data
    all_objs.append(y_obj)

    outfile = outpath + get_output_filename(year, month)
    writer.write(all_objs, outfile, write_to_db=True)

def write_projection_data(all_objs):
    """ Write projection variable and add metadata to all
    other variables reflecting that
    """

    for i in all_objs:
        i.add_metadata('grid_mapping', 'polar_stereographic')
    proj = Wisps_data('polar_stereographic')
    # Make projection variables
    all_objs.append(proj)
    return all_objs


def get_dtype(grb):
    pass


def get_output_filename(year, month):
    """Returns a string representing the netcdf filename of gfs model data"""
    year = str(year)
    month = str(month).zfill(2)
    return 'gfs00' + year + month + '00.nc'


def get_fcst_time(fcst_time_str):
    """
    returns only the forecast hour from the grib string.
    also returns boundedTime information if it exists.
    assumes that bounded Times will have only 2 hours in the string.
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
    if deep_check:
        # Search all grbs to ensure the stride is consistant and dates are in
        # order
        pass
    start_date = str(grbs[0].dataDate)
    start_hour = str(grbs[0].hour).zfill(2)
    end_date = str(grbs[-1].dataDate)
    end_hour = str(grbs[-1].hour).zfill(2)

    ftime = timedelta(hours=grbs[0].forecastTime)

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
    # refer to grb attribute: validityDate and validityTime
    start_date = str(grbs[0].dataDate)
    start_hour = str(grbs[0].hour).zfill(2)
    end_date = str(grbs[-1].dataDate)
    end_hour = str(grbs[-1].hour).zfill(2)

    start = start_date + start_hour
    end = end_date + end_hour
    stride = Time.ONE_DAY
    offset = timedelta(seconds=(grbs[0].forecastTime * Time.ONE_HOUR))
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
    if deep_check:
        # Search all grbs to ensure the stride is consistant and dates are in
        # order
        pass
    start_date = str(grbs[0].dataDate)
    start_hour = str(grbs[0].hour).zfill(2)
    end_date = str(grbs[-1].dataDate)
    end_hour = str(grbs[-1].hour).zfill(2)

    start = start_date + start_hour
    end = end_date + end_hour
    stride = Time.ONE_DAY
    return Time.ForecastReferenceTime(start_time=start, end_time=end, stride=stride)


def get_grbs(grbs):
    """
    Parse the grib headers and return an object with relavent attributes.
    grib keys are:

    'parametersVersion'
    'hundred'
    'globalDomain'
    'GRIBEditionNumber'
    'grib2divider'
    'missingValue'
    'ieeeFloats'
    'section0Length'
    'identifier'
    'discipline'
    'editionNumber'
    'totalLength'
    'sectionNumber'
    'section1Length'
    'numberOfSection'
    'centre'
    'centreDescription'
    'subCentre'
    'tablesVersion'
    'masterDir'
    'localTablesVersion'
    'significanceOfReferenceTime'
    'year'
    'month'
    'day'
    'hour'
    'minute'
    'second'
    'dataDate'
    'julianDay'
    'dataTime'
    'productionStatusOfProcessedData'
    'typeOfProcessedData'
    'selectStepTemplateInterval'
    'selectStepTemplateInstant'
    'stepType'
    'sectionNumber'
    'grib2LocalSectionPresent'
    'sectionNumber'
    'gridDescriptionSectionPresent'
    'section3Length'
    'numberOfSection'
    'sourceOfGridDefinition'
    'numberOfDataPoints'
    'numberOfOctectsForNumberOfPoints'
    'interpretationOfNumberOfPoints'
    'PLPresent'
    'gridDefinitionTemplateNumber'
    'shapeOfTheEarth'
    'scaleFactorOfRadiusOfSphericalEarth'
    'scaledValueOfRadiusOfSphericalEarth'
    'scaleFactorOfEarthMajorAxis'
    'scaledValueOfEarthMajorAxis'
    'scaleFactorOfEarthMinorAxis'
    'scaledValueOfEarthMinorAxis'
    'radius'
    'Nx'
    'Ny'
    'latitudeOfFirstGridPoint'
    'latitudeOfFirstGridPointInDegrees'
    'longitudeOfFirstGridPoint'
    'longitudeOfFirstGridPointInDegrees'
    'resolutionAndComponentFlag'
    'LaD'
    'LaDInDegrees'
    'orientationOfTheGrid'
    'orientationOfTheGridInDegrees'
    'Dx'
    'DxInMetres'
    'Dy'
    'DyInMetres'
    'projectionCentreFlag'
    'scanningMode'
    'iScansNegatively'
    'jScansPositively'
    'jPointsAreConsecutive'
    'alternativeRowScanning'
    'iScansPositively'
    'scanningMode5'
    'scanningMode6'
    'scanningMode7'
    'scanningMode8'
    'gridType'
    'sectionNumber'
    'section4Length'
    'numberOfSection'
    'NV'
    'neitherPresent'
    'productDefinitionTemplateNumber'
    'parameterCategory'
    'parameterNumber'
    'parameterUnits'
    'parameterName'
    'typeOfGeneratingProcess'
    'backgroundProcess'
    'generatingProcessIdentifier'
    'hoursAfterDataCutoff'
    'minutesAfterDataCutoff'
    'indicatorOfUnitOfTimeRange'
    'stepUnits'
    'forecastTime'
    'startStep'
    'endStep'
    'stepRange'
    'stepTypeInternal'
    'validityDate'
    'validityTime'
    'typeOfFirstFixedSurface'
    'unitsOfFirstFixedSurface'
    'nameOfFirstFixedSurface'
    'scaleFactorOfFirstFixedSurface'
    'scaledValueOfFirstFixedSurface'
    'typeOfSecondFixedSurface'
    'unitsOfSecondFixedSurface'
    'nameOfSecondFixedSurface'
    'scaleFactorOfSecondFixedSurface'
    'scaledValueOfSecondFixedSurface'
    'pressureUnits'
    'typeOfLevel'
    'level'
    'bottomLevel'
    'topLevel'
    'paramIdECMF'
    'paramId'
    'shortNameECMF'
    'shortName'
    'unitsECMF'
    'units'
    'nameECMF'
    'name'
    'cfNameECMF'
    'cfName'
    'cfVarNameECMF'
    'cfVarName'
    'ifsParam'
    'genVertHeightCoords'
    'PVPresent'
    'sectionNumber'
    'section5Length'
    'numberOfSection'
    'numberOfValues'
    'dataRepresentationTemplateNumber'
    'packingType'
    'referenceValue'
    'referenceValueError'
    'binaryScaleFactor'
    'decimalScaleFactor'
    'bitsPerValue'
    'typeOfOriginalFieldValues'
    'lengthOfHeaders'
    'sectionNumber'
    'section6Length'
    'numberOfSection'
    'bitMapIndicator'
    'bitmapPresent'
    'sectionNumber'
    'section7Length'
    'numberOfSection'
    'codedValues'
    'values'
    'packingError'
    'unpackedError'
    'maximum'
    'minimum'
    'average'
    'numberOfMissing'
    'standardDeviation'
    'skewness'
    'kurtosis'
    'isConstant'
    'changeDecimalPrecision'
    'decimalPrecision'
    'setBitsPerValue'
    'getNumberOfValues'
    'scaleValuesBy'
    'offsetValuesBy'
    'productType'
    'section8Length'
    """
    forecasts = []
    counter = 0
    for grb in grbs:
        loggin.info(str(counter))
        counter += 1
        grb_info = type('', (), {})()  # Create empty object
        grb_inv = str(grb).split(':')
        grb_info.name = grb_inv[1]
        grb_info.units = grb_inv[2]
        grb_info.projection = grb_inv[3]
        grb_info.coordinate = grb_inv[4]
        grb_info.level = grb_inv[5]
        grb_info.fcst_time = grb_inv[6]
        grb_info.model_run = grb_inv[7]
        grb_info.data = grb.values
        forecasts.append(grb_info)
    return forecasts

# reduce_grib()
# convert_grib2('/scratch3/NCEPDEV/mdl/Riley.Conroy/output/mdl.gfs47.06.pgrb2')

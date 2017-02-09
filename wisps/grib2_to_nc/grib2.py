#!/usr/bin/env python
import sys, os
file_dir = os.path.dirname(os.path.realpath(__file__))
relative_path = "/.."
path = os.path.abspath(file_dir + relative_path)
sys.path.insert(0, path)

from subprocess import call 
from subprocess import Popen
from data_mgmt.Wisps_data import Wisps_data
import data_mgmt.writer as writer
import registry.util as yamlutil
import subprocess
import pygrib
import pdb
import re
import numpy as np

def reduce_grib():
    
    registery_path = yamlutil.CONFIG_PATH
    # Init
    control = yamlutil.read_grib2_control()
  
    wgrib2 = control['wgrib2']
    grbindex = control['grbindex']
    datadir = control['datadir']
    outpath = control['outpath']
    projection = control['projection']
    nonpcp_file = registery_path + control['nonpcp_file']
    pcp_file = registery_path + control['pcp_file']
   
    # projections
    gfs47a, gfs47b, gfs47c = projection.split(" ")
   
    # Find ALL files in the datadir
    files = os.listdir(datadir)

    # Just get the gfs files
    match_string = r'^...\.t\d\dz\.pgrb2\.0p25\.f\d\d\d$'
    files = filter(lambda f: re.match(match_string, f, re.I), files)
    
    # Only get those files that are every third projection time
    files = filter(lambda f: int(f[-3:]) % 3 == 0 and int(f[-3:])<=96, files)

    print "number of files:", files
    forecast_hour = files[0][5:7]
    outfile = outpath + 'mdl.gfs47.'+forecast_hour+'.pgrb2'

    for gfs_file in files:
        infile = datadir + gfs_file
        print infile
        
        PIPE = subprocess.PIPE
        get_inv_cmd = [wgrib2, infile]
        non_pcp_cmd = [wgrib2, infile,                       # Specify infile
                       "-i",                                 # Use Inventory
                       "-new_grid_winds", "grid",            # new_grid wind orientation ('grid' or 'earth')
                       "-new_grid_interpolation", "bilinear",# new_grid interpolation ('bilinear','bicubic','neighbor', or 'budget')
                       "-append",                            # add to existing file if exist
                       "-new_grid", gfs47a, gfs47b, gfs47c,  # new_grid to specifications
                       outfile]
        
        pcp_cmd = [wgrib2, infile,                       # Specify infile
                       "-i",                                 # Use Inventory
                       "-new_grid_winds", "grid",            # new_grid wind orientation ('grid' or 'earth')
                       "-new_grid_interpolation", "budget",# new_grid interpolation ('bilinear','bicubic','neighbor', or 'budget')
                       "-append",                            # add to existing file if exist
                       "-new_grid", gfs47a, gfs47b, gfs47c,  # new_grid to specifications
                       outfile]
        
    #    p1 = Popen(get_inv_cmd, stdout=PIPE)
    #    p2 = Popen(['grep','-f', nonpcp_file],stdin=p1.stdout, stdout=PIPE)
    #    p3 = Popen(non_pcp_cmd, stdin=p2.stdout)
    #    p1.stdout.close()
    #    p2.stdout.close()

        ## OR

        #Do nonPCP
        cmd = " ".join(get_inv_cmd) + " | grep -f "+nonpcp_file+" | " + " ".join(non_pcp_cmd)
        subprocess.check_output(cmd, shell=True)
        cmd = " ".join(get_inv_cmd) + " | grep -f "+pcp_file+" | " + " ".join(pcp_cmd)
        subprocess.check_output(cmd, shell=True)
   
def get_forecast_hash(grb):
    if 'lengthOfTimeRange' in grb.keys():
        fcst_hash = str(grb.name) + '_' \
                + str(grb.lengthOfTimeRange) + 'hr' + '_' \
                + str(grb.stepTypeInternal) + '_'\
                + str(grb.level)
        return fcst_hash

    fcst_hash = str(grb.name) + '_' \
            + str(grb.stepTypeInternal) + '_'\
            + str(grb.level)

    return fcst_hash

def get_lon_lat_data(grb):
    pass
    

def convert_grib2(filename):
    """
    Converts grib file into Wisps Data and writes 
    to netCDF.
    """
    # Load lookup table first
    lookup = yamlutil.read_grib2_lookup()
    # Read Control and take out a few variables
    control = yamlutil.read_grib2_control()
    outpath = control['outpath']

    print "reading grib"
    grbs = pygrib.open(filename)
    # where each index is an hour. So we need the +1 for hour 96
    number_of_forecast_hours = 96 + 1
    fcst_hours = [None] * number_of_forecast_hours
    metadata = {}
    print "organizing grbs into model runs/projection hours"
    for grb in grbs:
        # Initialize dictionary at forecast hour if necessary
        
        if not fcst_hours[grb.forecastTime]:
            fcst_hours[grb.forecastTime] = {}

        fcst_hash = get_forecast_hash(grb)
        #data = grb.values
        
        # Pull out the grb dictionary at the forecast hour
        all_vars = fcst_hours[grb.forecastTime]
        if fcst_hash not in all_vars:
            all_vars[fcst_hash] = [grb]
        else:
            all_vars[fcst_hash].append(grb)

    #pdb.set_trace()
    
    # Temporary grb to grab standard information
    tmp_grb = fcst_hours[0]
    tmp_grb = tmp_grb[tmp_grb.keys()[0]][0]
    lead_time = tmp_grb.hour
    all_objs = [] # Collection of Wisps_data objects
    print "Creating Wisps-data objects for variables at each projection"
    # Will typically only do something every third forecast hour
    for hour in range(number_of_forecast_hours):
        all_vars = fcst_hours[hour]
        if all_vars == None:
            continue
        print hour
        for name,values in all_vars.iteritems():
            # Convert name to the proper wisps name in the db/netcdf.yml
            try:
                name = lookup[name]
            except:
                print 'Warning:', name, 'not in grib2 lookup table'
            stacked = np.array([])
            for grb in values:
                if len(stacked) == 0:
                    stacked = grb.values
                else:
                    stacked = np.dstack((stacked,grb.values))

            obj = Wisps_data(name)
            obj.add_source('GFS')
            obj.add_leadTime(filename[-2:])
            obj.add_metadata('ForecastReferenceTime', hour)
            obj.dimensions = ['lat','lon','time']
            try:
                obj.add_data(stacked) 
                all_objs.append(obj)
            except: 
                print 'not an numpy array'
 
    # Make longitude and latitude variables
    lat = Wisps_data('latitude')
    lon = Wisps_data('longitude')
    lat.dimensions = ['lat','lon']
    lon.dimensions = ['lat','lon']
    lat_lon_data = tmp_grb.latlons()
    lat.data = lat_lon_data
    lon.data = lat_lon_data
    all_objs.append(lat)
    all_objs.append(lon)

    outfile = outpath + get_output_filename()
    writer.write(all_objs, outfile)

def get_output_filename():
    """Returns a string representing the netcdf filename of gfs model data"""
    return 'grbtst.nc'

def convert_grib(filename):
    """
    Converts grib file into Wisps Data
    """
    grbs = pygrib.open(filename)
    pdb.set_trace()
    grbs_info = get_grbs(grbs)
    len(grbs_info)
    i = 1
    tmp_dict = {}
    for fcst in grbs_info:
        fcst_hash = fcst.name + fcst.level
        fcst_hash = fcst.model_run
        if fcst_hash in tmp_dict:
            tmp_dict[fcst_hash] += 1
        else:
            tmp_dict[fcst_hash] = 0
    pdb.set_trace()
    print ""

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
        return (bounded,matches[0])
    if len(matches) == 2:
        bounded = True
        return (bounded, matches[1])

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
        print counter
        counter +=1
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

#reduce_grib()
convert_grib2('/scratch3/NCEPDEV/mdl/Riley.Conroy/output/mdl.gfs47.12.pgrb2')


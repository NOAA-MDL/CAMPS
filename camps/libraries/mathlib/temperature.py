import logging
import os
import sys
import re
import pdb
import metpy.calc as calc
from metpy.units import units
import math
import copy
import numpy as np
import numpy.ma as ma
import operator

from ...core.fetch import *
from ...core.Time import epoch_to_datetime
from ...core import Time as Time
from ...core import Location as Location
from ...core.Camps_data import Camps_data as Camps_data
from ...core import util as util


#Minimum and maximum time zone offset values
TZ_MIN = -10
TZ_MAX = -4


def extreme_temperature_setup(filepaths, time, predictor, station_list=None, station_defs=None):
    """Compute the extreme temperature, either the daytime maximum temperature
    or the nighttime minimum temperature.  The daytime maximum temperature is the
    maximum temperature found in the time window between 7am and 7pm inclusive
    local standard time.  The window for nighttime minimum temperature is between
    7pm and 8am (next day) inclusive local standard time.  The daytime maximum temperature
    is stored at 06Z the next day and the nighttime minimum temperature is stored
    at 18Z that same day.

    Arguments:
        filepaths (list): contains input absolute filepaths.
        time(int): The valid time of the predictor given as the
            number of seconds since January 1, 1970 00Z.
        predictor(Predictor): a Predictor object instantiated prior
            to the call to this function with the metadata fields
            pre-filled.  The metadata contains key/value pairs used
            for enquiring the database.
        station_list (list): list of selected stations.
        station_defs (dictionary): dictionary for stations with values
            containing information about the station like coordinates, etc.

    Returns:
        ExtremeT (numpy.ma): contains the unambiguously determined extreme
            temperature at stations in station_list.
    """

    #method constants are in CAPS.
    #These three may be global.
    HOUR = 60*60
    HOURS_in_DAY = 24
    DAY = HOURS_in_DAY*HOUR

    #Method constants specific to whether the extreme temperature
    #is nighttime minimum or daytime maximum.  We specify the UTC
    #hour at which the variable is stored, the variable name, and
    #the statistical method used.  In addition, we include the start
    #and end of the time window of each variable given in hours of
    #of the day.  Finally, assuming variable values given hourly, we
    #denote the variable data indices for a time zone offset of 0.
    IS_MIN = predictor.search_metadata['property'] == 'NightMinT'
    if IS_MIN:
        HOUR_UTC = 18
        NAME = 'nighttime_minimum_temperature'
        CALCULATION = 'NightMinTempCalc'
        DURATION_METHOD = 'minimum'
        START_LST = 19
        END_LST = 8 #the next day from START_LST.
        I_UTC = [nhours+(START_LST-HOUR_UTC) for nhours in [0, (HOURS_in_DAY-START_LST)+END_LST]]
    else:
        HOUR_UTC = 6
        NAME = 'daytime_maximum_temperature'
        CALCULATION = 'DayMaxTempCalc'
        DURATION_METHOD = 'maximum'
        START_LST = 7
        END_LST = 19 #the same day as in START_LST
        I_UTC = [nhours+(START_LST-HOUR_UTC) for nhours in [0, (END_LST-START_LST)]]

    #Check that the function argument 'time' corresponds to the
    #appropriate hour of the day in UTC for data storage.
    datetime_utc = Time.epoch_to_datetime(time)
    hour_utc = datetime_utc.hour
    minute_utc = datetime_utc.minute
    TIME_CHK = True
    if hour_utc != HOUR_UTC or minute_utc:
        logging.info("Hour of time must be " + str(HOUR_UTC) + "Z")
        SIGN = -1
        TIME_CHCK = False

    #This method is called with a specific model cycle and lead time
    #in mind, even though the data does not depend on either.  We check
    #here if that cycle time + lead time equals the data storage hour
    #of the day.
    model_cycle_hour = int(predictor.fcst_ref_time)
    lead_time_hours = predictor.leadTime
    if ((lead_time_hours % HOURS_in_DAY) + model_cycle_hour) % HOURS_in_DAY != HOUR_UTC:
        logging.info("Model cycle hour + lead time must correspond to hour " + str(HOUR_UTC) + "Z")
        SIGN = -1
        TIME_CHK = False

    if TIME_CHK:
        #Cull the station list to stations with time zone offsets between
        #TZ_MIN and TZ_MAX.
        sta_tz = {}
        for sta in station_list:
            info = station_defs[sta]
            tz = info['tz']
            if tz >= TZ_MIN and tz <= TZ_MAX:
                sta_tz.update({sta : tz})

        #Define the 24-hour window size which includes four 6-hour periods
        #straddling the data needed to determine the nighttime minimum temperature
        #for time zone offset ranging from TZ_MIN to TZ_MAX, inclusive.
        start_24h = time - DAY
        end_24h = time

        #Fetch the hourly temperature in the 24-hour window.
        pred = predictor.copy()
        pred.change_property('Temp')
        pred.search_metadata.update({'start' : start_24h})
        pred.search_metadata.update({'end' : end_24h})
        pred.search_metadata.update({'duration' : 0})
        pred.search_metadata.update({'vert_coord1' : 2})
        pred.search_metadata.update({'reserved1' : 'vector'})
        hrly = fetch(filepaths, **pred.search_metadata)
        hrly_missing = hrly is None

        #Fetch 6-hour extrema.  We cannot use the above 24-hour window
        #to fetch the four 6-hour extrema values, since the 'start' and
        #'end' values in the database table 'variable' are not correctly
        #calculated.  So we pop these keys out of the search dictionary,
        #resulting in fetching all available values.
        pred.search_metadata.pop('start')
        pred.search_metadata.pop('end')
        pred.search_metadata.update({'duration' : 6})
        pred.search_metadata.update({'duration_method' : DURATION_METHOD})
        extT_6hr = fetch(filepaths, **pred.search_metadata)
        extT6_missing = extT_6hr is None

        #Return 'None' if both fetches failed.
        if hrly_missing and extT6_missing:
            if IS_MIN:
                logging.info("Could not fetch hourly temperatures and 6-hour minimum temperatures.")
            else:
                logging.info("Could not fetch hourly temperatures and 6-hour maximum temperatures.")
            return None

    #At this point, we have some data with which to come up with
    #extremum Temperature values.  So lets instantiate a data object.
    ExtremeT = Camps_data(NAME)

    #initialize extT, the placeholder of the extremum data values.
    #The initial value is -9999 because our code is set up to look
    #for maxima.  Thus, for nighttime minimum temperature, we will
    #feed the maxima algorithms, negatives of the temperature values.
    #Finding the maximum of a set of these values corresponds to
    #the minimum of the true values.  The initial value is the default
    #value.  It is only changed if a true maximum is found.
    extT = np.full(len(station_list),-9999)
    if TIME_CHK:
        #Reduce hrly to a camps data object with just the times and
        #data within the time range [start_hrly_min,end_hrly_max].
        #This data is fed into the method that finds the maximum.
        if not hrly_missing:
            if IS_MIN:
                if hrly.data.fill_value != 9999:
                    hrly.data.set_fill_value(9999)
                SIGN = -1
            else:
                if hrly.data.fill_value != -9999:
                    hrly.data.set_fill_value(-9999)
                SIGN = 1
            ptime = hrly.get_phenom_time()
            index_start = ptime.get_index(start_24h)
            index_end = ptime.get_index(end_24h)
            ptime.data = ptime.data[index_start:index_end+1]
            hrly.add_data(hrly.data[index_start:index_end+1,:,:])
            hrly_stations = np.array(util.station_trunc(hrly.location.get_stations()))
            hourlies = {}
            for i, sta in enumerate(station_list):
                if sta in hrly_stations:
#                if sta in sta_tz.keys():
                    ind = np.where(hrly_stations==sta)[0][0]
                    hourlies.update({sta : (SIGN*hrly.data.filled()[:,ind,0]).tolist()})
            if len(extT)>len(hourlies):
                extT = extT[0:len(hourlies)]
            find_max_in_hourlies(hourlies, I_UTC, sta_tz, station_list, extT)
        #Reduce the extT_6hr to those which have a period that at least
        #part is within the above hourly window [start_hrly_min, end_hrly_max].
        #Feed these values to the method 'adjust_max_with_6hours' that looks
        #for a maximum and compares it the value of extT that may have been
        #set in 'find_max_in_hourlies'.
        if not extT6_missing:
            if IS_MIN:
                if extT_6hr.data.fill_value != 9999:
                    extT_6hr.data.set_fill_value(9999)
                SIGN = -1
            else:
                if extT_6hr.data.fill_value != -9999:
                    extT_6hr.data.set_fill_value(-9999)
                SIGN = 1
            ptime_pd = extT_6hr.get_time_bounds()
            indices = [i for i in range(ptime_pd.data.shape[0]) if \
                ptime_pd.data[i,0] < end_24h and ptime_pd.data[i,1] > start_24h]
            ptime_pd.data = ptime_pd.data[indices,:]
            extT_6hr.add_data(extT_6hr.data[indices,:])
            maxt6 = {}
            extT_stations = np.array(util.station_trunc(extT_6hr.location.get_stations()))
            for i, sta in enumerate(station_list):
#            if sta in sta_tz.keys():
                if sta in extT_stations:
                    ind = np.where(extT_stations==sta)[0][0]
                    maxt6.update({sta : (SIGN*extT_6hr.data.filled()[:,ind]).tolist()})
            if len(extT)>len(maxt6):
                extT = extT[0:len(maxt6)]
            adjust_max_with_6hours(maxt6, I_UTC, sta_tz, station_list, extT)

#    for istn,stn in enumerate(station_list):
#        if stn in sta_tz.keys():
#            print stn, hourlies[stn], maxt6[stn], extT[istn]
    #Complete construction of the camps data object and return.
    phenomenonTime = Time.PhenomenonTime(data=np.array([time]))
    ExtremeT.time.append(phenomenonTime)
    resultTime = Time.ResultTime(data=np.array([time]))
    resultTime.append_result(None)
    ExtremeT.time.append(resultTime)
    ExtremeT.add_dimensions('number_of_stations')
    if TIME_CHK:
        #Adopt the station list from the 6-hour extremum data object.
        #If not fetched, then use that from the hourly data object.
        if not extT6_missing:
            ExtremeT.location=copy.copy(extT_6hr.location)
            ExtremeT.location.set_stations(list(maxt6.keys()))
            ExtremeT.processes = copy.deepcopy(extT_6hr.processes)
            for meta in extT_6hr.metadata:
                if meta not in list(ExtremeT.metadata.keys()):
                    if meta != 'hours':
                        ExtremeT.metadata[meta] = extT_6hr.metadata[meta]
            for prop in extT_6hr.properties:
                if 'coord_val' in prop:
                    ExtremeT.properties[prop] = extT_6hr.properties[prop]
        elif not hrly_missing:
            ExtremeT.location=copy.copy(hrly.location)
            ExtremeT.location.set_stations(list(hourlies.keys()))
            ExtremeT.processes = copy.deepcopy(hrly.processes)
            ExtremeT.add_process('BoundsProcMax')
            for meta in hrly.metadata:
                if meta not in list(ExtremeT.metadata.keys()):
                    ExtremeT.metadata[meta] = hrly.metadata[meta]
            ExtremeT.properties = copy.copy(hrly.properties)
   
    #Make a masked array of the data and insert it into the data object.
    ExtremeT.add_data(ma.masked_outside(SIGN*extT, -9998, 9998))
    ExtremeT.data[ExtremeT.data.data==-9999] = 9999
    if cfg.read_dimensions()['time'] not in ExtremeT.dimensions:
        ExtremeT.dimensions.insert(0,cfg.read_dimensions()['time'])
    ExtremeT.data = np.ma.masked_equal(ExtremeT.data, 9999) 
    ExtremeT.add_process(CALCULATION)
    
    return ExtremeT


def find_max_in_hourlies(hourlies, iwin, tzs, station_list, extT):
    """This method divides the hourly series of temperatures into
        five segments: two small segments outside of the variable's
        time window and three middle segments within the time window.
        Maximums are obtained from each segment and compared to one
        another to determine if an unambiguous maximum occurs within
        the time window.

    Arguments:
        hourlies (dict): keys are station names and values the hourly
            temperature series (25 hours).
        iwin (list): list of length 2 of start and end indices of
            time window at Greenwich.
        tzs (dict): keys are station names and values the time zone offsets.
        station_list (list): contains station names.
        extT (list): contains the maximum values of daytime maximum
            temperature or negative nighttime minimum temperature found
            for stations in the station list.

    """

    #The hourly data for a given station is divided into 5 contiguous
    #sections; three of which are within the variable time window
    #(tsegB, tseg, tsegC) and two without (tsegA, tsegD).  We try to
    #define a maximum in each segment restricted by certain conditions.
    #These restrictions are noted below.
    for I,stn in enumerate(hourlies.keys()):
        if stn in list(tzs.keys()):
            dh = -tzs[stn]
            i_start = iwin[0] + dh
            i_end = iwin[1] + dh
            tsegA = hourlies[stn][i_start-2:i_start]
            tsegB = hourlies[stn][i_start:i_start+4]
            tseg = hourlies[stn][i_start+4:i_end-3]
            tsegC = hourlies[stn][i_end-3:i_end+1]
            tsegD = hourlies[stn][i_end+1:i_end+3]
            if tsegA == []:
                tsegA = [tsegB[0]]
            if tsegD == []:
                tsegD = [tsegC[-1]]

            #Initialize maximums of segments to -9999.
            #These are default values.
            maxes = [-9999, -9999, -9999, -9999, -9999]
            #Set the maximum for each segment if less than two values are missing.
            for i,seg in enumerate([tsegA,tsegB,tseg,tsegC,tsegD]):
                nmiss = len([j for j, value in enumerate(seg) if value == -9999])
                if nmiss <= 1:
                    maxes[i] = max(seg)

            #Define a boolean value for the slope between the segments at the time window edges.
            #The slope is favorable towards the maximum being within the window if it is
            #positive(negative) between segments A(C) and B(D).  This value will be used as
            #a tiebreaker if the maximu is at the window edge and is the same in each segment
            #at the edge.
            slope = [False, False]
            indicesA = [i for i, value in enumerate(tsegA) if value != -9999]
            indicesB = [i for i, value in enumerate(tsegB) if value != -9999]
            if 0 in indicesA and 1 in indicesB:
                if tsegA[0] < tsegB[1]:
                    slope[0] = True
            elif 1 in indicesA and 1 in indicesB:
                if tsegA[1] < tsegB[1]:
                    slope[0] = True
            indicesC = [i for i, value in enumerate(tsegC) if value != -9999]
            indicesD = [i for i, value in enumerate(tsegD) if value != -9999]
            if 0 in indicesD and 3 in indicesC:
                if tsegD[0] < tsegC[3]:
                    slope[1] = True
            elif 1 in indicesD and 3 in indicesC:
                if tsegD[1] < tsegC[3]:
                    slope[1] = True

            #Find the maximum of the set of segment maxima.  Locate those within
            #the time window.  Also identify the segments with a missing maxima.
            #Then apply criteria to identify a legitimate maximum within the time
            #window.
            maxth = max(maxes)
            i_maxth = [i+1 for i, value in enumerate(maxes[1:-1]) if value == maxth]
            n_maxth = len(i_maxth)
            i_missh = [i for i, value in enumerate(maxes) if value == -9999]
            n_missh = len(i_missh)
            #We divide our search for a maximum into the number of the three middle
            #segments (covering the time window) having the same maximum value.
            #Starting with one middle segment, first check that maxes in neighboring
            #segments exist.  If they do, then if the middle segment with the max of
            #interest is the left one, at the left edge, then accept its max if it
            #exceeds the max of the extreme left segment that is outside the time window
            #or if equal, the slope is True (positive).  If the central segment has the
            #the max, then if the neighboring middle segments are not missing, accept
            #that max.  Finally, if the segment with the max is the right middle segment,
            #use the same logic as for the left one.
            if n_maxth == 1:
                if 1 in i_maxth:
                    if i_maxth[0]-1 not in i_missh and i_maxth[0]+1 not in i_missh:
                        if maxes[1] > maxes[0]:
                            extT[I] = maxth
                        elif maxes[1] == maxes[0]:
                            if slope[0]:
                                extT[I] = maxth
                elif 2 in i_maxth:
                    if i_maxth[0]-1 not in i_missh and i_maxth[0]+1 not in i_missh:
                        extT[I] = maxth
                elif 3 in i_maxth:
                    if i_maxth[0]-1 not in i_missh and i_maxth[0]+1 not in i_missh:
                        if maxes[3] > maxes[4]:
                            extT[I] = maxth
                        elif maxes[3] == maxes[4]:
                            if slope[1]:
                                extT[I] = maxth
            #If the number of middle segments having the max is two, then consider the
            #two cases in which the central segment and one of the edge segments have
            #the same max, and finally the rare case where its the left and right middle
            #segments that have the same max.  In each case, we follow the logic given above.
            elif n_maxth == 2:
                if 1 in i_maxth and 3 not in i_maxth:
                    if i_maxth[0]-1 not in i_missh and i_maxth[0]+1 not in i_missh:
                        if maxes[1] > maxes[0]:
                            extT[I] = maxth
                        elif maxes[1] == maxes[0]:
                            if slope[0]:
                                extT[I] = maxth
                elif 1 not in i_maxth and 3 in i_maxth:
                    if i_maxth[1]-1 not in i_missh and i_maxth[1]+1 not in i_missh:
                        if maxes[3] > maxes[4]:
                            extT[I] = maxth
                        elif maxes[3] == maxes[4]:
                            if slope[1]:
                                extT[I]
                elif 1 in i_maxth and 3 in i_maxth:
                    if i_maxth[0]-1 not in i_missh and i_maxth[1]+1 not in i_missh:
                        if maxes[1] > maxes[0] and maxes[3] > maxes[4]:
                            extT[I] = maxth
                        elif maxes[1] == maxes[0] and maxes[3] > maxes[4]:
                            if slope[0]:
                                extT[I] = maxth
                        elif maxes[1] > maxes[0] and maxes[3] == maxes[4]:
                            if slope[1]:
                                extT[I] = maxth
                        elif maxes[1] == maxes[0] and maxes[3] == maxes[4]:
                            if slope[0] and slope[1]:
                                extT[I] = maxth
            #Finally, there is the case where all three middle segments have the same
            #max.  Here we compare the maxes of the left and right middle segments with
            #their neighbors outside of the time window.
            elif n_maxth == 3:
                if 0 not in i_missh and 4 not in i_missh:
                    if maxes[0] < maxes[1] and maxes[3] > maxes[4]:
                        extT[I] = maxth
                    elif maxes[0] == maxes[1] and maxes[3] > maxes[4]:
                        if slope[0]:
                            extT[I] = maxth
                    elif maxes[0] < maxes[1] and maxes[3] == maxes[4]:
                        if slope[1]:
                            extT[I] = maxth
                    elif maxes[0] == maxes[1] and maxes[3] == maxes[4]:
                        if slope[0] and slope[1]:
                            extT[I] = maxth



def adjust_max_with_6hours(maxt6, iwin, tzs, station_list, extT):
    """This method takes the 6-hour maximums from either the 6-hour maximum
        temperature or the negative 6-hour nighttime minimum temperature and
        adjusts the maximum found by find_max_in_hourlies or determines it
        on its own.

    Arguments:
        maxt6 (list): list of length 4 of 6-hour maximums of either the
            maximum temperature or the negative of minimum temperature.
        iwin (list): list of length 2 of start and end indices of
            time window at Greenwich.
        tzs (dict): keys are station names and values the time zone offsets.
        station_list (list): contains station names.
        extT (list): contains the maximum values of daytime maximum
            temperature or negative nighttime minimum temperature found
            for stations in the station list.

    """

    #Loope through each station.  Find the appropriate triplet of
    #6-hour maximums, obtain the triplet's maximum, and determine
    #if it is useful to set or adjust the value of extT.
    for I,stn in enumerate(maxt6):
        if stn in list(tzs.keys()):
            dh = -tzs[stn]
            i_start = iwin[0] + dh
            i_end = iwin[1] + dh

            if i_start < 6:
                triplet = maxt6[stn][0:3]
            else:
                triplet = maxt6[stn][1:4]

            #We note if extT has a non-missing value, obtain the max
            #of the 6-hour triplet, note which members of the triplet
            #have the maximum, and not which have a misssing value.
            success = extT[I] != -9999 #True if non-missing.
            max_triplet = max(triplet) #get its max
            i_max_triplet = [i for i, value in enumerate(triplet) if value == max_triplet]
            n_max_triplet = len(i_max_triplet)
            i_miss6 = [i for i, value in enumerate(triplet) if value == -9999]
            n_miss6 = len(i_miss6)
            #Divide the adjustment process by the number of missing
            #values in the triplet.  If none are missing and only one
            #member has the maximum and its the central member, then
            #set extT to that value.  Otherwise if the one member
            #with the maximum is not the central one, then we depend
            #on extT already having a non-missing value, and we chose
            #the max of that value and the triplet max.  If more than
            #one of the triplets has the maximum value in the triplet
            #non-missing case, then we again need a non-missing value
            #of extT to compare to and pick the max of the two.
            if n_miss6 == 0:
                if n_max_triplet == 1:
                    if 1 in i_max_triplet:
                        extT[I] = max_triplet
                    elif success:
                        extT[I] = max(extT[I], max_triplet)
                else:
                    if success:
                        extT[I] = max(extT[I], max_triplet)
            #In the case of there are one or two missing values in the
            #triplet, then we need a non-missing value of extT to compare
            #to the triplet max, and choose the max of the two.
            #the case of three missing values means there is no triplet value.
            elif n_miss6 == 1 or n_miss6 == 2:
                if success:
                    extT[I] = max(extT[I], max_triplet)



def temp_corr_setup(filepaths, temp, pred):
    """Compute temperature correction.
    """
    # Only will work if surface or 2m elevation
    level = pred.get_coordinate()
    if level != 2 or level is not None:
        raise ValueError("level is not surface or 2m")
    # Otherwise, will work on sigma surface and isobarametric surfaces
    # Get temperature, relative humidity, and pressure
    temp = fetch(filepaths, property='Temp', source='GFS', vert_coord1=level)
    pres = fetch(filepaths, property='Pres', source='GFS', vert_coord1=None)
    rel_hum = fetch(filepaths, property='RelHum', source='GFS', vert_coord1=level)

    # Package into quantity
    q_temp = units('K') * temp.data
    q_pres = units('Pa') * pres.data
    q_rel_hum = units(None) * rel_hum.data # Dimensionless
    return temp



def temp_corr(pressure_arr, temperature_arr):
    """Compute the temperature correction
    """
    pass



def temp_lapse_setup(filepaths, time, predictor):
    """Construct a camps data object for temperature differences
    between two pressure levels.

    Arguments:
        control(instance): contains mospred_control.yaml file variables.
        time(int): The valid time of the predictor given as the
            number of seconds since January 1, 1970 00Z.
        predictor(Predictor): a Predictor object instantiated prior
            to the call to this function with the metadata fields
            pre-filled.  The metadata contains key/value pairs used
            for enquiring the database.

    Returns:
        temp_lapse_object (Camps_data): difference in air temperature
            between two specified pressure values.

    """

#   Instantiate the camps data object for the temperature lapse predictor
#   and set the international standard unit for temperature.
    temp_lapse_object = Camps_data('TLapse')
    international_units = { 'temperature' : 'kelvin' } #this will be a global dictionary.

#   Obtain the standard international units for this predictor.
#   The unit dimensionality of other objects will be checked against this international standard
#   for correct dimensionality.
    intl_unit = international_units.get('temperature')
    iu_pint = units.Quantity(1., intl_unit)

#   Determine the unit for the constructed predictor.
#   First try to obtain the unit from the instantiation process.
#   If set here, then test its dimensionality.
    unit = None
    try:
        unit = temp_lapse_object.metadata["units"]
        u_pint = units.Quantity(1.,unit)
        assert(u_pint.dimensionality == iu_pint.dimensionality),"Units from database for temperature lapse has incorrect dimensionality."
    except KeyError:
        print("TLapse: ")
        print("    Metadata key \'units\' does not exist or has no value.")
        print("    Adopt the units of the fetched temperatures.")

#   Start the fetching the temperatures at the specified pressure levels.
#   The lapse is defined as the temperature at the larger pressure minus
#   the temperature at the lesser pressure.

#   Make a deep copy of the predictor object with which to edit for each fetch.
    pred = predictor.copy()

#   Identify the lesser and large isobars.
    plevel1 = pred.search_metadata.get('vert_coord1')
    plevel2 = pred.search_metadata.get('vert_coord2')
    pl = plevel1
    pg = plevel2
    if pl > pg:
        pl = plevel2
        pg = plevel1
    temp_lapse_object.add_coord(pl,pg,vert_type='plev')

#   The observed property is temperature.
    pred.change_property('Temp')
    intl_unit = international_units.get('temperature')
    iu_pint = units.Quantity(1., intl_unit)

#   Get rid of keys not relevant for searching for data at single isobars.
    pred.search_metadata.pop('vert_coord2')
    pred.search_metadata.pop('vert_method')

#   Fetch temperature at the lesser isobar and
#   adopt its units as the temperature lapse units if not set.
    pred.search_metadata.update({'vert_coord1' : pl})
    temp_pl = fetch(filepaths, time, **pred.search_metadata)
    assert(isinstance(temp_pl,Camps_data)),"temp_pl expected to be camps data object"
    mask = np.ma.getmaskarray(temp_pl.data)
    try:
        t_unit = temp_pl.metadata['units']
        t_pint = units.Quantity(1.,t_unit)
        assert(t_pint.dimensionality == iu_pint.dimensionality),"Fetched temperature unit has wrong dimensionality."
    except:
        print("Fetched temperature needs units!")
        raise
    if unit is None:
        unit = t_unit
#   Create a metpy object containing temperature data and units.
#   This object will be used in forming the temperature lapse data.
##   And add the temperature camps data object as a component of the temperature lapse.
    q_tempPL = units.Quantity(temp_pl.data, t_unit)
    temp_lapse_object.add_component(temp_pl)
    temp_lapse_object.preprocesses = temp_pl.preprocesses

#   Fetch temperature at the greater isobar and
#   ensure that it is a camps data object.
    pred.search_metadata.update({'vert_coord1' : pg})
    temp_pg = fetch(filepaths, time, **pred.search_metadata)
    assert(isinstance(temp_pg,Camps_data)),"temp_pg expected to be camps data object"
    mask += np.ma.getmaskarray(temp_pg.data)
    try:
        t_unit = temp_pl.metadata['units']
        t_pint = units.Quantity(1.,t_unit)
        assert(t_pint.dimensionality == iu_pint.dimensionality),"Fetched temperature unit has wrong dimensionality."
    except:
        print("Fetched temperature needs units!")
        raise
#   Create a metpy object containing temperature data and units.
#   This object will be used in forming the temperature lapse data.
##   And add the temperature camps data object as a component of the temperature lapse.
    q_tempPG = units.Quantity(temp_pg.data, t_unit)
    temp_lapse_object.add_component(temp_pg)
    for proc in temp_pg.preprocesses:
        temp_lapse_object.add_preprocess(proc)

#   Call the temperature lapse function and set the units of the
#   returned data.  Note that we use metpy to calculate the data
#   because it accounts for differences in units.
#   And insert the result into the camps data object.
    q_temp_lapse = temp_lapse(q_tempPG, q_tempPL).to(unit)
    temp_lapse_object.add_dimensions('y')
    temp_lapse_object.add_dimensions('x')
    temp_lapse_object.add_dimensions('plev_bounds')
    temp_lapse_object.add_data(np.ma.array(np.array(q_temp_lapse), mask=mask))
#   Construct the rest of the camps data object for temperature lapse.
    temp_lapse_object.time = copy.deepcopy(temp_pg.time)
    temp_lapse_object.location = temp_pg.location
    temp_lapse_object.metadata.update({'FcstTime_hour' : temp_pg.metadata.get('FcstTime_hour')})
    temp_lapse_object.metadata.update({'coordinates' : temp_pg.get_coordinate()})
    temp_lapse_object.add_process('TempLapseCalc')

    return temp_lapse_object



def temp_lapse(temp_pg, temp_pl):
    """A function receiving two Metpy objects of air temperature at
        two different isobars, returning their difference in a Metpy object.
    """

    temperature_lapse = temp_pg - temp_pl

    return temperature_lapse



def potential_temperature_setup(filepaths, time, predictor):
    r"""This method prepares relevant parameters for the calculation of
        the potential temperature at a specified pressure level.
        The potential temperature is the temperature achieved by adiabatically
        moving a parcel of air at a given temperature and isobaric level
        to the reference pressure level of 1000 millibars.

    Args:
        filepaths ():
        time (int): The number of seconds since January 1, 1970 00Z.
        predictor (Predictor): a generic object of type Predictor holding
            an appropriately sized data array and metadata or properties
            pertaining to air temperature and atmospheric relative
            humidity.

    Returns:
        potemp (Camps_data): A Camps data object containing the potential
        temperature in units of Kelvin degrees.

    """

#   Instatntiate the camps data object for potential temperature.
    potemp = Camps_data('potential_temperature_instant')
    international_units = { 'temperature' : 'kelvin' } #this will be a global dictionary.

#   Obtain the international standard unit for temperature
#   and create a metpy object with that unit.  The metpy
#   object is to be used to test the dimensionality of
#   potential units adopted for potential temperature.
    intl_unit = international_units.get('temperature')
    iu_pint = units.Quantity(1., intl_unit)

#   Test the unit for potential temperature stored in the database.
    unit = None
    try:
        unit = potemp.metadata['units']
        u_pint = units.Quantity(1.,unit)
        assert(u_pint.dimensionality == iu_pint.dimensionality),"Units from database for potential temperature has incorrect dimensionality."
    except KeyError:
        print("No units specified in the database for potential temperature.")
        print("Pick up units from the fetched temperature.")

#   Now fetch the necessary components of the potential temperature,
#   using the predictor object that contains keys to enquire the
#   database.
#   Make a deep copy of the predictor object with which to edit for each fetch.
#   This way these changes do not leak outside of the method.
    pred = predictor.copy()

#   Obtain the isobar level
    isobar = pred.search_metadata.get('vert_coord1')
    q_isobar = units.Quantity(isobar, units.mbar)
    potemp.add_coord(isobar, vert_type='plev')

#   Fetch the temperature at the isobaric level and
#   adopti its unit for potential temperature if available,
#   has the correct dimensionality, and no unit has been
#   adopted yet.
    pred.change_property('Temp')
    intl_unit = international_units.get('temperature')
    iu_pint = units.Quantity(1.,intl_unit)
    temp = fetch(filepaths, time, **pred.search_metadata)
    assert(isinstance(temp,Camps_data)),"temp expected to be camps data object"
    mask = np.ma.getmaskarray(temp.data)
    try:
        t_unit = temp.metadata['units']
        t_pint = units.Quantity(1.,t_unit)
        assert(t_pint.dimensionality == iu_pint.dimensionality),"Wrong unit dimensionality adopted from fetched temperature"
    except:
        print("Fetched temperature needs units!")
        raise
    if unit is None:
        unit = t_unit
#   Construct the metpy object for the fetched temperature data.
#   It will be an argument in calling the avaiable metpy function
#   for potential temperature.
##   Then, add the temperature camps data object to the list of components
##   of the potential temperature.
    q_temp = units.Quantity(temp.data, t_unit)
    potemp.dimensions = copy.deepcopy(temp.dimensions)
    potemp.add_component(temp)
    potemp.preprocesses = temp.preprocesses

#   The air pressure is also a component of the potential temperature,
#   but I cannot construct a camps data object of it to add to the
#   component list.
#   Call the potential temperature function.
#   Declare the dimensions of the data before putting the data into
#   the camps data object for potential temperature.
    q_data = potential_temperature(q_isobar, q_temp).to(unit)
    potemp.add_data(np.ma.array(np.array(q_data), mask=mask))

#   Construct the rest of the camps data object for
#   potential temperature.
    potemp.time = copy.deepcopy(temp.time)
    potemp.location = temp.location
    potemp.metadata.update({'FcstTime_hour' : temp.metadata.get('FcstTime_hour')})
    potemp.metadata.update({ 'coordinates' : temp.metadata.get('coordinates') })
    potemp.metadata.update({'ReferencePressure_in_hPa' : 1000})
    potemp.add_process('PotTempCalc')

    return potemp


def potential_temperature(pressure, temperature):
    r"""This method calls the metpy.calc function potential_temperature
        which takes the pint.Quantity objects containing the
        isobaric level value and the temperature at that level
        and produces the corresponding potential temperature
        with the reference pressure being 1000 millibars.

    """

    return calc.potential_temperature(pressure, temperature)



# TempAdv : libraries.mathlib.temperature.temp_advection_setup
def temp_advection_setup(filepaths, time, predictor):
    r"""
    """
    pred = predictor.copy()

    pred.change_property('Temp')
    temp = fetch(filepaths, time, **pred.search_metadata)

    pred.change_property('Uwind')
    u_wind = fetch(filepaths, time, **pred.search_metadata)
    pred.change_property('Vwind')
    v_wind = fetch(filepaths, time, **pred.search_metadata)

# source : 'GFS13' property : 'Lat_grid'
    pred.change_property('Lat_grid')
    lat = fetch(filepaths, time, **pred.search_metadata)
    pred.change_property('Lon_grid')
    lon = fetch(filepaths, time, **pred.search_metadata)

    la, lo = geo_direct(lat, lon)

    q_t = units.Quantity(temp.data, temp.units)
    q_u = units.Quantity(u_wind.data, u_wind.units)
    q_v = units.Quantity(v_wind.data, v_wind.units).to(u_wind.units)
    q_x = q_u*lo[:,:,1] + q_v*la[:,:,1]
    q_y = q_u*lo[:,:,0] + q_v*la[:,:,0]

    x = temp.get_x()
    y = temp.get_y()
    q_dx = units.Quantity(x.data[1:]-x.data[:-1], x.units)
    q_dy = units.Quantity(y.data[1:]-y.data[:-1], y.units)
    q_ta = temperature_advection(q_t, [q_y,q_x], [q_dy, q_dx])

    temp_adv = Camps_data('temperature_advection')
    temp_adv.time = temp.time
    temp_adv.location = temp.location
    temp_adv.dimensions = temp.dimensions
    temp_adv.processes = temp.processes
    temp_adv.add_coord(temp.get_coordinate())
    temp_adv.data = np.array(q_ta)
    for k,v in list(temp.metadata.items()):
        if not 'name' in k \
        and not 'Property' in k:
            temp_adv.metadata[k] = v

    return temp_advect


def temperature_advection(temp, wind, delta):
    r"""
    """

    temp_advect = calc.advection(temp, wind, delta)

    return temp_advect



def geo_direct(latitude, longitude):
    r"""
    """
    ny, nx = latitude.shape
    x = np.transpose(np.repeat(latitude.get_x(),ny,axis=0).reshape(nx,ny))
    y = np.repeat(latitude.get_y(),nx,axis=0).reshape(ny,nx)

    lat = latitude.data
    lon = longitude.data

    dlodx = np.zeros((ny,nx))
    dlodx[:,1:-1]=(lon[:,1:-1]-lon[:,:-2])/(x[:,1:-1]-x[:,:-2]) +\
        (lon[:,2:]-lon[:,1:-1])/(x[:,2:]-x[:,1:-1])
    dlodx[:,0]=(lon[:,1]-lon[:,0])/(x[:,1]-x[:,0])
    dlodx[:,-1]=(lon[:,-1]-lon[:,-2])/(x[:,-1]-x[:,-2])
    dlodx = dlodx/2.

    dlody = np.zeros((ny,nx))
    dlody[1:-1,:]=(lon[1:-1,:]-lon[:-2,:])/(y[1:-1,:]-y[:-2,:]) +\
        (lon[2:,:]-lon[1:-1,:])/(y[2:,:]-y[1:-1,:])
    dlody[0,:]=(lon[1,:]-lon[0,:])/(y[1,:]-y[0,:])
    dlody[-1,:]=(lon[-1,:]-lon[-2,:])/(y[-1,:]-y[-2,:])
    dlody = dlody/2.

    dlo = np.sqrt(dlody**2+dlodx**2)
    lo = (dlody, dlodx)/dlo

    dladx = np.zeros((ny,nx))
    dladx[:,1:-1]=(lat[:,1:-1]-lat[:,:-2])/(x[:,1:-1]-x[:,:-2]) +\
        (lat[:,2:]-lat[:,1:-1])/(x[:,2:]-x[:,1:-1])
    dladx[:,0]=(lat[:,1]-lat[:,0])/(x[:,1]-x[:,0])
    dladx[:,-1]=(lat[:,-1]-lat[:,-2])/(x[:,-1]-x[:,-2])
    dladx = dladx/2.

    dlady = np.zeros((ny,nx))
    dlady[1:-1,:]=(lat[1:-1,:]-lat[:-2,:])/(y[1:-1,:]-y[:-2,:]) +\
        (lat[2:,:]-lat[1:-1,:])/(y[2:,:]-y[1:-1,:])
    dlady[0,:]=(lat[1,:]-lat[0,:])/(y[1,:]-y[0,:])
    dlady[-1,:]=(lat[-1,:]-lat[-2,:])/(y[-1,:]-y[-2,:])
    dlady = dlady/2.

    dla = np.sqrt(dlady**2+dladx**2)
    la = (dlady, dladx)/dla

    return la,lo

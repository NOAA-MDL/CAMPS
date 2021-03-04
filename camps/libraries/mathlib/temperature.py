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

from ...mospred import parse_pred as parse_pred
from ...registry import util as cfg
from ...core.reader import read_var
from ...core.Time import epoch_to_datetime
from ...core import Time as Time
from ...core import Location as Location
from ...core.Camps_data import Camps_data as Camps_data
from ...core import util as util
from ...registry import constants as const


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
            for retrieving variables.
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
    IS_MIN = os.path.basename(predictor['search_metadata']['property']) == 'NightMinT'
    if IS_MIN:
        HOUR_UTC = 18
        NAME = 'nighttime_minimum_temperature'
        CALCULATION = 'NightMinTempCalc'
        DURATION_METHOD = 'min'
        START_LST = 19
        END_LST = 8 #the next day from START_LST.
        I_UTC = [nhours+(START_LST-HOUR_UTC) for nhours in [0, (HOURS_in_DAY-START_LST)+END_LST]]
    else:
        HOUR_UTC = 6
        NAME = 'daytime_maximum_temperature'
        CALCULATION = 'DayMaxTempCalc'
        DURATION_METHOD = 'max'
        START_LST = 7
        END_LST = 19 #the same day as in START_LST
        I_UTC = [nhours+(START_LST-HOUR_UTC) for nhours in [0, (END_LST-START_LST)]]

    #Check that the function argument 'time' corresponds to the
    #appropriate hour of the day in UTC for data storage. 
    datetime_utc = [Time.epoch_to_datetime(t) for t in time]
    hour_utc = [d.hour for d in datetime_utc]
    minute_utc = [d.minute for d in datetime_utc]
    TIME_CHK = True
    if np.any(np.array(hour_utc)!=HOUR_UTC) or np.any(minute_utc):
        logging.info("Hour of time must be " + str(HOUR_UTC) + "Z")
        SIGN = -1
        TIME_CHCK = False

    #This method is called with a specific model cycle and lead time
    #in mind, even though the data does not depend on either.  We check
    #here if that cycle time + lead time equals the data storage hour
    #of the day.
    model_cycle_hour = int(predictor['fcst_ref_time'])
    lead_time_hours = predictor['leadTime']
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
        start_24h = [t-DAY for t in time]
        end_24h = time

        #Fetch the hourly temperature in the 24-hour window.
        pred = copy.deepcopy(predictor)
        pred['search_metadata'].update({'property' : parse_pred.observedProperty('Temp')})
        pred['search_metadata'].update({'start' : start_24h})
        pred['search_metadata'].update({'end' : end_24h})
        pred['search_metadata'].update({'duration' : 0})
        pred['search_metadata'].update({'vert_coord1' : 2})
        pred['search_metadata'].update({'reserved1' : 'vector'})
        hrly = read_var(filepath=filepaths, **pred['search_metadata'])
        hrly_missing = hrly is None

        #Fetch 6-hour extrema.  We cannot use the above 24-hour window.
        #So we pop these keys out of the search dictionary,
        #resulting in fetching all available values.
        pred['search_metadata'].pop('start')
        pred['search_metadata'].pop('end')
        pred['search_metadata'].update({'duration' : 6})
        pred['search_metadata'].update({'duration_method' : DURATION_METHOD})
        extT_6hr = read_var(filepath=filepaths, **pred['search_metadata'])
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
    extT = np.full((len(time),len(station_list)),-9999)
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
            pdata = np.array([ptime.data[index_start[i]:index_end[i]+1] for i in range(len(index_start))])
            ptime.data = pdata
            hrlydata = np.ma.array([hrly.data[index_start[i]:index_end[i]+1,:] for i in range(len(index_start))],fill_value=SIGN*-9999)
            hrly_stations = np.array(util.station_trunc(hrly.location.get_stations()))
            hourlies = {}
            for i, sta in enumerate(station_list):
                if sta in hrly_stations:
                    ind = np.where(hrly_stations==sta)[0][0]
                    hourlies.update({sta : (SIGN*hrlydata.filled()[:,:,ind])})
            if extT.shape[1]>len(hourlies):
                extT = extT[:,0:len(hourlies)]
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
            indices = [np.where((t[1]>np.array(start_24h)) & (t[0]<np.array(end_24h)))[0] for t in ptime_pd.data]
            indices = [i for i,ind in enumerate(indices) if ind.size!=0]
            indices = np.reshape(indices,(len(time),int(len(indices)/len(time))))
            ptime_pd.data = ptime_pd.data[indices,:]
            hrly6_data = extT_6hr.data[indices,:]
            maxt6 = {}
            extT_stations = np.array(util.station_trunc(extT_6hr.location.get_stations()))
            for i, sta in enumerate(station_list):
                if sta in extT_stations:
                    ind = np.where(extT_stations==sta)[0][0]
                    maxt6.update({sta : (SIGN*hrly6_data.filled()[:,:,ind])})
            if extT.shape[1]>len(maxt6):
                extT = extT[0:len(maxt6)]
            adjust_max_with_6hours(maxt6, I_UTC, sta_tz, station_list, extT)

    #Complete construction of the camps data object and return.
    phenomenonTime = Time.PhenomenonTime(data=np.array(time))
    ExtremeT.time.append(phenomenonTime)
    ExtremeT.add_dimensions('stations')
    if TIME_CHK:
        #Adopt the station list from the 6-hour extremum data object.
        #If not fetched, then use that from the hourly data object.
        if not extT6_missing:
            ExtremeT.location=copy.copy(extT_6hr.location)
            ExtremeT.location.set_stations(list(maxt6.keys()))
            ExtremeT.processes = copy.deepcopy(extT_6hr.processes)
            for meta in extT_6hr.metadata:
                if meta not in list(ExtremeT.metadata.keys()):
                    if meta != 'hours' and meta!='coordinates':
                        ExtremeT.metadata[meta] = extT_6hr.metadata[meta]
            for prop in extT_6hr.properties:
                if 'coord_val' in prop:
                    ExtremeT.properties[prop] = extT_6hr.properties[prop]
        elif not hrly_missing:
            ExtremeT.location=copy.copy(hrly.location)
            ExtremeT.location.set_stations(list(hourlies.keys()))
            ExtremeT.processes = copy.deepcopy(hrly.processes)
            for meta in hrly.metadata:
                if meta not in list(ExtremeT.metadata.keys()):
                    if meta != 'coordinates':
                        ExtremeT.metadata[meta] = hrly.metadata[meta]
            ExtremeT.properties = copy.copy(hrly.properties)
   
    #Make a masked array of the data and insert it into the data object.
    if cfg.read_dimensions()['time'] not in ExtremeT.dimensions:
        ExtremeT.dimensions.insert(0,cfg.read_dimensions()['time'])
    ExtremeT.add_data(ma.masked_outside(SIGN*extT[:,:], -9998, 9998))
    ExtremeT.data[ExtremeT.data.data==-9999] = 9999
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
            tsegA = hourlies[stn][:,i_start-2:i_start]
            tsegB = hourlies[stn][:,i_start:i_start+4]
            tseg = hourlies[stn][:,i_start+4:i_end-3]
            tsegC = hourlies[stn][:,i_end-3:i_end+1]
            tsegD = hourlies[stn][:,i_end+1:i_end+3]
            if tsegA.size==0:
                tsegA = tsegB[:,0,None]
            if tsegD.size==0:
                tsegD = tsegC[:,-1,None]
            #Initialize maximums of segments to -9999.
            #These are default values.
            maxes = np.ones((hourlies[stn].shape[0],5))*-9999
            #Set the maximum for each segment if less than two values are missing.
            for i,seg in enumerate([tsegA,tsegB,tseg,tsegC,tsegD]):
                if seg.size!=0:
                    valid_days = np.where(np.count_nonzero(seg==-9999,axis=1)<=1)[0]
                    maxes[valid_days,i] = np.max(seg[valid_days,:],axis=1)

            #Define a boolean value for the slope between the segments at the time window edges.
            #The slope is favorable towards the maximum being within the window if it is
            #positive(negative) between segments A(C) and B(D).  This value will be used as
            #a tiebreaker if the maximu is at the window edge and is the same in each segment
            #at the edge.
            slope = np.array([[False, False]]*hourlies[stn].shape[0])
            
            indsAB = np.where((tsegA[:,0]!=-9999) & (tsegB[:,1]!=-9999) & (tsegA[:,0] < tsegB[:,1]))[0]
            if indsAB.size==0:
                indsAB = np.where((tsegA[:,1]!=-9999) & (tsegB[:,1]!=-9999) & (tsegA[:,1] < tsegB[:,1]))[0]
            slope[indsAB,0] = True
            if tsegD.size!=0:
                indsDC = np.where((tsegD[:,0]!=-9999) & (tsegC[:,3]!=-9999) & (tsegD[:,0]<tsegC[:,3]))[0]
                if indsDC.size==0:
                    try:
                        indsDC = np.where((tsegD[:,1]!=-9999) & (tsegC[:,3]!=-9999) & (tsegD[:,1]<tsegC[:,3]))[0]
                    except:
                        pass
            else: indsDC = []
            slope[indsDC,1] = True

            #Find the maximum of the set of segment maxima.  Locate those within
            #the time window.  Also identify the segments with a missing maxima.
            #Then apply criteria to identify a legitimate maximum within the time
            #window.
            maxth = np.max(maxes,axis=1)
            i_maxth = maxes[:,1:-1]==maxth[:,None]
            n_maxth = np.count_nonzero(i_maxth,axis=1)
            valid_inds=n_maxth!=0
            i_missh = maxes==-9999
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
            inds1 = np.where((n_maxth[valid_inds]==1) & (i_maxth[:,0][valid_inds]) & (~i_missh[:,0][valid_inds]) & (~i_missh[:,2][valid_inds]) & (maxes[:,1]>maxes[:,0])[valid_inds])[0]
            extT[np.where(valid_inds)[0][inds1],I] = maxth[valid_inds][inds1]

            inds2 = np.where((n_maxth[valid_inds]==1) & (i_maxth[:,0][valid_inds]) & (~i_missh[:,0][valid_inds]) & (~i_missh[:,2][valid_inds]) & (maxes[:,1]==maxes[:,0])[valid_inds] & (slope[:,0][valid_inds]))[0]
            extT[np.where(valid_inds)[0][inds2],I] = maxth[valid_inds][inds2]

            inds3 = np.where((n_maxth[valid_inds]==1) & (i_maxth[:,1][valid_inds]) & (~i_missh[:,1][valid_inds]) & (~i_missh[:,3][valid_inds]))[0]
            extT[np.where(valid_inds)[0][inds3],I] = maxth[valid_inds][inds3]

            inds4 = np.where((n_maxth[valid_inds]==1) & (i_maxth[:,2][valid_inds]) & (~i_missh[:,2][valid_inds]) & (~i_missh[:,4][valid_inds]) & (maxes[:,3]>maxes[:,4])[valid_inds])[0]
            extT[np.where(valid_inds)[0][inds4],I] = maxth[valid_inds][inds4]

            inds5 = np.where((n_maxth[valid_inds]==1) & (i_maxth[:,2][valid_inds]) & (~i_missh[:,2][valid_inds]) & (~i_missh[:,4][valid_inds]) & (maxes[:,3]==maxes[:,4])[valid_inds] & (slope[:,1][valid_inds]))[0]
            extT[np.where(valid_inds)[0][inds5],I] = maxth[valid_inds][inds5]
            #If the number of middle segments having the max is two, then consider the
            #two cases in which the central segment and one of the edge segments have
            #the same max, and finally the rare case where its the left and right middle
            #segments that have the same max.  In each case, we follow the logic given above.
            inds6 = np.where((n_maxth[valid_inds]==2) & (i_maxth[:,0][valid_inds]) & (~i_maxth[:,2][valid_inds]) & (~i_missh[:,0][valid_inds]) & (~i_missh[:,2][valid_inds]) & (maxes[:,1]>maxes[:,0])[valid_inds])[0]
            extT[np.where(valid_inds)[0][inds6],I] = maxth[valid_inds][inds6]

            inds7 = np.where((n_maxth[valid_inds]==2) & (i_maxth[:,0][valid_inds]) & (~i_maxth[:,2][valid_inds]) & (~i_missh[:,0][valid_inds]) & (~i_missh[:,2][valid_inds]) & (maxes[:,1]==maxes[:,0])[valid_inds] & (slope[valid_inds,0]))[0]
            extT[np.where(valid_inds)[0][inds7],I] = maxth[valid_inds][inds7]

            inds8 = np.where((n_maxth[valid_inds]==2) & (~i_maxth[:,0][valid_inds]) & (i_maxth[:,2][valid_inds]) & (~i_missh[:,2][valid_inds]) & (~i_missh[:,4][valid_inds]) & (maxes[:,3]>maxes[:,4])[valid_inds])[0]
            extT[np.where(valid_inds)[0][inds8],I] = maxth[valid_inds][inds8]

            inds9 = np.where((n_maxth[valid_inds]==2) & (~i_maxth[:,0][valid_inds]) & (i_maxth[:,2][valid_inds]) & (~i_missh[:,2][valid_inds]) & (~i_missh[:,4][valid_inds]) & (maxes[:,3]==maxes[:,4])[valid_inds] & (slope[valid_inds,1]))[0]
            extT[np.where(valid_inds)[0][inds9],I] = maxth[valid_inds][inds9]

            inds10 = np.where((n_maxth[valid_inds]==2) & (i_maxth[:,0][valid_inds]) & (i_maxth[:,2][valid_inds]) & (~i_missh[:,0][valid_inds]) & (~i_missh[:,4][valid_inds]) & (maxes[:,1]>maxes[:,0])[valid_inds] & (maxes[:,3]>maxes[:,4])[valid_inds])[0]
            extT[np.where(valid_inds)[0][inds10],I] = maxth[valid_inds][inds10]

            inds11 = np.where((n_maxth[valid_inds]==2) & (i_maxth[:,0][valid_inds]) & (i_maxth[:,2][valid_inds]) & (~i_missh[:,1][valid_inds]) & (~i_missh[:,4][valid_inds]) & (maxes[:,1]==maxes[:,0])[valid_inds] & (maxes[:,3]>maxes[:,4])[valid_inds] & (slope[valid_inds,0]))[0]
            extT[np.where(valid_inds)[0][inds11],I] = maxth[valid_inds][inds11]

            inds12 = np.where((n_maxth[valid_inds]==2) & (i_maxth[:,0][valid_inds]) & (i_maxth[:,2][valid_inds]) & (~i_missh[:,1][valid_inds]) & (~i_missh[:,4][valid_inds]) & (maxes[:,1]>maxes[:,0])[valid_inds] & (maxes[:,3]==maxes[:,4])[valid_inds] & (slope[valid_inds,1]))[0]
            extT[np.where(valid_inds)[0][inds12],I] = maxth[valid_inds][inds12]

            inds13 = np.where((n_maxth[valid_inds]==2) & (i_maxth[:,0][valid_inds]) & (i_maxth[:,2][valid_inds]) & (~i_missh[:,1][valid_inds]) & (~i_missh[:,4][valid_inds]) & (maxes[:,1]==maxes[:,0])[valid_inds] & (maxes[:,3]==maxes[:,4])[valid_inds] & (slope[valid_inds,0]) & (slope[valid_inds,1]))[0]
            extT[np.where(valid_inds)[0][inds13],I] = maxth[valid_inds][inds13]
            #Finally, there is the case where all three middle segments have the same
            #max.  Here we compare the maxes of the left and right middle segments with
            #their neighbors outside of the time window.

            inds14 = np.where((n_maxth[valid_inds]==3) & (~i_missh[:,0][valid_inds]) & (~i_missh[:,4][valid_inds]) & (maxes[:,0]<maxes[:,1])[valid_inds] & (maxes[:,3]>maxes[:,4])[valid_inds])[0]
            extT[np.where(valid_inds)[0][inds14],I] = maxth[valid_inds][inds14]

            inds15 = np.where((n_maxth[valid_inds]==3) & (~i_missh[:,0][valid_inds]) & (~i_missh[:,4][valid_inds]) & (maxes[:,0]==maxes[:,1])[valid_inds] & (maxes[:,3]>maxes[:,4])[valid_inds] & (slope[valid_inds,0]))[0]
            extT[np.where(valid_inds)[0][inds15],I] = maxth[valid_inds][inds15]

            inds16 = np.where((n_maxth[valid_inds]==3) & (~i_missh[:,0][valid_inds]) & (~i_missh[:,4][valid_inds]) & (maxes[:,0]>maxes[:,1])[valid_inds] & (maxes[:,3]==maxes[:,4])[valid_inds] & (slope[valid_inds,1]))[0]
            extT[np.where(valid_inds)[0][inds16],I] = maxth[valid_inds][inds16]

            inds17 = np.where((n_maxth[valid_inds]==3) & (~i_missh[:,0][valid_inds]) & (~i_missh[:,4][valid_inds]) & (maxes[:,0]==maxes[:,1])[valid_inds] & (maxes[:,3]==maxes[:,4])[valid_inds] & (slope[valid_inds,0]) & (slope[valid_inds,1]))[0]
            extT[np.where(valid_inds)[0][inds17],I] = maxth[valid_inds][inds17]


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
                triplet = maxt6[stn][:,0:3]
            else:
                triplet = maxt6[stn][:,1:4]
            #We note if extT has a non-missing value, obtain the max
            #of the 6-hour triplet, note which members of the triplet
            #have the maximum, and not which have a misssing value.
            success = extT[:,I] != -9999 #True if non-missing.
            max_triplet = np.max(triplet,axis=1) #get its max
            i_max_triplet = max_triplet[:,None] == triplet
            n_max_triplet = np.count_nonzero(i_max_triplet,axis=1)
            i_miss6 = triplet==-9999
            n_miss6 = np.count_nonzero(i_miss6,axis=1)
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
            inds1 = np.where((n_miss6==0) & (n_max_triplet==1) & (i_max_triplet[:,1]))[0]
            extT[inds1,I] = max_triplet[inds1]

            inds2 = np.where((n_miss6==0) & (n_max_triplet==1) & (success))[0]
            extT[inds2,I] = np.maximum(extT[inds2,I],max_triplet[inds2])

            inds3 = np.where((n_miss6==0) & ~(n_max_triplet==1) & (success))[0]
            extT[inds3,I] = np.maximum(extT[inds3,I],max_triplet[inds3])

            #In the case of there are one or two missing values in the
            #triplet, then we need a non-missing value of extT to compare
            #to the triplet max, and choose the max of the two.
            #the case of three missing values means there is no triplet value.
            inds4 = np.where(((n_miss6==1) | (n_miss6==2)) & (success))[0]
            extT[inds4,I] = np.maximum(extT[inds4,I],max_triplet[inds4])


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
            for retrieving variables.

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
        assert(u_pint.dimensionality == iu_pint.dimensionality),"Units in metadata for temperature lapse has incorrect dimensionality."
    except KeyError:
        print("TLapse: ")
        print("    Metadata key \'units\' does not exist or has no value.")
        print("    Adopt the units of the fetched temperatures.")

#   Start the fetching the temperatures at the specified pressure levels.
#   The lapse is defined as the temperature at the larger pressure minus
#   the temperature at the lesser pressure.

#   Make a deep copy of the predictor object with which to edit for each fetch.
    pred = copy.deepcopy(predictor)

#   Identify the lesser and large isobars.
    plevel1 = pred['search_metadata'].get('vert_coord1')
    plevel2 = pred['search_metadata'].get('vert_coord2')
    pl = plevel1
    pg = plevel2
    if pl > pg:
        pl = plevel2
        pg = plevel1
    temp_lapse_object.add_vert_coord(pl,pg,vert_type='plev')

#   The observed property is temperature.
    pred['search_metadata'].update({'property' : parse_pred.observedProperty('Temp')})
    intl_unit = international_units.get('temperature')
    iu_pint = units.Quantity(1., intl_unit)

#   Get rid of keys not relevant for searching for data at single isobars.
    pred['search_metadata'].pop('vert_coord2')
    pred['search_metadata'].pop('vert_method')

#   Fetch temperature at the lesser isobar and
#   adopt its units as the temperature lapse units if not set.
    pred['search_metadata'].update({'vert_coord1' : pl})
    temp_pl = read_var(filepath=filepaths, forecast_time=time, **pred['search_metadata'])
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
    pred['search_metadata'].update({'vert_coord1' : pg})
    temp_pg = read_var(filepath=filepaths, forecast_time=time, **pred['search_metadata'])
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
    temp_lapse_object.add_dimensions('phenomenonTime')
    temp_lapse_object.add_dimensions('y')
    temp_lapse_object.add_dimensions('x')
    temp_lapse_object.add_data(np.ma.array(np.array(q_temp_lapse), mask=mask))
#   Construct the rest of the camps data object for temperature lapse.
    temp_lapse_object.time = copy.deepcopy(temp_pg.time)
    temp_lapse_object.location = temp_pg.location
    temp_lapse_object.metadata.update({'FcstTime_hour' : temp_pg.metadata.get('FcstTime_hour')})
    temp_lapse_object.metadata.update({'coordinates' : temp_pg.metadata['coordinates']})
    temp_lapse_object.metadata.update({'PROV__hadPrimarySource' : temp_pg.metadata['PROV__hadPrimarySource']})
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

#   Test the unit for potential temperature stored in netcdf.yaml.
    unit = None
    try:
        unit = potemp.metadata['units']
        u_pint = units.Quantity(1.,unit)
        assert(u_pint.dimensionality == iu_pint.dimensionality),"Units from metadata for potential temperature has incorrect dimensionality."
    except KeyError:
        print("No units specified in netcdf.yaml for potential temperature.")
        print("Pick up units from the fetched temperature.")

#   Now fetch the necessary components of the potential temperature,
#   using the predictor object.
#   Make a deep copy of the predictor object with which to edit for each fetch.
#   This way these changes do not leak outside of the method.
    pred = copy.deepcopy(predictor)

#   Obtain the isobar level
    isobar = pred['search_metadata'].get('vert_coord1')
    q_isobar = units.Quantity(isobar, units.mbar)
    potemp.add_vert_coord(isobar, vert_type='plev')

#   Fetch the temperature at the isobaric level and
#   adopti its unit for potential temperature if available,
#   has the correct dimensionality, and no unit has been
#   adopted yet.
    pred['search_metadata'].update({'property' : parse_pred.observedProperty('Temp')})
    intl_unit = international_units.get('temperature')
    iu_pint = units.Quantity(1.,intl_unit)
    temp = read_var(filepath=filepaths, forecast_time=time, **pred['search_metadata'])
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
    potemp.metadata[const.VERT_COORD] = temp.metadata[const.VERT_COORD]
    potemp.metadata.update({'FcstTime_hour' : temp.metadata.get('FcstTime_hour')})
    potemp.metadata.update({ 'coordinates' : temp.metadata.get('coordinates') })
    potemp.metadata.update({'ReferencePressure_in_hPa' : 1000})
    potemp.metadata.update({'PROV__hadPrimarySource' : temp.metadata.get('PROV__hadPrimarySource')})
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

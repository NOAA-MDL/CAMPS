import sys
import os
from datetime import datetime, timedelta
import csv
import logging
import string
import pdb
import re
import numpy as np
from netCDF4 import Dataset
from . import Time


"""Module: util.py

Methods:
    generate_date_range
    read_station_list
    read_station_table
    station_trunc
    equations_summary
"""



#NOTE: This was in Riley's util.py in mospred...I'm confused by it existing
#wouldn't this mean that station_cache is ALWAYS none whenever these
#functions are called?
station_cache = {'station_defs' : None, 'valid_stations' : None}


def generate_date_range(drlist):
    """Generates a list of dates in YYYYMMDDHH format. The format
    of the argument is 'YYYYMMDDHH-YYYYMMDDHH,stride'
    """

    if type(drlist) is str:
        drlist = [drlist]

    #Initialize the date list.
    dates = []
    for dr in drlist:
        if dr.isdigit(): #check for single date
            dates.append(Time.datetime_to_str(Time.str_to_datetime(dr)))
        else: #is range of dates
            dr_range = dr.split(",")[0]
            dr_stride = dr.split(",")[1]
            dt_start = Time.str_to_datetime(dr_range.split("-")[0])
            dt_stop = Time.str_to_datetime(dr_range.split("-")[1])
            if any(h in dr_stride for h in ['h','H']):
                delta = timedelta(hours=int(re.sub(r'[a-zA-Z]','',dr_stride)))
            #Stride from start to stop.  Note that stop time may not be in list.
            while dt_start <= dt_stop:
                dates.append(Time.datetime_to_str(dt_start))
                dt_start += delta

    return dates


def read_station_list(file_path):
    """Reads station IDs from file path defined from a
    control file. Returns them as a sorted list with
    no duplicates.
    """

    #Use previously saved station list if possible
    if station_cache['valid_stations'] is not None:
        return station_cache['valid_stations'].copy()

    #Read in station list from file provided and return
    #sorted list with no repeated stations
    station_list = []
    with open(file_path, 'r') as f:
        for line in f:
            station_list.append(line.strip())

    #Filter out undefined stations if possible
    if station_cache['station_defs'] is not None:
        stations_copy = station_list[:]
        for station in stations_copy:
            if station not in station_cache['station_defs']:
                station_list.remove(station)
    #Sort and remove duplicates
    valid_stations = list(sorted(set(station_list)))
    #Add to cache
    station_cache['valid_stations'] = valid_stations

    return valid_stations


def read_station_table(file_path,stalist):
    """Reads station metadata from the station table file.
    Reads all station definitions from file defined in control
    file. Returns a dictionary where the keys are the station
    call letters and dictionary values of form {lat: xxx, lon:yyy, ...}.
    Positive lat/lon values indicate North/West,
    while negative lat/lon values indicate South/East.
    """

    #Use station_cache data if available
    if station_cache['station_defs'] is not None:
        return station_cache['station_defs'].copy()

    #Create the station dictionary
    station_dict = {}
    with open(file_path,'r') as f:
        reader = csv.reader(f,delimiter=":",quoting=csv.QUOTE_NONE)
        for row in reader:
            call = row[0].strip(' ')
            #Only take the first definition for a call in the case of duplicates.
            if call not in station_dict:
                link1 = row[1]
                name = row[2]
                state = row[3]
                code = row[4]
                elev = row[5]
                lat = row[6]
                lon = row[7]
                tz = row[8]
                quality_flag = row[9]

                if lat[0] == 'N':
                    lat = float(lat[1:])
                elif lat[0] == 'S':
                    lat = -float(lat[1:])
                if lon[0] == 'W':
                    lon = -float(lon[1:])
                elif lon[0] == 'E':
                    lon = float(lon[1:])

                station_dict[call] = {}
                station_dict[call]['name'] = name
                station_dict[call]['long_name'] = name
                station_dict[call]['state'] = state
                station_dict[call]['code'] = code # Leave a string for now
                station_dict[call]['elev'] = int(elev) if len(elev.strip()) > 0 else 0
                station_dict[call]['lat'] = lat
                station_dict[call]['lon'] = lon
                station_dict[call]['tz'] = int(tz.strip()) if len(tz.strip()) > 0 else 0
                station_dict[call]['quality_flag'] = quality_flag

    #The station table has been read, now make sure each station
    #in the list is in the table.  Remove, if not.
    stalist_from_table = list(station_dict.keys())
    stalist_new = []
    for sta in stalist:
        if sta in stalist_from_table:
            stalist_new.append(sta)
        else:
            logging.warning("Station "+sta+" not found in table. Removing from list.")

    #Save in cache for later use
    station_cache['station_defs'] = station_dict

    return stalist_new,station_dict


def station_trunc(station_list):
    """Removes trailing '_' and ' ' from station names in given list."""

    station_list = [station.replace('_','').replace(' ','') for station in station_list if station is not None]

    return station_list

def equations_summary(**kwargs):
    """Writes out a summary of information from a regression equation, including:
    Reduction of Variance
    Standard Error
    Predictors used in the equation and their coefficients
    Equation Constant

    Usage:
    EITHER coefficients AND predictors (usage 1) OR filepath (usage 2) are required

    coefficients is an array or nested list of equation cofficients
    predictors is a string array of predictor names
    filepath is a string which points to an equations_driver output file

    other allowed keywords are:
    stations - a station name or list of station names (usage 1 and 2)

    predictands - a string array of predictand names (usage 1)

    variance - an array of Reduction of Variance (usage 1)

    error - an array of Standard Error Estimate (usage 1)

    consts - an array of Equation Constants (usage 1)

    outname - a filepath and filename to which the summary is written (usage 1 and 2)
    if outname is not provided, summary will be written to "equations_summary.txt"
    in the current working directory
    """

    # Get information from kwargs and open file to be written
    if "outname" not in kwargs:
        outname = "equations_summary.txt"
    else:
        outname = kwargs['outname']
    outfile = open(outname,"w")
    if "variance" in kwargs:
        variance = kwargs['variance']
    if "error" in kwargs:
        error = kwargs['error']
    if "consts" in kwargs:
        consts = kwargs['consts']
    if "averages" in kwargs:
        averages = kwargs['averages']
    if "stations" in kwargs:
        stations = kwargs['stations']
        if not isinstance(stations,list):
            stations = [stations] #Set stations to list if it isn't already
    #First use case: coefficients and predictors are provided.
    #Output will be created directly from these input
    if "coefficients" in kwargs and "predictors" in kwargs:
        coefficients = kwargs['coefficients']
        predictors = kwargs['predictors']
        #Loop over input stations
        for n,sta in enumerate(stations):
            if isinstance(sta,list): sta = sta[0]
            if isinstance(sta,bytes): sta = sta.decode()
            if isinstance(coefficients,list): coefficients = np.array(coefficients)
            #Find indices coefficients for station which are nonzero
            #and find the associated predictor names
            #If predictands was provided, the output will name the predictand,
            #otherwise a numeral will be provided
            if "predictands" in kwargs:
                predictands = kwargs['predictands']
                for m,tand in enumerate(predictands):
                    coefs_ind = np.nonzero(coefficients[n,:,m])[0]
                    preds = predictors[coefs_ind,:]
                    coefs = coefficients[n,coefs_ind,m]
                    try:
                        avg = averages[n,m]
                    except NameError:
                        avg = None
                    try:
                        var = variance[n,m]
                    except NameError:
                        var = None
                    try:
                        err = error[n,m]
                    except NameError:
                        err = None
                    try:
                        const = consts[n,m]
                    except NameError:
                        const = None
                    pred_strings = [pred.tostring() for pred in preds]
                    # Make sure tand is byte strings, convert to str and combine characters in array
                    if isinstance(tand[0],bytes): tand = (tand.tostring()).decode()
                    if pred_strings:
                        # Construct an output string based on all input information
                        info_string1 = "Equation Summary for station: {sta} for predictand: {tand}\n".format(sta=sta,tand=tand)
                        if avg:
                            info_string1 += "Predictand Average: "+str(avg)+"\n"
                        if var:
                            info_string1 += "Variance of Reduction: "+str(var)+" "
                        if err:
                            info_string1 += "Standard Error Estimate: "+str(err)+"\n"
                        if var and not err:
                            info_string1 += "\n"
                        info_string2=''
                        for i,pred in enumerate(pred_strings): info_string2+=str(pred.decode())+","+str(coefs[i])+"\n"
                        if const:
                            info_string2+="Equation Constant: "+str(const)+"\n"
                        info_string = info_string1+info_string2+"\n"
                        outfile.write(info_string)
                    elif not pred_strings:
                        info_string = "No equation information available for station: "+sta+" for predictand: "+tand+"\n\n"
                        outfile.write(info_string)
                outfile.write("\n")
            # If no predictand list is provided, denote predictand with a numeral
            else:
                for m in range(coefficients[n].shape[1]):
                    coefs_ind = np.nonzero(coefficients[n,:,m])[0]
                    preds = predictors[coefs_ind,:]
                    coefs = coefficients[n,coefs_ind,m]
                    try:
                        avg = averages[n,m]
                    except NameError:
                        avg = None
                    try:
                        var = variance[n,m]
                    except NameError:
                        var = None
                    try:
                        err = error[n,m]
                    except NameError:
                        err = None
                    try:
                        const = consts[n,m]
                    except NameError:
                        const = None
                    pred_strings = [pred.tostring() for pred in preds]
                    if pred_strings:
                        # Construct an output string based on all input information
                        info_string1 = "Equation Summary for station: {sta} for predictand #{tand_n}:\n".format(sta=sta,tand_n=str(m+1))
                        if avg:
                            info_string1 += "Predictand Average: "+str(avg)+"\n"
                        if var:
                            info_string1 += "Variance of Reduction: "+str(var)+" "
                        if err:
                            info_string1 += "Standard Error Estimate: "+str(err)+"\n"
                        if var and not err:
                            info_string1 += "\n"
                        info_string2=''
                        for i,pred in enumerate(pred_strings): info_string2+=str(pred)+","+str(coefs[i])+"\n"
                        if const:
                            info_string2+="Equation Constant: "+str(const)+"\n"
                        info_string = info_string1+info_string2+"\n"
                        outfile.write(info_string)
                    elif not pred_strings:
                        outfile.write("No equation information available for station: "+sta+" for predictand #"+str(m+1)+".\n\n")
                outfile.write("\n")
        outfile.close()
    #Second use case: a path to a file is provided.
    #Necessary equation information will be drawn from file.
    #If a station or list of stations is not provided, will run for all stations in file.
    elif "filepath" in kwargs:
        filepath = kwargs['filepath']
        pred_file = Dataset(filepath)
        if "stations" not in kwargs:
            file_stations = station_trunc([sta.tostring() for sta in pred_file.variables['station'][:]])
            stations = file_stations

        coefficients = pred_file.variables['MOS_Equations'][:,:-1,:]
        consts = pred_file.variables['MOS_Equations'][:,-1,:]
        variance = pred_file.variables['Reduction_of_Variance'][:]
        error = pred_file.variables['Standard_Error_Estimate'][:]
        averages = pred_file.variables['Predictand_Average'][:]
        predictors = pred_file.variables['Equations_List'][:-1,:]
        predictands = pred_file.variables['Predictand_List'][:]
        for n,sta in enumerate(stations):
            if isinstance(sta,list): sta = sta[0]
            #Find indices coefficients for station which are nonzero
            #and find the associated predictor names
            for m,tand in enumerate(predictands):
                coefs_ind = np.nonzero(coefficients[n,:,m])[0]
                preds = predictors[coefs_ind,:]
                coefs = coefficients[n,coefs_ind,m]
                var = variance[n,m]
                err = error[n,m]
                const = consts[n,m]
                avg = averages[n,m]
                pred_strings = [pred.tostring() for pred in preds]
                if pred_strings:
                    # Contstruct output string based on all input information
                    info_string1 = "Equation Summary for station: {sta} for predictand: {tand}\n".format(sta=sta,tand=tand.tostring())
                    info_string1 += "Predictand Average: "+str(avg)+"\n"
                    info_string1 += "Variance of Reduction: "+str(var)+" "
                    info_string1 += "Standard Error Estimate: "+str(err)+"\n"
                    info_string2=''
                    for i,pred in enumerate(pred_strings): info_string2+=str(pred)+","+str(coefs[i])+"\n"
                    info_string2+="Equation Constant: "+str(const)+"\n"
                    info_string = info_string1+info_string2+"\n"
                    outfile.write(info_string)
                elif not pred_strings:
                    outfile.write("No equation information available for station: "+sta+" for predictand: "+tand.tostring()+"\n\n")
            outfile.write("\n")
        outfile.close()
    # Raise error if neither first nor second use case are met
    else:
        raise ValueError("Either coefficients and predictors arguments OR filepath argument must be given")

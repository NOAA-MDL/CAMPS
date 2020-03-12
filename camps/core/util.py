import sys
import os
from datetime import datetime, timedelta
import csv
import logging
import string
import pdb
from . import Time


"""Module: util.py

Methods:
    generate_date_range
    read_station_list
    read_station_table
    station_trunc
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
                delta = timedelta(hours=int(dr_stride.translate(None,string.letters)))
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
    stalist_from_table = station_dict.keys()
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

import os
import sys
import csv



def read_station_definitions(file_path):
    """
    Reads all station definitions from file defined in control
    file. Returns a dictionary where the keys are the station
    call letters and has dictionary values such that
    {lat: xxx, lon:yyy}.
    Positive values indicate North or West, while
    negative values indicate South or East.
    """
    station_dict = {}
    with open(file_path, 'r') as f:
        reader = csv.reader(f, delimiter=":", quoting=csv.QUOTE_NONE)
        for row in reader:
            call = row[0].strip(' ')
            if call not in station_dict:  # So we will only take the
                long_name = row[2]       # first definition for a call
                state = row[3]           # in the case of dupes.
                code = row[5]
                lat = row[6]
                lon = row[7]
                # Positive North
                if lat[0] == 'N':
                    lat = float(lat[1:])
                else:
                    lat = -float(lat[1:])
                # Negative West
                if lon[0] == 'W':
                    lon = -float(lon[1:])
                else:
                    lon = float(lon[1:])

                station_dict[call] = {}
                station_dict[call]['lat'] = lat
                station_dict[call]['lon'] = lon
                station_dict[call]['long_name'] = long_name
                station_dict[call]['code'] = code
    return station_dict


def strip_array(arr):
    """
    Strips whitespace out of an array of strings.
    Will fail if not given a string list.
    """
    return [word.strip(' ') for word in arr]


def read_valid_stations(file_path):
    """
    Reads the valid METAR stations from file defined
    in control file. Returns them as a set.
    """
    station_list = set()
    with open(file_path, 'r') as f:
        station_list = f.read().splitlines()
    station_list = strip_array(station_list)
    return station_list



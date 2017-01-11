import sys, os
file_dir = os.path.dirname(os.path.realpath(__file__))
relative_path = "/.."
path = os.path.abspath(file_dir + relative_path)
sys.path.insert(0, path)

from collections import defaultdict
from station import station
import csv
import os
import logging
import pdb
from qc_error import qc_error as qce
import qc_error 
import registry.util as cfg

class metarreader():
    """
    Class for reading METAR formatted files.
    If the instance variable 'filename' is defined in the object
    and exists as a METAR formatted file, calling read will 
    add stations to the station_list.
    """
    
    obs_type = "METAR"
     
    # Specify input filename.
    # Specify output directory -- will append data to filename.
    def __init__(self,filename=None):
        """
        Initializes station dictionaries, and observation list.
        """
        self.filename = filename
        self.obs_time = None
        self.observations = []
        self.station_list = {}

        # Read valid and defined stations
        def_path = cfg.read_metar_control()['station_defs']
        val_path = cfg.read_metar_control()['valid_stations']
        self.station_definitions = self.read_station_definitions(def_path)
        self.valid_stations = self.read_valid_stations(val_path)
    
    def read_valid_stations(self, file_path):
        """ 
        Reads the valid METAR stations from file defined
        in control file. Returns them as a list.
        """
        station_list = set()
        with open(file_path, 'r') as f:
            station_list = f.read().splitlines()
        station_list = strip_array(station_list)
        return station_list
    
    def read_station_definitions(self, file_path):
        """
        Reads all station definitions from file defined in control
        file. Returns a dictionary where the keys are the station
        call letters and has dictionary values such that
        {lat: xxx, lon:yyy}.
        """
        station_dict = {}
        with open(file_path,'r') as f:
            reader = csv.reader(f, delimiter=":", quoting=csv.QUOTE_NONE)
            for row in reader:
                call = row[0].strip(' ')
                if call not in station_dict: # So we will only take the
                    long_name = row[2]       # first definition for a call
                    state = row[3]           # in the case of dupes.
                    code = row[5]
                    lat = row[6]
                    lon = row[7]
                    if lat[0] == 'N':
                        lat = float(lat[1:])
                    else:
                        lat = -float(lat[1:])
                    if lon[0] == 'W':
                        lon = float(lon[1:])
                    else:
                        lon = -float(lon[1:])
                    
    
                    station_dict[call] = {}
                    station_dict[call]['lat'] = lat
                    station_dict[call]['lon'] = lon
        return station_dict
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                


    def read(self):
        """
        Starts reading self.filename.
        """
        with open(self.filename, "r") as metar_file:
            metar_reader = csv.reader(metar_file, delimiter=":" ) 
            self.parse_file(metar_reader)
    
    def parse_file(self, metar_reader):
        """
        Parses the file, creates station objects, for the observations.
        """
        file_header = metar_reader.next() #pull out the first line and parse it
        self.parse_header(file_header)
        self.observations = metar_reader.next() #pull out the second line -- data 
        self.observations.pop(0) # We don't need CALL
        self.observations.pop() # csv file has an extra ':' at the end. 
                                # I should probably preprocess them
        self.observations = strip_array(self.observations)

        for row in metar_reader:
            # METAR files last line contain a ZZZZZZZZ
            if row[0] != 'ZZZZZZZZ':
                name = row.pop(0).strip() # get the station name
                row.pop()                 # remove last empty element

                if name not in self.station_list:
                    if name in self.valid_stations:
                        #self.station_list[name] = station(name,station_type)
                        self.station_list[name] = station(name)
                        self.station_list[name].add_record(self.observations, 
                                                          row, 
                                                          self.obs_time,
                                                          new=True)
                else:
                    self.station_list[name].add_record(self.observations, \
                                                          row, \
                                                          self.obs_time)

    def parse_header(self, first_row):
        """
        Extracts header information from 'first_row'
        """
        self.obs_time = first_row[0][30:40] # hardcoded

    def check_latlon(self):
        """
        Checks if the latitude on longitude of the stations
        are within bounds of station definitions.
        """
        for station in self.station_list.values():
            station_def = self.station_definitions[station.name]
            lat = float(station.get_obs('LAT')[0])
            lon = float(station.get_obs('LON')[0])
            lat_diff = abs(lat - station_def['lat'])
            lon_diff = abs(lon - station_def['lon'])
            if lat_diff > .1:
                qc_error.all_qc_errors.append(
                        qce(
                                station_name=station.name,\
                                error_code=9000,\
                                old_data_value=lat,
                                explanation= \
                                "lats are different for: " + station.name + \
                                ". Old value : " +str(station_def['lat'])
                        ))
            if lon_diff > .1:
                qc_error.all_qc_errors.append(
                        qce(
                                station_name=station.name,\
                                error_code=9000,\
                                old_data_value=lon,
                                explanation= \
                                "lons are different for: " + station.name + \
                                ". Old value : " + str(station_def['lon'])
                        ))


def strip_array(arr):
    """
    Strips whitespace out of an array of strings.
    Will fail if not given a string list.
    """
    return [word.strip(' ') for word in arr]


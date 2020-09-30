import sys
import os
from collections import defaultdict
import csv
import os
import logging
import pdb

from .station import station
from .qc_error import qc_error as qce
from . import qc_error
from ....registry import util as cfg



"""Module: metarreader.py

Class: metarreader
    Methods:
        __init__
        read_valid_stations
        _fill_missing
        read
        parse_header
        check_latlon

Methods:
    strip_array
"""



class metarreader():
    """Class for reading METAR formatted files.  If the instance variable 'filename' is
    defined in the object and exists as a METAR formatted file, calling read will
    add stations to the station_list.
    """

    obs_type = "METAR"


    def __init__(self, stn_tbl, stn_lst, filename=None):
        """Initializes station dictionaries, and observation list."""

        self.filename = filename
        self.obs_time = 0
        self.observations = []
        self.station_list = {}
        self.read_count = 0

        # Create file object
        self._metar_file = open(self.filename,"rt")
        self._metar_reader = csv.reader(self._metar_file,delimiter=":")

        # Read valid and defined stations
        self.station_definitions = stn_tbl
        self.valid_stations = stn_lst

        # Create dictionary where station name is the key and value is
        # an instance of station.station.
        for s in self.valid_stations:
            self.station_list[s] = station(s)


    def _fill_missing(self,stations):
        """Fill all obs for a station in stations with missing."""

        # We have now read all obs for a given hour. Some stations might be missing, so
        # here check for missing obs for expected stations
        for name in list(self.station_list.keys()):
            if name not in stations:
                logging.debug("No obs available for station "+name+" for date = "+str(self.obs_time))
                self.station_list[name].add_empty_record(self.observations,-1,self.obs_time)


    def read(self,date,advance=True):
        """Read MDL Hourly obs file, creates station objects, for the observations."""

        station_list_check = []
        if advance:
            file_header = next(self._metar_reader)
            self.parse_header(file_header)
            self.observations = next(self._metar_reader)
            self.observations.pop(0) # This removes "CALL" from the ob name row
            self.observations.pop()  # Remove extra column
            self.observations = strip_array(self.observations)

        if self.obs_time < date:
            logging.debug("Skipping date "+self.obs_time)
            for row in self._metar_reader:
                if row[0] == 'ZZZZZZZZ':
                    break
            self.read(date)

        elif self.obs_time == date:
            logging.info("Reading METAR Obs for date = "+self.obs_time)
            #self.observations = self._metar_reader.next()
            #self.observations.pop(0) # This removes "CALL" from the ob name row
            #self.observations.pop()  # Remove extra column
            #self.observations = strip_array(self.observations)

            # Iterate over every row (ob) for a given hour; get and catalog the station name
            # of the ob. If it exists in the user input station list, then capture the obs.
            for row in self._metar_reader:
                if row[0] == 'ZZZZZZZZ':
                    break
                name = row.pop(0).strip() # Get the station name
                station_list_check.append(name)
                row.pop()                 # Remove last empty element
                if name in list(self.station_list.keys()):
                    self.station_list[name].add_record(self.observations,
                                                       row,
                                                       self.obs_time)
            self._fill_missing(station_list_check)

        elif self.obs_time > date:
            # IMPORTANT: We should only come here if a date that we want process is
            # missing in the input file.
            logging.warning("No METAR Obs for date "+date+". Data set to missing.")
            #for row in self._metar_reader:
            #    if row[0] == 'ZZZZZZZZ':
            #        break
            self._fill_missing(station_list_check)

        self.read_count += 1


    def parse_header(self, first_row):
        """Extracts header information from 'first_row'. """

        self.obs_time = first_row[0][30:40]  # hardcoded


    def check_latlon(self):
        """Checks if the latitude on longitude of the stations
        are within bounds of station definitions.
        """

        for station in list(self.station_list.values()):
            station_def = self.station_definitions[station.name]
            lat = float(station.get_obs('LAT')[0])
            lon = float(station.get_obs('LON')[0])
            lat_diff = abs(lat - station_def['lat'])
            lon_diff = abs(lon - station_def['lon'])
            if lat_diff > .1:
                qc_error.all_qc_errors.append(
                    qce(
                        station_name=station.name,
                        error_code=9000,
                        old_data_value=lat,
                        explanation="lats are different for: " + station.name +
                        ". Old value : " + str(station_def['lat'])
                    ))
            if lon_diff > .1:
                qc_error.all_qc_errors.append(
                    qce(
                        station_name=station.name,
                        error_code=9000,
                        old_data_value=lon,
                        explanation="lons are different for: " + station.name +
                        ". Old value : " + str(station_def['lon'])
                    ))


def strip_array(arr):
    """Strips whitespace out of an array of strings.
    Will fail if not given a string list.
    """

    return [word.strip(' ') for word in arr]

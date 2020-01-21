import sys
import os
from collections import defaultdict
import csv
import os
import logging
import pdb

from ..metar_to_nc.station import station
from ....registry import util as cfg

class marinereader():
    """
    Class for reading NDBC QC'ed Marine text files. If the instance variable 'filename' is
    defined in the object and exists as a Marine formatted file, calling read will
    add stations to the station_list.
    """

    obs_type = "MARINE"

    def __init__(self,stn_tbl,stn_lst,filename=None):
        """
        Initializes station dictionaries, and observation list.
        """
        self.filename = filename
        self.obs_time = None
        self.observations = []
        self.station_list = {}

        # Create file object
        self._marine_file = open(self.filename,"rt")
        self._marine_reader = csv.reader(self._marine_file,delimiter=":")

        # Read valid and defined stations
        self.station_definitions = stn_tbl
        self.valid_stations = stn_lst

        # Create dictionary where station name is the key and value is
        # an instance of station.station.
        for s in self.valid_stations:
            self.station_list[s] = station(s)


    def read(self,end_date=None):
        """
        Read NDBC Hourly obs file, creates station objects, for the observations.
        """
        # These 2 lines read the Marine archive file header. The first line
        # contains variable names; the second contains a decimal scale factor
        # for each 
        eof = False
        file_header = self._marine_reader.next()[4:]
        decscale_header = self._marine_reader.next()[4:]
        decscale_header.pop()
        decscale = [10.0**float(s) for s in decscale_header] # Convert to actual scale floats
        self.observations = file_header
        self.observations.pop()  # Remove extra column
        self.observations = strip_array(self.observations)

        # Add TYPE and TIME. These values are not in the NDBC Monthly Obs file.
        self.observations.append('TYPE')
        self.observations.append('TIME')

        # Iterate over every row (ob) for a given hour; get and catalog the station name
        # of the ob. If it exists in the user input station list, then capture the obs.
        idate = 0
        self.obs_time = 0
        station_list_check = []
        for row in self._marine_reader:

            # Conditions to break the loop
            if row[0] == '99999999':
                break
            idate = (int(row[0])*100)+int(row[1])
            if idate > int(end_date):
                # If we are here, we are done reading, but we still need to
                # check for missing obs from the last date.
                self.check_missing_obs(station_list_check)
                break
            if idate > int(self.obs_time):
                # Here means we are at a new date
                if int(self.obs_time) > 0:
                    self.check_missing_obs(station_list_check)
                logging.info("READING MARINE OBS FOR DATE "+str(idate))
                station_list_check = []

            # Get some information from the row (observation)
            name = row[3].strip() # Get the station name
            station_list_check.append(name)
            self.obs_time = str(idate)
            obs_hour = row[1] # Get the hour of the obs before removing items
            row = row[4:] # Remove elements 0-3
            row.pop() # Remove last empty element

            # Apply decimal scale factor. IMPORTANT: Some variables need to be
            # converted to int, then back to string. NumPy cannot convert a
            # float as a string and cast as in int so we do that here.
            for i,(obname,ob,ds) in enumerate(zip(self.observations,row,decscale)):
                if int(ob) != 9999:
                    if obname in ['AWPD','DWPD','TEMP','WDIR','WGST','WTMP','WVDR','WVHT']:
                        row[i] = str(int(float(ob)*ds))
                    else:
                        row[i] = str(float(ob)*ds)

            # Add TYPE and TIME values for each hourly observation.
            row.append('MARI')
            row.append(obs_hour+'00')

            # Added the station observation to the marinereader object.
            if name in self.station_list.keys():
                self.station_list[name].add_record(self.observations,
                                                   row,
                                                   self.obs_time)


    def check_missing_obs(self,stnlist):
        # We have now read all obs for a given hour. Some stations might be missing, so
        # here check for missing obs for expected stations
        for name in self.station_list.keys():
            if name not in stnlist:
                logging.debug("NO OBS AVAILABLE FOR STATION "+name+" FOR HOUR "+str(self.obs_time))
                self.station_list[name].add_empty_record(self.observations,-1,self.obs_time)


    def check_latlon(self):
        """
        Checks if the latitude and longitude of the stations
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
    """
    Strips whitespace out of an array of strings.
    Will fail if not given a string list.
    """
    return [word.strip(' ') for word in arr]

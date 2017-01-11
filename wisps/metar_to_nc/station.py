import logging
from datetime import datetime
from datetime import timedelta
import pdb
import enumerations
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool

MISSING_VALUE = 9999

class station:

    def __init__(self, name):
        self.name = name
        self.long_name = None
        # Where the keys are the METAR names of the observations, 
        # and the values are an array representing the hourly data
        self.observations = {}
        # Hours are represented YYYYMMDDHH
        self.hours = []  

    def get_obs(self, obs_str):
        """
        Returns and array of the given observation string. e.g. 'TMP' would
        return the temperature array of the station.
        """
        obs_str = obs_str.upper()
        obs_arr = self.observations.get(obs_str, None)
        if obs_arr is not None:
            return obs_arr
        #TODO check for alternate names
        return obs_arr

    def add_record(self, observation_keys, values, hour, new=False):
        """
        Appends to the data for a given time period
        to the predictor dictionary for this station.
        'observation_keys' is an array of all observations keys e.g. 'TMP', in METAR file.
        'values' is a string list
        'hour' is the hour of this observation
        'new' is boolean indicating it's the first record
        """
        #if(len(observation_keys) is not len(values)):
        #    raise RuntimeWarning("the number of given observation_keys and " \
        #                         "associated values do not match")
        # This will become True if a duplicate station
        # at given time is closer to the 50
        if new:
            for ob in observation_keys:
                self.observations[ob] = []; 

        remove_dupe = False
        unknown_station_type = 9
        # enumerate station type
        #type_index = observation_keys.index('TYPE')
        #unknown_station_type = 'UNKN'
        #if values[type_index] != unknown_station_type:
        if values[0] != 'UNKN':
           if self.check_duplicate_time(hour):
               if self.is_closer_time(values,observation_keys):
                   # exit this function, because existing record was closer
                   return
               remove_dupe = True
           else:
               self.hours.append(hour)

        for ob, datum in zip(observation_keys,values):
            datum = datum.strip()
            # assigns the function that will handle special-case string observations
            # returns None if enumeration is not necessary
            datum = enumerations.get_enumeration_function(ob)(datum)
            if datum == '':
                datum = MISSING_VALUE
            if remove_dupe:
                self.observations[ob][-1] = datum
            else:
                self.observations[ob].append(datum)

    def get_region(self):
        """
        Returns this station's region based on its lat/lon.
        Return values will be one of the following:
        'southeast'
        'southwest'
        'northeast'
        'northwest'
        'farnorth'
        """
        if "LAT" in self.observations and "LON" in self.observations:
            # Choose the first lat and lon
            lat = self.observations["LAT"][0]
            lon = self.observations["LON"][0]
            if lat > 50:
                return "farnorth"
            if lat > 35:
                prefix = "north"
            else:
                prefix = "south"
            if lon > 100:
                suffix = "west"
            else:
                suffix = "east"
            return prefix + suffix
        return None

    def get_epoch_time(self):
        """ Return hours array as seconds since the epoch """
        epoch = datetime.utcfromtimestamp(0)
        unix_time = lambda dt: (dt-epoch).total_seconds() 
        return [unix_time(self.parse_hour_to_datetime(i)) for i in self.hours]

    def get_season(self,string_return=True):
        """
        Returns the season as a string, or
        if specified by 'string_return=False' a number, where,
        'spring' : 0
        'summer' : 1
        'fall'   : 2
        'winter' : 3
        Assume that the duration of a station record will
        never be more than about a month .
        """
        # Get a middle date in the record.
        date = self.hours[len(self.hours)/2]
        month = int(date[4:6])
        if month >= 3 and month <= 5:
            if string_return:
                return "spring"
            return 0
        if month >= 6 and month <= 8:
            if string_return:
                return "summer"
            return 1
        if month >= 9 and month <= 11:
            if string_return:
                return "fall"
            return 2
        if month == 12 or month <= 2:
            if string_return:
                return "winter"
            return 3

    def add_empty_record(self, index, hour):
        """
        Takes in index for the hours object data field and the hour that 
        should be inserted. This routine should be used when a station is not 
        represented in a METAR file. This will give MISSING values too obersvations
        for the given hour.
        """
        for obs_name, obs_list in self.observations.iteritems():
            obs_list.insert(index, MISSING_VALUE)
        self.hours.insert(index,hour)
    
    def fill_empty_records(self, start=None, end=None, delta=None):
        """ 
        start and end should both be datetime's. delta should be a timedelta. 
        This subroutine will identify any time gaps within a given time 
        period an optional delta time in any of the station records
        and replace them with missing values
        """
        # If arguments not given, assume the range is the start and end of the 
        # self.hours array, and the delta time is 1 hour
        if not start:
            start = parse_hour_to_datetime(self.hours[0])
        if not end:
            end = parse_hour_to_datetime(self.hours[len(hours)-1])
        if not delta:
            delta = timedelta(hours=1)
        hours_index = 0
        while start <= end:
            try:
                cur_time = self.hours[hours_index]
            except IndexError as e:
                # If the current index is out of bounds, and the loop has not yet 
                # reached the end of the time range, add an empty record to the end
                self.add_empty_record(hours_index,\
                        self.parse_datetime_to_hour(start))
                continue
            cur_time = self.parse_hour_to_datetime(cur_time)
            while start < cur_time :
                self.add_empty_record(hours_index,\
                        self.parse_datetime_to_hour(start))
                start += delta
                hours_index += 1
            hours_index += 1 
            start += delta
            
    def parse_datetime_to_hour(self, time):
        """ 
        Assumed that time is a datetime object.
        hours are represented YYYYMMDDHH
        """
        return str(time.year).zfill(4) + str(time.month).zfill(2) \
                + str(time.day).zfill(2) + str(time.hour).zfill(2)

    def parse_hour_to_datetime(self, time):
        """
        Assumed that time is in form YYYYMMDDHH, which is the format of the
        self.hours array.
        """
        year = int(time[:4])
        month = int(time[4:6])
        day = int(time[6:8])
        hour =  int(time[8:10])
        return datetime(year,month,day,hour)

    def check_duplicate_time(self, cur_hour):
        """Given cur_hour, returns if it is a duplicate to the last entered time"""
        if self.hours:
            most_recent_hour = self.hours[-1]
            return cur_hour == most_recent_hour # We've got dupes
        return False
    
    def is_closer_time(self, station_obs, predictors):
        """ 
        Returns a boolean based on whether the old station_obs is
        closer to 50 of the hour. MANU observations are selected over
        Automated observations. This function expects that the argument,
        station_obs, is from the same hourly record as the current last time. 
        """
        # First check station type
        new_station_type =  station_obs[predictors.index('TYPE')]
        old_station_type = self.observations['TYPE']
        old_station_type = old_station_type[len(old_station_type)-1]
        if new_station_type == 'MANU' and old_station_type != 1:
            return False
        if new_station_type != 'MANU' and old_station_type == 1:
            return True
        
        new_time =  station_obs[predictors.index('TIME')]
        old_time = self.observations['TIME']
        old_time = old_time[len(old_time)-1]
        # extract the hour
        new_time  = new_time.strip()[-2:]
        old_time  = old_time.strip()[-2:]
        # cast to int
        new_time = int(new_time)
        old_time = int(old_time)
        if new_time < 30:
            new_time+=60
        if old_time < 30:
            old_time+=60
        return  abs(old_time - 50) < abs(new_time - 50) 

    def is_auto(self,i):
        """Return true if station is an automatic station"""
        type_arr = self.get_obs("TYPE")
        return type_arr[i] >= 2 and type_arr[i] <= 8

    def is_AO2_or_MANU(self, i):
        """
        return true if station is a manual station (MANU) 
        or if AO2 or AO2A.
        """
        type_arr = self.get_obs("TYPE")
        return type_arr[i] >= 1 and type_arr[i] <= 3

    def is_canadian(self):
        return self.name[:1] == 'C' 

    def is_russian(self):
        return self.name[:2] == 'UH' or self.name[:2] == 'UE'

    def __str__(self):
        return self.name
    
    __repr__ = __str__
 






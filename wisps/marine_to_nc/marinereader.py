from collections import defaultdict
import csv
import os
import pdb


class marinereader():
    """
    Class to read Marine CSV text files.
    """

    obs_type = "marine"

    def __init__(self, filename="undefined"):
        """
        Initializes class variables.
        """
        self.filename = filename
        self.obs_time = None
        self.observations = []
        self.station_list = {}
        self.dates = []

    def read(self, start_date=None, end_date=None):
        """
        Reads the file stored in self.filename and
        stores the results as a station list dictionary.
        """
    #    try:
        with open(self.filename, "r") as marine_file:
            marine_reader = csv.reader(marine_file, delimiter=":")
            self.parse_file(marine_reader, start_date, end_date)
    #     except Exception as e:
    #         print "Error reading csv file"
    #         print e
        return self.station_list

    def parse_file(self, marine_reader, start_date, end_date):
        """
        Takes an csv reader argument where each iteratable item contains
        an array representing the observation of a station at a given hour
        """
        # The first line contains the names of the observations
        # Remove first 4 elements (date/station name information)
        self.observations = marine_reader.next()[4:]

        # The second line does indicate anything important
        marine_reader.next()

        # csv file has an extra ':' at the end. Remove it.
        # Future: preprocess them off
        self.observations.pop()

        # Remove whitespace around variables
        self.observations = strip_array(self.observations)

        # used for filling in empty records
        cur_date = "99999"
        n_records = 0

        # Loop through the file. Each row is line of the csv file parsed into a
        # list.
        for row in marine_reader:
            year_month_day = row.pop(0)
            # the file's last entry is an empty 99999999
            if year_month_day != '99999999':
                obs_hour = row.pop(0)
                obs_minute = row.pop(0)
                if obs_minute == '99':
                    obs_minute = "00"
                date = year_month_day + obs_hour

                # Upon hitting a new date, backfill any data that
                # was not reported by the stations for the previous date
                if cur_date != date:
                    self.fill_empty_records(n_records)
                    n_records += 1
                    cur_date = date
                    self.dates.append(cur_date)

                # If the end date is hit. Work is done. Exit.
                if(end_date is not None and end_date == date):
                    self.dates.pop()
                    return self.station_list

                # Otherwise, append the station data to the end of the
                # station's data
                station_name = row.pop(0)
                station_name = station_name.strip(' ')
                row.pop()  # remove last null element
                row = strip_array(row)

                if station_name not in self.station_list:
                    self.station_list[station_name] = [row]
                else:
                    self.station_list[station_name].append(row)

    def fill_empty_records(self, n_records, num_obs=14):
        """
        Method to append empty records to station_list up to
        n_records. If only 1 record is in a station,
        fills records from previous dates.
        """
        empty_record = ['9999'] * num_obs
        for station_name, observations in self.station_list.iteritems():
            r_len = len(observations)

            # If there are two entries for the same period
            if r_len > n_records:
                self.station_list[station_name].pop()
            else:
                # Fill empty records
                for i in range(r_len, n_records):
                    self.station_list[station_name].append(empty_record)
                    # Fill before record when it's the station's first record
                    # added
                    if r_len == 1:
                        self.station_list[station_name].reverse()


def strip_array(arr):
    """
    Strips whitespace out of an array of strings.
    Will throw TypeError if not given a string list.
    """
    return [word.strip(' ') for word in arr]

#!/usr/bin/env python
import os
import sys
file_dir = os.path.dirname(os.path.realpath(__file__))
relative_path = '/..'
path = os.path.abspath(file_dir + relative_path)
sys.path.insert(0, path)
import util


def test_read_station_definitions():
    """  """
    station_dict = util.read_station_definitions('station_def.sub.tbl')
    assert station_dict['CYUB']['lat'] == 69.4333
    assert station_dict['KEFC']['lon'] == 103.8620

def test_read_valid_stations():
    station_list = util.read_valid_stations('devsites.sub.lst')
    assert 'KMLP' in station_list


if __name__ == "__main__":
    test_read_station_definitions()
    test_read_valid_stations()
    print "test_util passed"
    

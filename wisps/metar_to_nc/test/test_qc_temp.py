import os
import sys
import re
relative_path = os.path.abspath(
        os.path.dirname(os.path.realpath(__file__)) + "/..")
sys.path.insert(0, relative_path)
from qc_general import *
import numpy as np
import pdb

MISSING_VALUE = 9999


def test_synoptic():
    print "#########################"
    print "## Testing synoptic QC ##"
    print "#########################"
    test_hour = ["2016010400", "2016010401", "2016010402", "2016010403", "2016010404",
                 "2016010405", "2016010406", "2016010406", "2016010407", "2016010408"]
    test_1h_array = np.array([35, 70, 35, 35, 35, 35, 35, 35, 35, 35])
    test_6h_array = np.array([35, 35, 35, 35, 35, 35, 35, 35, 35, 35])
    station_type = np.array([1, 1, 1, 1, 1, 1, 1, 1, 1, 1])
    assert_result = np.array([35, 35, 35, 35, 35, 35, 9999, 35, 35, 35])

    # pdb.set_trace()
    check_6hour_max(test_1h_array, test_6h_array, test_hour, station_type)
    np.testing.assert_array_equal(test_6h_array, assert_result)
    print "PASSED test 1"
    # Changed anomaly to not the first or last index
    test_1h_array = np.array([35, 35, 70, 35, 35, 35, 35, 35, 35, 35])
    assert_result = np.array([35, 35, 35, 35, 35, 35, 9999, 35, 35, 35])
    print "PASSED test 2"

    print "checking long if statement"
    extrema = 31
    synoptic = 30
    indicies = [0]
    assert compound_if_statement(extrema, synoptic, indicies) == False
    print "PASSED test 1"
    extrema = 32
    assert compound_if_statement(extrema, synoptic, indicies) == False
    print "PASSED test 2"
    extrema = 32
    indicies = [3]
    assert compound_if_statement(extrema, synoptic, indicies) == False
    print "PASSED test 3"
    extrema = 31
    indicies = [3]
    assert compound_if_statement(extrema, synoptic, indicies) == True
    print "PASSED test 4"
    indicies = [0]
    assert compound_if_statement(extrema, synoptic, indicies) == False
    print "PASSED test 5"
    indicies = [5]
    assert compound_if_statement(extrema, synoptic, indicies) == False
    print "PASSED test 6"
    indicies = [5, 0]
    assert compound_if_statement(extrema, synoptic, indicies) == True
    print "PASSED test 7"
    extrema = 32
    indicies = [5, 0]
    assert compound_if_statement(extrema, synoptic, indicies) == False
    print "PASSED test 8"


def compound_if_statement(extrema, synoptic, indicies):
    hourly_values = [30, 30, 30, 31, 30, 30]  # anything, just need len
    if ((
            extrema - synoptic == 1 and len(indicies) > 1
    )
        or (
            (extrema - synoptic) == 1 and len(indicies) == 1
        and (indicies[0] != 0 and indicies[0] != len(hourly_values) - 1)
    )):
        return True
    return False


def test_consistancy():
    # Case where value is just wrong
    print "############################"
    print "## Testing consistency QC ##"
    print "############################"
    test_array = np.array([35, 35, 35, 35, 100, 35])
    station_type = np.array([2, 2, 2, 2, 2, 2])
    assert_result = np.array([35, 35, 35, 35, 9999, 35])
    check_consistency(test_array, station_type, 10)
    np.testing.assert_array_equal(test_array, assert_result)
    print "PASSED test 1"

    test_array = np.array([9999, 35, 35, 35, 35, 9999])
    assert_result = np.array([9999, 35, 35, 35, 35, 9999])
    check_consistency(test_array, station_type, 10)
    np.testing.assert_array_equal(test_array, assert_result)
    print "PASSED test 2"

    # wierd case, but this is what it should give
    test_array = np.array([35, 35, 120, 9999, -120, 35])
    assert_result = np.array([35, 35, 120, 9999, -120, 35])
    check_consistency(test_array, station_type, 10)
    np.testing.assert_array_equal(test_array, assert_result)
    print "PASSED test 3"

    test_array = np.array([31, 42, 53, 64, 75, 86])
    assert_result = np.array([31, 42, 53, 64, 75, 86])
    check_consistency(test_array, station_type,  10)
    np.testing.assert_array_equal(test_array, assert_result)
    print "PASSED test 4"


def test_dew_point():
    print "############################"
    print "## Testing check_dewpoint ##"
    print "############################"
    dewpoint = np.array([56, 56, 56, 56, 56])
    temper = np.array([56, 56, 55, 56, 56])
    result = np.array([56, 56, 55, 56, 56])
    # pdb.set_trace()
    check_dewpoint(dewpoint, temper)
    np.testing.assert_array_equal(dewpoint, result)

    print "PASSED test 1"


def test_min_max():
    print "#####################"
    print "## Testing min_max ##"
    print "#####################"
    print "test 1:"
    min_arr = np.array([2, 2, 2, 2, 2])
    max_arr = np.array([2, 2, 1, 2, 2])
    assert_arr = np.array([2, 2, 9999, 2, 2])
    qc_general.check_min_max(min_arr, max_arr)
    np.testing.assert_array_equal(min_arr, assert_arr)
    np.testing.assert_array_equal(max_arr, assert_arr)
    print "PASSED test1"


def test_bounds():
    print "####################"
    print "## Testing bounds ##"
    print "####################"
    arr = np.array([1, 2, 3, 4, 5])
    assert_arr = np.array([9999, 2, 3, 9999, 9999])
    qc_general.check_bounds(arr, 2, 3)
    np.testing.assert_array_equal(arr, assert_arr)
    print "PASSED test1"

if __name__ == "__main__":
    test_min_max()
    test_dew_point()
    test_synoptic()
    test_consistancy()

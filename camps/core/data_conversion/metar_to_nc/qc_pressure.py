import logging
import os
from . import qc_general
from .qc_error import qc_error
from . import qc_error
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool



"""Module: qc_pressure.py

Methods:
    qc_pressure
    qc_pressure_st
"""


MISSING_VALUE = 9999


def qc_pressure(station_list):

    all_errors = []
    num_processors = int(os.getenv('NUM_PROCS', 8))
    pool = Pool(num_processors)
    all_errors = pool.map(qc_pressure_st, station_list)
    pool.close()
    pool.join()

    return all_errors


def qc_pressure_st(station):

    all_errors = []
    pressure = station.get_obs("MSL")
    altimeter = station.get_obs("ALT")
    station_type = station.get_obs("TYPE")

    # scale factor is 10

    errors = qc_general.check_bounds(pressure, 875, 1075)
    qc_error.set_all_attr(errors, "error_code", 9601)
    qc_error.set_all_attr(errors, "station_name", station.name)
    all_errors += errors

    tolerance = 3.4

    errors = qc_general.check_consistency(pressure, station_type, tolerance)
    qc_error.set_all_attr(errors, "error_code", 9603)
    qc_error.set_all_attr(errors, "station_name", station.name)
    all_errors += errors

    # scale factor is 100

    tolerance = .1

    errors = qc_general.check_bounds(altimeter, 24, 32)
    qc_error.set_all_attr(errors, "error_code", 9602)
    qc_error.set_all_attr(errors, "station_name", station.name)
    all_errors += errors

    errors = qc_general.check_consistency(altimeter, station_type, tolerance)
    qc_error.set_all_attr(errors, "error_code", 9604)
    qc_error.set_all_attr(errors, "station_name", station.name)
    all_errors += errors

    return all_errors

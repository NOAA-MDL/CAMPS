import logging
import os
from . import qc_general
import pdb
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool
from .qc_error import qc_error


"""Module: qc_clouds.py

Methods:
    qc_clouds
    qc_clouds_st
    set_all_to_missing
    qc_clouds_test
"""


MISSING_VALUE = 9999



def qc_clouds(station_list):

    errors = []
    all_errors = []
    pool = Pool()
    num_processors = int(os.getenv('NUM_PROCS', 8))
    pool = Pool(num_processors)
    all_errors = pool.map(qc_clouds_st, station_list)
    pool.close()
    pool.join()
    # for station in station_list:
    #    qc_temp_st(station)

    return all_errors


def qc_clouds_st(station):

    errors = []
    cloud_height = []
    cloud_amount = []
    # package the heights in an array
    for i in range(1, 7):
        cloud_height.append(station.get_obs("CH" + str(i)))
        cloud_amount.append(station.get_obs("CA" + str(i)))

    num_hours = len(station.hours)
    for hour in range(0, num_hours):
        date = station.hours[hour]
        prev_height = -999
        prev_amount = -999
        # First, check for a clear sky
        if cloud_amount[0][hour] == 0 or cloud_amount[0][hour] == 1:
            set_all_to_missing(cloud_height, hour)
            set_all_to_missing(cloud_amount, hour)
            cloud_amount[0][hour] = 0
            cloud_height[0][hour] = 888
            continue
        # Check for POB (Partially OBscured) in group 1
        if cloud_amount[0][hour] == 9 and cloud_height[0][hour] != 0:
            errors.append(qc_error(
                station_name=station.name, date_of_error=date,
                error_code=9531, old_data_value=cloud_height[0][hour],
                new_data_value=0,
                explanation="First group for cloud amount is POB,"
                " (partially obscured sky)"
            ))
            cloud_height[0][hour] = 0
        # Check if KMWN or KMWS reported POB in first and second cloud amounts
        # which represents fog in the valley below station.
        if (station.name == 'KMWN' or station.name == 'KMWS') \
                and cloud_amount[0][hour] == 8 and cloud_amount[1][hour] == 8:
            # shift groups down by 1 and set group 6 to missing
            for i in range(1, 6):
                cloud_amount[i - 1][hour] = cloud_amount[i][hour]
                cloud_height[i - 1][hour] = cloud_height[i][hour]
            cloud_amount[5][hour] = MISSING_VALUE
            cloud_height[5][hour] = MISSING_VALUE
            errors.append(qc_error(
                station_name=station.name, date_of_error=date,
                error_code=9540, old_data_value=amount_layer[hour],
                new_data_value=MISSING_VALUE,
                explanation="POB reported, but not in first cloud group"
            ))
        for j, tup in enumerate(zip(cloud_height, cloud_amount)):
            height_layer, amount_layer = tup
            # Check if POB is not in first group
            if (station.name != 'KMWN' or station.name != 'KMWS') \
                    and j != 0 and amount_layer[hour] == 9:
                errors.append(qc_error(
                    station_name=station.name, date_of_error=date,
                    error_code=9541, old_data_value=amount_layer[hour],
                    new_data_value=MISSING_VALUE,
                    explanation="POB reported, but not in first cloud group."
                    "\ngroup  : " + str(j + 1) +
                    "\ngroup 1: " + str(cloud_amount[0][hour])
                ))
                set_all_to_missing(cloud_height, hour)
                set_all_to_missing(cloud_amount, hour)
            # Check out of bounds height
            if height_layer[hour] != MISSING_VALUE \
                    and height_layer[hour] > 450:
                set_all_to_missing(cloud_height, hour)
                set_all_to_missing(cloud_amount, hour)
                errors.append(qc_error(
                    station_name=station.name, date_of_error=date,
                    error_code=9500, old_data_value=height_layer[hour],
                    new_data_value=MISSING_VALUE,
                    explanation="Cloud height is out of range (>45000 ft)"
                ))
            # Check that cloud heights are reported correctly.
            if height_layer[hour] > 50 and height_layer[hour] <= 100 \
                    and height_layer[hour] % 5 != 0 and \
                    not station.is_canadian():
                set_all_to_missing(cloud_height, hour)
                set_all_to_missing(cloud_amount, hour)
                errors.append(qc_error(
                    station_name=station.name, date_of_error=date,
                    error_code=9501, old_data_value=height_layer[hour],
                    new_data_value=MISSING_VALUE,
                    explanation="cloud height is greater than "
                    "5,000 ft and less than 10,000 ft"
                    "and not rounded to the nearest 10"
                ))
            elif height_layer[hour] > 100 and \
                    height_layer[hour] != MISSING_VALUE \
                    and height_layer[hour] % 10 != 0 \
                    and not station.is_canadian():
                set_all_to_missing(cloud_height, hour)
                set_all_to_missing(cloud_amount, hour)
                errors.append(qc_error(
                    station_name=station.name, date_of_error=date,
                    error_code=9501, old_data_value=height_layer[hour],
                    new_data_value=MISSING_VALUE,
                    explanation="cloud height is greater than "
                    "10,000 ft, and not rounded "
                    " to the nearest 10"
                ))
            # Check that they're increasing through layers
            elif prev_height > height_layer[hour]:
                set_all_to_missing(cloud_height, hour)
                set_all_to_missing(cloud_amount, hour)
                errors.append(qc_error(
                    station_name=station.name, date_of_error=date,
                    error_code=9510, old_data_value=height_layer[hour],
                    new_data_value=MISSING_VALUE,
                    explanation="Cloud heights not increasing through groups"
                ))
            # Check that they're increasing through layers
            elif prev_amount > amount_layer[hour]:
                errors.append(qc_error(
                    station_name=station.name, date_of_error=date,
                    error_code=9511, old_data_value=height_layer[hour],
                    new_data_value=MISSING_VALUE,
                    explanation="Cloud amounts not increasing throught groups"
                ))
                set_all_to_missing(cloud_height, hour)
                set_all_to_missing(cloud_amount, hour)
            # Check that both are defined, or missing
            elif amount_layer[hour] == MISSING_VALUE and \
                    height_layer[hour] != MISSING_VALUE:
                errors.append(qc_error(
                    station_name=station.name, date_of_error=date,
                    error_code=9520, old_data_value=height_layer[hour],
                    new_data_value=MISSING_VALUE,
                    explanation="missing cloud amount, "
                    "but height is not missing\n"
                    "Height: " + str(height_layer[hour]) + "\n"
                    "Amount: " + str(amount_layer[hour])
                ))
                set_all_to_missing(cloud_height, hour)
                set_all_to_missing(cloud_amount, hour)
            elif amount_layer[hour] != MISSING_VALUE and \
                    height_layer[hour] == MISSING_VALUE:
                errors.append(qc_error(
                    station_name=station.name, date_of_error=date,
                    error_code=9520, old_data_value=amount_layer[hour],
                    new_data_value=MISSING_VALUE,
                    explanation="missing cloud height,"
                    "but cloud amount is not missing\n"
                    "Height: " + str(height_layer[hour]) + "\n"
                    "Amount: " + str(amount_layer[hour])
                ))
                set_all_to_missing(cloud_height, hour)
                set_all_to_missing(cloud_amount, hour)

            prev_height = height_layer[hour]
            prev_amount = amount_layer[hour]

    return errors


def set_all_to_missing(list_of_arrays, index):

    for arr in list_of_arrays:
        arr[index] = MISSING_VALUE

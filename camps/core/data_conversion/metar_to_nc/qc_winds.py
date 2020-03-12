import logging
import qc_general
import pdb
from qc_error import qc_error


"""Module: qc_winds.py

Methods:
    qc_winds
"""


MISSING_VALUE = 9999


def qc_winds(station_list):

    all_errors = []
    for station in station_list:
        station_errors = []
        speed_arr = station.observations["WSP"]
        gust_arr = station.observations["GST"]
        direction_arr = station.observations["WDR"]
        station_type = station.observations["TYPE"]

        for i, (speed, gust, direction) in enumerate(
                zip(speed_arr, gust_arr, direction_arr)):
            if direction_arr[i] == -9:
                direction = 990
                direction_arr[i] = 990
            if direction != MISSING_VALUE and \
                    direction % 10 != 0 and station_type[i] != 8:
                err_msg = "Wind direction not to the nearest 10 degrees"
                new_error = qc_error(
                    station_name=station.name,
                    station_type=station_type[i],
                    date_of_error=station.hours[i],
                    error_code=9401, old_data_value=direction,
                    new_data_value=MISSING_VALUE, explanation=err_msg
                )
                station_errors.append(new_error)
                direction_arr[i] = MISSING_VALUE
                speed_arr[i] = MISSING_VALUE
                gust_arr[i] = MISSING_VALUE

            if gust != MISSING_VALUE and \
                    (gust < 10 or gust < (speed + 3) or gust > (speed + 40)):

                err_msg = "Wind guest not greater" + \
                        "than 9 kts and not " + \
                        "between wind speed + 3 kts" + \
                        "and wind speed " + \
                        "+ 40 kts. Speed is : " + str(speed)
                new_error = qc_error(
                    station_name=station.name,
                    station_type=station_type[i],
                    date_of_error=station.hours[i],
                    error_code=9402, old_data_value=gust,
                    new_data_value=MISSING_VALUE, explanation=err_msg
                )
                station_errors.append(new_error)
                gust_arr[i] = MISSING_VALUE

            if station_type[i] != 8 and \
                    (direction == 0 and
                        (speed != 0 or gust != MISSING_VALUE)) \
                    or (speed == 0 and
                        (direction != 0 or gust != MISSING_VALUE)):
                err_msg = "Calm report does not have 0 for all three wind" + \
                        " components"
                new_error = qc_error(
                    station_name=station.name,
                    station_type=station_type[i],
                    date_of_error=station.hours[i],
                    error_code=9403, old_data_value=gust,
                    new_data_value=MISSING_VALUE, explanation=err_msg
                )
                station_errors.append(new_error)
                direction_arr[i] = MISSING_VALUE
                speed_arr[i] = MISSING_VALUE
                gust_arr[i] = MISSING_VALUE

            if direction == -9:
                direction_arr[i] = 990
        all_errors += station_errors

    return all_errors

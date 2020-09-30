import logging
from . import qc_general
from . import qc_weather
import pdb
import numpy as np
from .qc_error import qc_error



"""Module: qc_precip.py

Modules:
    qc_precip
"""


MISSING_VALUE = 9999


def qc_precip(station_list):

    errors = []
    # pull out the precip layer
    for station in station_list:
        precip_1h = station.get_obs("1PCP")
        precip_3h = station.get_obs("3PCP")
        precip_6h = station.get_obs("6PCP")
        precip_24h = station.get_obs("24PP")
        present_weather = (station.get_obs("PRWX1"),
                           station.get_obs("PRWX2"),
                           station.get_obs("PRWX3"))
        dew_point = station.get_obs("DEW")
        temperature = station.get_obs("TMP")
        station_type = station.get_obs("TYPE")
        if station.is_canadian() or station.is_russian():
            precip_1h[:] = MISSING_VALUE
            precip_3h[:] = MISSING_VALUE
            precip_6h[:] = MISSING_VALUE
            precip_24h[:] = MISSING_VALUE
            continue

        corrected_24h = 0
        precip_24_diff = 0
        for i in range(1, len(precip_1h), 6):

            i_3h = i + 2
            i_6h = i + 5
            if i_6h >= len(precip_1h):
                continue
            date = station.hours[i]
            date_3h = station.hours[i_3h]
            date_6h = station.hours[i_6h]
            if i + 12 % 24 == 0:
                if precip_24h[i] != MISSING_VALUE:
                    if corrected_24h == 4:
                        errors.append(qc_error(
                            station_name=station.name, date_of_error=date_6h,
                            error_code=9740, old_data_value=precip_24h[i],
                            new_data_value=0,
                            explanation="24 hour precip was corrected as dew "
                            "or snowmelt for all 6h periods"
                        ))
                        precip_24h[i] = 0
                    elif corrected_24h > 0:
                        errors.append(qc_error(
                            station_name=station.name, date_of_error=date_6h,
                            error_code=9741, old_data_value=precip_24h[i],
                            new_data_value=precip_24h[i] - precip_24_diff,
                            explanation="24 hour precip was corrected as dew "
                            "or snowmelt in 1 or more 6h periods"
                        ))
                        precip_24h[i] -= precip_24_diff
                corrected_24h = 0
                precip_24_diff = 0
            if precip_3h[i_3h] > precip_6h[i_6h]:
                precip_3h[i_3h] = MISSING_VALUE
                precip_6h[i_6h] = MISSING_VALUE
                if precip_3h[i_3h] != MISSING_VALUE and precip_3h[i_3h] > 900:
                    errors.append(qc_error(
                        station_name=station.name, date_of_error=date_3h,
                        error_code=9700, old_data_value=precip_3h[i_3h],
                        new_data_value=MISSING_VALUE,
                        explanation="3 hour precip out of range. > 9"
                    ))
                    precip_3h[i_3h] = MISSING_VALUE
                if precip_6h[i_6h] != MISSING_VALUE and precip_6h[i_6h] > 1200:
                    errors.append(qc_error(
                        station_name=station.name, date_of_error=date_6h,
                        error_code=9700, old_data_value=precip_6h[i_6h],
                        new_data_value=MISSING_VALUE,
                        explanation="6 hour precip out of range. > 12"
                    ))
                    precip_6h[i_6h] = MISSING_VALUE
            weather_in_3h = False
            weather_in_6h = False
            p1 = precip_1h[i:i + 6]
            for j in range(0, len(p1)):
                date = station.hours[i + j]
                if int(date) > 2006111300 and int(date) < 2007032800:
                    udef_amount = 0
                else:
                    undef_amount = MISSING_VALUE
                if precip_1h[i + j] == -9:
                    precip_1h[i + j] = undef_amount
                if precip_3h[i + j] == -9:
                    precip_3h[i + j] = undef_amount
                if precip_6h[i + j] == -9:
                    precip_6h[i + j] = undef_amount
                if precip_24h[i + j] == -9:
                    precip_24h[i + j] = undef_amount
                if p1[j] != MISSING_VALUE and p1[j] > 375:
                    errors.append(qc_error(
                        station_name=station.name, date_of_error=date,
                        error_code=9700, old_data_value=p1[j],
                        new_data_value=MISSING_VALUE,
                        explanation="1 hour precip out of range. > 3.75"
                    ))
                    precip_1h[i + j] = MISSING_VALUE
                if present_weather[0][i + j] > 51 and \
                        present_weather[0][i + j] < 196:
                    weather_in_3h = j < 3
                    weather_in_6h = j >= 3
                    if p1[j] != MISSING_VALUE and p1[j] == 0:
                        errors.append(qc_error(
                            station_name=station.name, date_of_error=date,
                            error_code=9705, old_data_value=p1[j],
                            new_data_value=MISSING_VALUE,
                            explanation="The reported present weather (" +
                            str(present_weather[0][i + j]) +
                            ") included precip, "
                            "but no precip amount reported"
                        ))
                        precip_1h[i + j] = MISSING_VALUE
                    if precip_3h[i_3h] != MISSING_VALUE and \
                            station.is_AO2_or_MANU(i + j) \
                            and precip_3h[i_3h] == 0 \
                            and weather_in_3h:
                        errors.append(qc_error(
                            station_name=station.name, date_of_error=date_3h,
                            error_code=9706, old_data_value=precip_3h[i_3h],
                            new_data_value=MISSING_VALUE,
                            explanation="The reported present weather (" +
                            str(present_weather[0][i + j]) +
                            ") included precip, "
                            "but no 3h precip amount reported"
                        ))
                        precip_1h[i_3h] = MISSING_VALUE
                    if precip_6h[i_6h] != MISSING_VALUE and \
                            station.is_AO2_or_MANU(i + j) \
                            and precip_6h[i_6h] == 0:
                        errors.append(qc_error(
                            station_name=station.name, date_of_error=date_6h,
                            error_code=9707, old_data_value=precip_1h[i_6h],
                            new_data_value=MISSING_VALUE,
                            explanation="The reported present weather (" +
                            str(present_weather[0][i + j]) +
                            ") included precip, "
                            "but no 6h precip amount reported"
                        ))
                        precip_6h[i_6h] = MISSING_VALUE
            if (precip_6h[i_6h] != MISSING_VALUE or precip_6h[i_6h] == 0)\
                    and precip_3h[i_3h] != MISSING_VALUE and weather_in_3h \
                    and not weather_in_6h:
                errors.append(qc_error(
                    station_name=station.name, date_of_error=date_6h,
                    error_code=9711, old_data_value=precip_1h[i_6h],
                    new_data_value=precip_3h[i_3h],
                    explanation="The reported present weather included precip,"
                    " but no 6-h precip amount reported"
                ))
                precip_6h[i_6h] = precip_3h[i_3h]
            if station_type[i + j] >= 2 and station_type[i + j] <= 6 \
                    and station_type[i + j] != 5:
                if (precip_6h[i_6h] == 1 or
                        precip_6h[i_6h] == 2) and not weather_in_6h:
                    # Check for fog and dewpoint depression
                    for j in range(0, len(p1)):
                        if present_weather[0][i + j] == 45 and \
                                (temperature[i + j] - dew_point[i + j] < 2):
                            corrected_24h += 1
                            precip_24_diff += precip_6h[i_6h]
                            precip_3h[i_3h] = 0
                            precip_6h[i_6h] = 0
                            precip_1h[i:i + 6] = 0
                            errors.append(qc_error(
                                station_name=station.name,
                                date_of_error=date_6h,
                                error_code=9720,
                                old_data_value=precip_1h[i_6h],
                                new_data_value=0,
                                explanation="six hour precip is"
                                ".01 or .02, dewpoint depression was "
                                "less than 2, and fog was reported."
                            ))
                elif precip_6h[i_6h] != MISSING_VALUE and \
                        precip_6h[i_6h] > 1 and not weather_in_6h:
                    temp_6h = temperature[i:i + 6]
                    temp_max = max(temp_6h)
                    temp_min = min(temp_6h)
                    if temp_min <= 30 and temp_max >= 35:
                        corrected_24h += 1
                        precip_24_diff += precip_6h[i_6h]
                        errors.append(qc_error(
                            station_name=station.name, date_of_error=date_6h,
                            error_code=9730, old_data_value=precip_1h[i_6h],
                            new_data_value=0,
                            explanation="six hour precip is reported, "
                            "and temperature increased "
                            "from less than 30 to more than 35"
                        ))

    return errors

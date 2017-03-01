import logging
import os
import qc_general
from qc_error import qc_error
from qc_error import set_all_attr
from qc_error import stats
import pdb
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool

MISSING_VALUE = 9999
def qc_temp(station_list):
    all_errors = []
    num_processors = int(os.getenv('NUM_PROCS', 8))
    pool = Pool(num_processors)
    all_errors = pool.map(qc_temp_st,station_list)
    pool.close()
    pool.join()
#    for station in station_list:
#        qc_temp_st(station)
    return all_errors

def qc_temp_st(station):
    # Used observations for this QC:
    #   TMP
    #   MX6
    #   MN6
    #   X24
    #   N24
    #print "temp"
    station_errors = []
    # Pull out the needed data from each station
    station_hours = station.hours
    temperature = station.observations['TMP']
    dew_point = station.observations['DEW']
    max_temp_6_hour = station.observations['MX6']
    min_temp_6_hour = station.observations['MN6']
    max_temp_24_hour = station.observations['X24']
    min_temp_24_hour = station.observations['N24']
    station_type = station.get_obs("TYPE")
    lat = station.get_obs("LAT")[0]
    lon = station.get_obs("LON")[0]
    season = station.get_season() 

    # Temperature QC
    errors = qc_general.check_consistency(temperature, station_type, 10)
    set_all_attr(errors,"error_code",9901)
    station_errors += errors

    errors = check_6hour_max(temperature, max_temp_6_hour, station_hours,station_type)
    station_errors += errors
    
    errors = check_6hour_min(temperature, min_temp_6_hour, station_hours,station_type)
    station_errors += errors

    errors = qc_general.check_min_max(max_temp_6_hour,max_temp_6_hour)
    set_all_attr(errors,"error_code",9930)
    station_errors += errors

    errors = qc_general.check_min_max(max_temp_24_hour,max_temp_24_hour)
    set_all_attr(errors,"error_code",9931)
    station_errors += errors

    # Dew Point QC
    allowance = 10
    is_spring_or_summer = season == 'spring' or season == 'summer'
    is_fall_or_winter = season == 'winter' or season == 'fall'
    if lon >= 95 and lon < 30:
        if is_spring_or_summer:
            allowance = 15
        elif is_fall_or_winter:
            allowance = 12
    errors = qc_general.check_consistency(dew_point, station_type, allowance)
    set_all_attr(errors,"error_code",9802)
    for err in errors:
        err.date_of_error = station_hours[err.date_of_error]
    station_errors += errors

    errors = check_dewpoint(dew_point, temperature)
    for err in errors: 
        err.date_of_error = station_hours[err.date_of_error]
    station_errors += errors

    for err in station_errors:
        err.station_name = station.name

    return station_errors



#check boundary conditions
#maybe change synoptic to 'synoptic_max'
#if you were to do this again, you may consider just indexing
def check_6hour_max(hourly_temp_array, six_hour_max_array, date_array, station_type):
    """
    Performs QC on the 6 hour max temperature measurements. 
    """
    errors = []
    tmp_6hours = []


    for i,date in enumerate(date_array):
        if station_type[i] >= 2 and station_type[i] <= 8:
            base_tolerance = 8
        else:
            base_tolerance = 6
        six_hour_temp = six_hour_max_array[i]
        one_hour_temp = hourly_temp_array[i]

        current_hour = date[-2:] #get just the hour
        tmp_6hours.append(one_hour_temp)
        # Every 6 hours (00,06,12,18)z, do checks
        if (int(current_hour) % 6) == 0: 
            if(len(tmp_6hours) < 3 and i != 1):
                #pdb.set_trace()
                pass
            extrema,indicies,num_missing = calc_special_max(tmp_6hours,six_hour_temp)
            temp_difference = extrema - six_hour_temp
            # Tolerance definition
            tolerance = base_tolerance + (2*num_missing)
            # First check if six_hour_temp value is already missing
            if six_hour_temp == MISSING_VALUE: 
                tmp_6hours=[tmp_6hours.pop()] 
            # Determine the tolerance
            elif num_missing == len(tmp_6hours):
                six_hour_max_array[i] = MISSING_VALUE
            # Check Tolerance
            elif ((six_hour_temp - extrema) > tolerance): 
                new_error = qc_error(
                        date_of_error=date,\
                        error_code=9915,old_data_value=six_hour_temp,\
                        new_data_value=MISSING_VALUE,explanation=\
                        "The reported synoptic 6-h max is out of tolerance, " \
                        "where tolerance is "+str(base_tolerance)+"+(2*the " \
                        "number of hours missing--"+str(num_missing)+\
                        "\n"+str( tmp_6hours)+"\n" \
                        ") in the synoptic period. \n" \
                        "reported 6h max   : "+str(six_hour_temp)+"\n" \
                        "calculated 6h max : "+str(extrema)
                        )
                errors.append(new_error)
                six_hour_max_array[i] = MISSING_VALUE
            # Check if garbage six_hour_temp time value
            elif temp_difference >= 2 and len(indicies) > 1:
                new_error = qc_error(
                        date_of_error=date,\
                        error_code=9911,old_data_value=six_hour_temp,\
                        new_data_value=MISSING_VALUE,explanation=\
                        "The calculated 6-h max from the hourly " \
                        "temperatures is greater than the reported " \
                        "6-h max by 2 degrees and this occured " \
                        "more than once during the synoptic period."
                        )
                errors.append(new_error)
                six_hour_max_array[i] = MISSING_VALUE
            # Check for a rounding error in the hourlies
            elif (temp_difference == 1 and len(indicies) > 1) \
                    or ( \
                        (temp_difference == 1 and len(indicies) == 1) \
                        and (indicies[0] != 0 and indicies[0] != len(tmp_6hours)-1)\
                        ):
                # Correct hours that were affected
                for affected_hour in indicies: 
                    new_error = qc_error(
                            date_of_error=date,error_code=9902,\
                            old_data_value=hourly_temp_array[(i-6)+affected_hour],\
                            new_data_value=six_hour_temp,explanation=\
                            "The calculated 6-h max from the hourly " \
                            "temperatures is greater than the reported " \
                            "6-h max by only one degree and this occured " \
                            "more than once during the period OR this " \
                            "occured only once during the period, but not " \
                            "the first or last hour"
                            )
                    errors.append(new_error)
                    hourly_temp_array[(i-6)+affected_hour] = six_hour_temp
            # correct six_hour_temp if the hourly is greater near the start/end of the record
            elif (temp_difference > 0 and len(indicies) == 1)\
                    and (indicies[0] == 0 or indicies[0] == len(tmp_6hours)-1):
                new_error = qc_error(
                        date_of_error=date,\
                        error_code=9912,old_data_value=six_hour_temp,\
                        new_data_value=extrema,explanation=\
                        "The calculated 6-h max from the hourly " \
                        "temperatures is greater than the reported " \
                        "6-h max and this occured " \
                        "at the first or last hour of the synoptic period."
                        )
                errors.append(new_error)
                six_hour_max_array[i] = extrema
            elif (temp_difference) >= 2 \
                    and (indicies[0] != 0 and indicies[0] != len(tmp_6hours)-1):
                new_error = qc_error(
                        date_of_error=date,\
                        error_code=9914,old_data_value=six_hour_temp,\
                        new_data_value=MISSING_VALUE,explanation=\
                        "The calculated 6-h max from the hourly " \
                        "temperatures is greater than the reported " \
                        "6-h max by 2 degrees or more on any hour except " \
                        "the first or last hour of the synoptic period."
                        )
                errors.append(new_error)
                six_hour_max_array[i] = MISSING_VALUE
            tmp_6hours = [tmp_6hours.pop()]
    return errors

#check boundary conditions
#maybe change synoptic to 'synoptic_max'
#if you were to do this again, you may consider just indexing
def check_6hour_min(hourly_temp_array, six_hour_min_array, date_array, station_type):
    """
    Performs QC on the 6hour time measurements.
    """
    errors = []
    tmp_6hours = []
    for i,date in enumerate(date_array):
        if station_type[i] >= 2 and station_type[i] <= 8:
            base_tolerance = 8
        else:
            base_tolerance = 6
        six_hour_temp = six_hour_min_array[i]
        one_hour_temp = hourly_temp_array[i]

        current_hour = date[-2:] #get just the hour
        tmp_6hours.append(one_hour_temp)
        # Every 6 hours (00,06,12,18)z, do checks
        if (int(current_hour) % 6) == 0: 
            extrema,indicies,num_missing = calc_special_min(tmp_6hours,six_hour_temp)
            temp_difference = extrema - six_hour_temp
            # Tolerance definition
            tolerance = base_tolerance + (2*num_missing)
            # First check if six_hour_temp value is already missing
            if six_hour_temp == MISSING_VALUE: 
                tmp_6hours=[] 
            # Determine the tolerance
            elif num_missing == len(tmp_6hours):
                six_hour_min_array[i] = MISSING_VALUE
            # Check Tolerance
            elif ( extrema - six_hour_temp ) > tolerance: 
                new_error = qc_error(
                        date_of_error=date,\
                        error_code=9925,old_data_value=six_hour_temp,\
                        new_data_value=MISSING_VALUE,explanation=\
                        "The reported synoptic 6-h min is out of tolerance, " \
                        "where tolerance is "+str(base_tolerance)+"+(2*the " \
                        "number of hours missing--"+str(num_missing)+"+"\
                        ") in the synoptic period. \n" \
                        "reported 6h min   : "+str(six_hour_temp)+"\n" \
                        "calculated 6h min : "+str(extrema)
                        )
                errors.append(new_error)
                six_hour_min_array[i] = MISSING_VALUE
            # Check if garbage six_hour_temp time value
            elif temp_difference <= -2 and len(indicies) > 1:
                new_error = qc_error(
                        date_of_error=date,\
                        error_code=9921,old_data_value=six_hour_temp,\
                        new_data_value=MISSING_VALUE,explanation=\
                        "The calculated 6-h min from the hourly " \
                        "temperatures is greater than the reported " \
                        "6-h min by 2 degrees and this occured " \
                        "more than once during the synoptic period."
                        )
                errors.append(new_error)
                six_hour_min_array[i] = MISSING_VALUE
            # Check for a rounding error in the hourlies
            elif (temp_difference == -1 and len(indicies) > 1) \
                    or ( \
                        (temp_difference == -1 and len(indicies) == 1) \
                        and (indicies[0] != 0 and indicies[0] != len(tmp_6hours)-1)\
                        ):
                # Correct hours that were affected
                for affected_hour in indicies: 
                    new_error = qc_error(
                            date_of_error=date,error_code=9902,\
                            old_data_value=hourly_temp_array[(i-6)+affected_hour],\
                            new_data_value=six_hour_temp,explanation=\
                            "The calculated 6-h min from the hourly " \
                            "temperatures is greater than the reported " \
                            "6-h min by only one degree and this occured " \
                            "more than once during the period OR this " \
                            "occured only once during the period, but not " \
                            "the first or last hour"
                            )
                    errors.append(new_error)
                    hourly_temp_array[(i-6)+affected_hour] = six_hour_temp
            # correct six_hour_temp if the hourly is greater near the start/end of the record
            elif (temp_difference < 0 and len(indicies) == 1)\
                    and (indicies[0] == 0 or indicies[0] == len(tmp_6hours)-1):
                new_error = qc_error(
                        date_of_error=date,\
                        error_code=9922,old_data_value=six_hour_temp,\
                        new_data_value=extrema,explanation=\
                        "The calculated 6-h min from the hourly " \
                        "temperatures is greater than the reported " \
                        "6-h min and this occured " \
                        "at the first or last hour of the synoptic period."
                        )
                errors.append(new_error)
                six_hour_min_array[i] = extrema
            elif (temp_difference) <= -2 \
                    and (indicies[0] != 0 and indicies[0] != len(tmp_6hours)-1):
                new_error = qc_error(
                        date_of_error=date,\
                        error_code=9924,old_data_value=six_hour_temp,\
                        new_data_value=MISSING_VALUE,explanation=\
                        "The calculated 6-h min from the hourly " \
                        "temperatures is greater than the reported " \
                        "6-h min by 2 degrees or more on any hour except " \
                        "the first or last hour of the synoptic period."
                        )
                errors.append(new_error)
                six_hour_min_array[i] = MISSING_VALUE
            tmp_6hours = []
    return errors

def calc_special_max(in_array, observed_max):
    """
    Find the maximum/minimum value(s) in an array. Return a tuple in which 
    element 0 is the maximum/minimum value (if it exists), and 
    element 1 is an array of indicies at which the the hourly max was greater than
                the observed max by at least two, OR if the hourly max is only 1 over,
                then indicies at which this max is present, and
    element 2 is the number of missing values
    """
    num_missing = 0
    maximum = -9999
    for i in in_array:
        if i != MISSING_VALUE and i>maximum:
            maximum = i
    indicies = []
    for i in range(0,len(in_array)):
        if in_array[i] == MISSING_VALUE:
            num_missing += 1
        elif maximum - observed_max == 1 and in_array[i] == maximum:
            indicies.append(i)
        elif in_array[i] - observed_max > 1:
            indicies.append(i)
    return (maximum, indicies,  num_missing)
    
def calc_special_min(in_array, observed_min):
    """
    Find the maximum/minimum value(s) in an array. Return a tuple in which 
    element 0 is the maximum/minimum value (if it exists), and 
    element 1 is an array of indicies at which the max was found, and
    element 2 is the number of missing values
    """
    num_missing = 0
    indicies = []
    minimum = min(in_array)
    for i in range(0,len(in_array)):
        if in_array[i] == MISSING_VALUE:
            num_missing += 1
        elif minimum - observed_min == -1 and in_array[i] == minimum:
            indicies.append(i)
        elif in_array[i] - observed_min < -1:
            indicies.append(i)
    return (minimum, indicies,  num_missing)

def check_dewpoint(dewpoint_arr, temperature_arr):
    errors = []
    for i, (dewpoint, temp) in enumerate(zip(dewpoint_arr,temperature_arr)):
        if(dewpoint==MISSING_VALUE):
            continue
        dewpoint_depression = temp - dewpoint
        if dewpoint < -30 and dewpoint_depression > 15:
            new_error = qc_error(
                    date_of_error=i,\
                    error_code=9800,old_data_value=dewpoint,\
                    new_data_value=MISSING_VALUE,explanation=\
                    "dewpoint is less than -30 degrees and the dewpoint " \
                    "depression is greater than 15 degrees"
                    )
            errors.append(new_error)
            dewpoint_arr[i] = MISSING_VALUE
        if dewpoint > temp:
            new_error = qc_error(
                    date_of_error=i,\
                    error_code=9803,old_data_value=dewpoint,\
                    new_data_value=MISSING_VALUE,explanation=\
                    "dewpoint is greater than temperature "
                    )
            errors.append(new_error)
            dewpoint_arr[i] = temp
    return errors




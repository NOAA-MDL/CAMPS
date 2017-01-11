import logging
import qc_general
from qc_error import qc_error
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool

MISSING_VALUE = 9999
def qc_weather(station_list):
    """ 
    QC present weather and visibility.
    """
    all_errors = []
    pool = Pool()
    pool = Pool(16)
    all_errors = pool.map(qc_weather_st,station_list)
    pool.close()
    pool.join()
    return all_errors
    #for station in station_list:

def qc_weather_st(station):
    errors = []
    # Pull out needed stations
    present_wx = []
    visibility = station.get_obs("VIS")
    temperature = station.get_obs('TMP')
    windspeed = station.get_obs("WSP")
    gust = station.get_obs("GST")
    present_wx.append(station.get_obs("PRWX1"))
    present_wx.append(station.get_obs("PRWX2"))
    present_wx.append(station.get_obs("PRWX3"))
    cloud_amount = station.get_obs("CA1")
    station_type = station.get_obs("TYPE")

    for i,(vis, wx_1, wx_2, wx_3) in enumerate(zip(
        visibility,present_wx[0],present_wx[1],present_wx[2])):

        all_wx = (wx_1,wx_2,wx_3)
        date = station.hours[i]
        if vis != MISSING_VALUE:
            if vis > 100 or vis < 0:
                errors.append(
                        qc_error(
                        station_name=station.name,date_of_error=date,\
                        error_code=9300,old_data_value=vis,\
                        new_data_value=MISSING_VALUE,explanation=\
                        "visibility out of range"
                        ))
                visibility[i] = MISSING_VALUE
            elif vis >= 7 and vis <= 10 \
                  and any(map(is_vision_obstructing,all_wx)):
                errors.append(
                        qc_error(
                        station_name=station.name,date_of_error=date,\
                        error_code=9310,old_data_value=vis,\
                        new_data_value=6,explanation=\
                        "visibility should be reduced based on weather "\
                        "conditions" + str(all_wx)
                        ))
                visibility[i] = 6
            elif vis > 10 and any(map(is_vision_obstructing,all_wx)):
                errors.append(
                        qc_error(
                        station_name=station.name,date_of_error=date,\
                        error_code=9312,old_data_value=vis,\
                        new_data_value=MISSING_VALUE,explanation=\
                        "visibility too large based on weather "\
                        "conditions:" + str(all_wx)
                        ))
                visibility[i] = MISSING_VALUE
                present_wx[0][i] = MISSING_VALUE
                present_wx[1][i] = MISSING_VALUE
                present_wx[2][i] = MISSING_VALUE
                #where 45 == FOG
            elif vis > .5 and 45 in all_wx:
                errors.append(
                        qc_error(
                        station_name=station.name,date_of_error=date,\
                        error_code=9210,old_data_value=all_wx,\
                        new_data_value=10,explanation=\
                        "Fog reported, but visibility > .5"
                        ))
                index = all_wx.index(45)
                present_wx[index][i] = 10
            elif vis < .5 and 10 in all_wx:
                errors.append(
                        qc_error(
                        station_name=station.name,date_of_error=date,\
                        error_code=9211,old_data_value=all_wx,\
                        new_data_value=10,explanation=\
                        "Mist reported, but visibility < .5"
                        ))
                index = all_wx.index(10)
                present_wx[index][i] = 45 
            elif (station_type[i] == 1 or station_type[i] == 3) \
                    and vis <= 6 and 0 in all_wx:
                present_wx[0][i] = MISSING_VALUE
                present_wx[1][i] = MISSING_VALUE
                present_wx[2][i] = MISSING_VALUE
            if is_light_drizzle_or_snow(wx_1) \
                    and is_only_reported_wx(all_wx):
                if vis > .25 and vis <= .50:
                    present_wx[0][i] += 2
                    wx_1 += 2
                    if wx_1 == 58:
                        present_wx[0][i] = 57
                    errors.append(
                        qc_error(
                        station_name=station.name,date_of_error=date,\
                        error_code=9214,old_data_value=wx_1-2,\
                        new_data_value=present_wx[0][i],explanation=\
                        "Intensity of light snow/drizzle reported does not match" \
                        " visibility ("+str(vis)+") reported, and no other weather was reported"+str(all_wx)

                        ))
                elif vis < .25:
                    present_wx[0][i] += 4
                    if wx_1 == 60:
                        present_wx[0][i] = 156 
                    errors.append(
                        qc_error(
                        station_name=station.name,date_of_error=date,\
                        error_code=9214,old_data_value=wx_1,\
                        new_data_value=present_wx[0][i],explanation=\
                        "Intensity of light snow/drizzle reported does not match" \
                        " visibility ("+str(vis)+") reported, and no other weather was reported"+str(all_wx)

                        ))
            elif is_moderate_drizzle_or_snow(wx_1) \
                    and is_only_reported_wx(all_wx):
                if vis > .50:
                    present_wx[0][i] -= 2
                    wx_1 += 2
                    if wx_1 == 55:
                        present_wx[0][i] = 56
                    errors.append(
                        qc_error(
                        station_name=station.name,date_of_error=date,\
                        error_code=9214,old_data_value=wx_1-2,\
                        new_data_value=present_wx[0][i],explanation=\
                        "Intensity of moderate snow/drizzle reported does not match" \
                        " visibility ("+str(vis)+") reported, and no other weather was reported"+str(all_wx)

                        ))
                elif vis < .25:
                    present_wx[0][i] += 2
                    if wx_1 == 158:
                        present_wx[0][i] = 57 
                    errors.append(
                        qc_error(
                        station_name=station.name,date_of_error=date,\
                        error_code=9214,old_data_value=wx_1,\
                        new_data_value=present_wx[0][i],explanation=\
                        "Intensity of moderate snow/drizzle reported does not match" \
                        " visibility ("+str(vis)+") reported, and no other weather was reported"+str(all_wx)

                        ))
            elif is_heavy_drizzle_or_snow(all_wx[0]) \
                    and is_only_reported_wx(all_wx):
                if vis > .50:
                    present_wx[0][i] -= 4
                    if present_wx[0][i]  == 152:
                        present_wx[0][i]  = 56 
                    errors.append(
                        qc_error(
                        station_name=station.name,date_of_error=date,\
                        error_code=9214,old_data_value=wx_1,\
                        new_data_value=present_wx[0][i],explanation=\
                        "Intensity of heavy snow/drizzle reported does not match" \
                        " visibility ("+str(vis)+") reported, and no other weather was reported"+str(all_wx)

                        ))
                elif vis > .25 :
                    present_wx[0][i]  -= 2 
                    if present_wx[0][i]  == 154:
                        present_wx[0][i]  = 57
                    errors.append(
                        qc_error(
                        station_name=station.name,date_of_error=date,\
                        error_code=9214,old_data_value=all_wx[0],\
                        new_data_value=present_wx[0][i] ,explanation=\
                        "Intensity of heavy snow/drizzle reported does not match" \
                        " visibility ("+str(vis)+") reported, and no other weather was reported" +str(all_wx)
                        ))
            elif is_ice_pellets(all_wx[0]) \
                    and is_only_reported_wx(all_wx):
                if vis >= 3 and vis <= 6:
                    present_wx[0][i] = 79
                    errors.append(
                        qc_error(
                        station_name=station.name,date_of_error=date,\
                        error_code=9215,old_data_value=all_wx[0],\
                        new_data_value=present_wx[0][i] ,explanation=\
                        "Intensity of heavy snow/drizzle reported does not match" \
                        " visibility ("+str(vis)+") reported, and no other weather was reported" +str(all_wx)
                        ))


        # Swap the order if hydrometeor precedes precipitation
        if is_precipitation(wx_2) and is_hydrometeor(wx_1):
            present_wx[0][i]  = wx_2
            present_wx[1][i]  = wx_1 
            errors.append(qc_error(
                    station_name=station.name,date_of_error=date,\
                    error_code=9220,old_data_value=wx_2,\
                    new_data_value=wx_1,explanation=\
                    "Order of weather is incorrect. " \
                    "Hydrometeor before precip" 
                    ))
        # If showers within sight is reported as well as precipitation
        if is_present(all_wx,is_precipitation) and 16 in all_wx:
            present_wx[0][i]  = wx_2
            present_wx[1][i]  = wx_3
            present_wx[2][i]  = MISSING_VALUE
            errors.append(
                    qc_error(
                    station_name=station.name,date_of_error=date,\
                    error_code=9221,old_data_value=wx_2,\
                    new_data_value=wx_3,explanation=\
                    "Showers within sight reported " \
                    "and precip was reported" 
                    ))
        # If two types of thunderstorms were reported 
        if is_tstorm(wx_1) and wx_2 == 96:
            errors.append(
                    qc_error(
                    station_name=station.name,date_of_error=date,\
                    error_code=9222,old_data_value=wx_2,\
                    new_data_value=90,explanation=\
                    "thunderstorm reported in group 1 " \
                    "and thunderstorm also reported in group 2" 
                    ))
            present_wx[1][i]  = 90
        dupe_found = False
        if is_drizzle(wx_1) and is_drizzle(wx_2):
            present_wx[1][i]  = MISSING_VALUE
            present_wx[2][i]  = MISSING_VALUE
            dupe_found = True
        elif is_drizzle(wx_1) and is_drizzle(wx_3):
            present_wx[1][i]  = MISSING_VALUE
            present_wx[2][i]  = MISSING_VALUE
            dupe_found = True
        elif is_rain(wx_1) and is_rain(wx_2):
            present_wx[1][i]  = MISSING_VALUE
            present_wx[2][i]  = MISSING_VALUE
            dupe_found = True
        elif is_rain(wx_1) and is_rain(wx_3):
            present_wx[1][i]  = MISSING_VALUE
            present_wx[2][i]  = MISSING_VALUE
            dupe_found = True
        elif is_snow(wx_1) and is_snow(wx_2):
            present_wx[1][i]  = MISSING_VALUE
            present_wx[2][i]  = MISSING_VALUE
            dupe_found = True
        elif is_snow(wx_1) and is_snow(wx_3):
            present_wx[1][i]  = MISSING_VALUE
            present_wx[2][i]  = MISSING_VALUE
            dupe_found = True

        if dupe_found:
            errors.append(
                    qc_error(
                    station_name=station.name,date_of_error=date,\
                    error_code=9223,old_data_value=wx_2,\
                    new_data_value=present_wx[1][i] ,explanation=\
                    "Duplicate weather group found" 
                    ))
        dupe_found = False
        if is_drizzle(wx_2) and is_drizzle(wx_3):
            present_wx[2][i]  = MISSING_VALUE
            dupe_found = True
        elif is_rain(wx_2) and is_rain(wx_3):
            present_wx[2][i]  = MISSING_VALUE
            dupe_found = True
        elif is_snow(wx_2) and is_snow(wx_3):
            present_wx[2][i]  = MISSING_VALUE
            dupe_found = True
        if dupe_found:
            errors.append(
                    qc_error(
                    station_name=station.name,date_of_error=date,\
                    error_code=9223,old_data_value=wx_2,\
                    new_data_value=present_wx[1][i] ,explanation=\
                    "Duplicate weather group found" 
                    ))
        # Temperature is less than 30 and there's liquid precip
        if is_present(all_wx,should_not_exist_below_30) \
                and temperature[i] < 30:
            present_wx[0][i] = MISSING_VALUE
            present_wx[1][i] = MISSING_VALUE
            present_wx[2][i] = MISSING_VALUE
            errors.append(
                    qc_error(
                    station_name=station.name,date_of_error=date,\
                    error_code=9230,old_data_value=wx_1,\
                    new_data_value=MISSING_VALUE,explanation=\
                    "Temperature is less than 30 and reported weather is" \
                    " liquid precipitation"
                    ))
        elif is_present(all_wx,should_not_exist_above_40) \
                and temperature[i] > 40 \
                and temperature[i] != MISSING_VALUE:
            present_wx[0][i] = MISSING_VALUE
            present_wx[1][i] = MISSING_VALUE
            present_wx[2][i] = MISSING_VALUE
            errors.append(
                    qc_error(
                    station_name=station.name,date_of_error=date,\
                    error_code=9231,old_data_value=wx_1,\
                    new_data_value=MISSING_VALUE,explanation=\
                    "Temperature is greater than 40 and reported "\
                    "weather is freezing rain/drizzle"
                    ))
        elif is_present(all_wx,should_not_exist_above_44) \
                and temperature[i] > 44:
            present_wx[0][i] = MISSING_VALUE
            present_wx[1][i] = MISSING_VALUE
            present_wx[2][i] = MISSING_VALUE
            errors.append(
                    qc_error(
                    station_name=station.name,date_of_error=date,\
                    error_code=9232,old_data_value=wx_1,\
                    new_data_value=MISSING_VALUE,explanation=\
                    "Temperature is greater than 40 and reported "\
                    "weather is rain/snow mix"
                    ))
        elif is_present(all_wx,is_blowing_phenom)\
                and windspeed[i] < 9 \
                and gust[i] == MISSING_VALUE:
            if is_blowing_phenom(wx_1):
                present_wx[0][i] = MISSING_VALUE
                present_wx[1][i] = MISSING_VALUE
                present_wx[2][i] = MISSING_VALUE
            elif is_blowing_phenom(wx_1):
                present_wx[1][i] = MISSING_VALUE
                present_wx[2][i] = MISSING_VALUE
            elif is_blowing_phenom(wx_1):
                present_wx[2][i] = MISSING_VALUE
            errors.append(
                    qc_error(
                    station_name=station.name,date_of_error=date,\
                    error_code=9240,old_data_value=wx_1,\
                    new_data_value=MISSING_VALUE,explanation=\
                    "blowing phenomenon is reported  "\
                    "but wind speed is less than 9 knots with no gust"
                    ))
        if cloud_amount[i] == 10 and wx_1 == 0  \
                and all_wxstation_type[i] >= 1 and station_type[i] <= 3:
            present_wx[0][i] = MISSING_VALUE
            present_wx[1][i] = MISSING_VALUE
            present_wx[2][i] = MISSING_VALUE
            errors.append(
                    qc_error(
                    station_name=station.name,date_of_error=date,\
                    error_code=9250,old_data_value=wx_1,\
                    new_data_value=MISSING_VALUE,explanation=\
                    "cloud height reported as obstructed, but "\
                    "no present weather was reported"
                    ))
        elif station_type[i] == 1 and cloud_amount[i] == 1  \
                and is_present(all_wx, is_present_weather):
            present_wx[0][i] = MISSING_VALUE
            present_wx[1][i] = MISSING_VALUE
            present_wx[2][i] = MISSING_VALUE
            cloud_amount[i] = MISSING_VALUE
            errors.append(
                    qc_error(
                    station_name=station.name,date_of_error=date,\
                    error_code=9251,old_data_value=wx_1,\
                    new_data_value=MISSING_VALUE,explanation=\
                    "Clear Skys reported, but "\
                    "present weather was also reported"
                    ))


                
    return errors

# No visibility restrictions on light pellets
def is_blowing_phenom(wx_num):
    return wx_num in set([7,38,207])

def is_ice_pellets(wx_num):
    return 79 == wx_num

def is_precipitation(wx_num):
    if wx_num == 79:
        return False
    return  wx_num > 50 and wx_num < 200
        
def is_hydrometeor(wx_num):
    return (wx_num >= 4 and wx_num <= 12) \
            or (wx_num >= 36 and wx_num <= 45)

def is_tstorm(wx_num):
    return wx_num in set([17,95,96,97])

def is_present(wx_arr, function):
    return any(map(function,wx_arr))

def is_vision_obstructing(wx_num):
    obstructed = set([4,5,6,7,8,10,12,18,31,\
                  32,33,34,38,45,156,166])

    if wx_num >= 176 and wx_num < 207:
        return True
    return wx_num in obstructed

def is_light_drizzle_or_snow(wx_num):
    return wx_num in set([51,56,71])

def is_moderate_drizzle_or_snow(wx_num):
    return wx_num in set([53,57,73])

def is_heavy_drizzle_or_snow(wx_num):
    return wx_num in set([55,156,75])

def is_drizzle(wx_num):
    if wx_num == 156:
        return True
    return wx_num >= 51 and wx_num <= 57

def is_rain(wx_num):
    return wx_num in set([61,62,63,64,65,66,67,80,166,183])

def is_snow(wx_num):
    return wx_num in set([71,72,73,74,75,85,86,187])

def is_liquid_precipitation(wx_num):
    wx_elements = set([51,52,53,54,55,58,59,\
                   60,61,62,63,64,65,80,81,183])
    return wx_num in wx_elements

def is_only_reported_wx(all_wx):
    return all_wx[0] != 9999 \
            and all_wx[1] == 9999 \
            and all_wx[2] == 9999

def is_rain_snow(wx_num):
    return wx_num in set([68,69,83,84])

def should_not_exist_below_30(wx_num):
    return is_liquid_precipitation(wx_num) or is_rain_snow(wx_num)

def should_not_exist_above_40(wx_num):
    return wx_num in set([56,57,66,67,76,156,166])
    
def should_not_exist_above_44(wx_num):
    if is_rain_snow(wx_num):
        return True
    if is_rain_snow(wx_num):
        return True
    return wx_num == 174 or wx_num == 176

def is_present_weather(wx_num):
    if wx_num == 76:
        return False
    return wx_num >= 51 and wx_num <= 97





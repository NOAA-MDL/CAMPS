"""
Defines various enumerations used in metar conversion.
"""
MISSING_VALUE = 9999

def get_station_type_enumeration(station_type_str):
    """
    Where station_type is the string that represents the station_type
    """
    return station_type.get(station_type_str, 9)

def get_enumeration_function(name): 
    """ 
    Returns an enumeration function based if given 'name' enumeration.
    Otherwise, returns None.
    """
    return needs_enumeration.get(name, lambda ob: ob)

def get_station_type(station_type_num):
    """ Returns the string representation of the station type. """
    station_type_number  = station_type_num
    return station_type.get(station_type_number, 'UNKN')

def get_cloud_amount_enumeration(observation):
    """
    Where observation is the string that represents a code for the cloud amount
    """
    return cloud_amount.get(observation, MISSING_VALUE)

def get_weather_type_enumeration(observation):
    """
    Where observation is the string that represents a code for the weather type
    """
    enum = weather_type.get(observation, MISSING_VALUE)
    if ( enum == MISSING_VALUE ): #potentially report error here
        pass
    return enum

cloud_amount = {
                'CLR' : 0,  #Clear
                'SKC' : 1,  #Clear
                'FEW' : 2,  #Few clouds; not currently used
                'SCT' : 3,  #Scattered
                'BKN' : 6,  #Broken Clouds
                'OVC' : 8,  #Overcast
                'POB' : 9,  #Sky parially obscured
                'OB' : 10   #Sky totally obscured
                }

weather_type = {
                '' : MISSING_VALUE,
                'FU' : 4,    #Smoke
                'HZ' : 5,    #Haze
                'DU' : 6,    #Dust
                'BLDU' : 7,  #Blowing dust
                'BLSA' : 7,  #Blowing sand
                'PO' : 8,    #Dust swirls or sand swirls
                'VCPO' : 8,  #Dust or sand between 5 and 10 miles from the sation
                'VCDS' : 9,  #Duststorm between 5 and 10 miles from the station
                'VCSS' : 9,  #Sandstorm between 5 and 10 miles from the station
                'BR' : 10,   #Mist with visibility between 5/8 sm and 6 sm
                'PY' : 11,   #Spray
                'VCSH' : 16, #Showers within sight, between 5 and 10 miles from the station
                'TS' : 17,   #Thunderstorms with no precipitation, also T-Storm in vicinity
                'SQ' : 18,   #Squalls
                '+FC' : 19,  #Tornado or waterspout, also funnel cloud
                'FC' : 19,   #Tornado or waterspout, also funnel cloud
                'DS' : 31,   #Moderate dust storm
                '-DS' : 31,  #Light dust storm
                'SS' : 31,   #Moderate sand storm
                '-SS' : 31,  #Light sand storm
                '+DS' : 34,  #Heavy dust storm
                '+SS' : 34,  #Heavy sand storm
                'DRSN' : 36, #Drifing snow
                '+DRSN' : 37,#Heavy drifting snow
                'BLSN' : 38, #Blowing snow
                '-BLSN' : 38,#Blowing snow
                'BLSA' : 38, #Blowing snow
                '+BLSA' : 39,#Heavy blowing snow
                'VCFG' : 40, #Fog between 5 and 10 miles from the station
                'BCFG' : 41, #Patchy fog
                'PRFG' : 44, #Partial fog
                'FG' : 45,   #Fog, visibility < 5/8 sm
                'MIFG' : 45, #Fog, visibility < 5/8 sm
                '-DZ' : 51,  #Light, continuous drizzle
                'DZ' : 53,   #Moderate continuous drizzle 
                '+DZ' : 55,  #Heavy continous drizzle
                '-FZDZ' : 56,#Light freezing drizzle
                'FZDZ' : 57, #Moderate freezing drizzle
                '+FZDZ' : 57,#Heavy freezing drizzle 
                '-RADZ' : 58,#Light rain and drizzle
                '-DZRA' : 58,#Light rain and drizzle
                'RADZ' : 59, #moderate rain and drizzle
                '+RADZ' : 59,#heavy  rain and drizzle
                'DZRA' : 59, #moderate rain and drizzle
                '+DZRA' : 59,#heavy rain and drizzle
                '-RA' : 61,  #Light rain
                'RA' : 63,   #Rain
                '+RA' : 65,  #Heavy rain
                '-FZRA' : 66,#Light freezing rain
                'FRZA' : 67, #Moderate freezing rain
                '+FRZA' : 67,#Heavy freezing rain
                '-RASN' : 68,# light rain and snow mixed
                '-SNRA' : 68,# light rain and snow mixed
                '-DZSN' : 68,# light drizzle and snow mixed
                '-SNDZ' : 68,# light drizzle and snow mixed
                'RASN' : 69, #Moderate rain and snow mixed
                'SNRA' : 69, #Moderate rain and snow mixed
                'SNDZ' : 69, #Moderate drizzle and snow mixed
                '+RASN' : 69,#Heavy rain and snow mixed
                '+SNRA' : 69,#Heavy rain and snow mixed
                'DZSN' : 69, #Moderate drizzle and snow mixed
                '+DZSN' : 69,#Heavy drizzle and snow mixed
                '+SNDZ' : 69,#Heavy drizzle and snow mixed
                '-SN' : 71,  #Light continuous snowfall
                'SN' : 73,   #Moderate continuous snowfall
                '+SN' : 75,  #Heavy continous snowfall
                'IC' : 76,   #Ice crystals
                'SG' : 77,   #Snow grains
                '-SG' : 77,  #Snow grains
                '+SG' : 77,  #Snow grains
                'PE' : 79,   #Ice pellets
                'PL' : 79,   #Ice pellets
                '+PE' : 79,  #Ice pellets
                '+PL' : 79,  #Ice pellets
                '-PL' : 79,  #Ice pellets
                'SHRA' : 81, #Moderate rain showers
                '+SHRA' : 81,#Heavy rain showers
                '-SHRASN':83,#Light showers of rain and snow mixed
                '-SHSNRA':83,#Light showers of rain and snow mixed
                'SHRASN' :84,#Moderate or heavy showers of rain/snow mixed
                'SHSNRA' :84,#Moderate or heavy showers of rain/snow mixed
                '+SHRASN':84,#Heavy showers of rain/snow mixed
                '+SHSNRA':84,#Heavy showers of rain/snow mixed
                '-SHSN' : 85,#Light snow showers
                'SHSN' : 86, #Moderate snow showers
                '+SHSN': 86, #Heavy snow showers
                'GS' : 88,   #Small hail K< 1/4 inch in diameter or snow pellets
                'GR' : 90,   #Hail greater than or equal to 1/4 inch in diameter
                'TSRA' : 95, #Thunderstorms with moderate rain
                '-TSRA' : 95,#Thunderstorms with light rain
                'TSSN' : 95, #Thunderstorms with moderate snow
                '-TSSN' : 95,#Thunderstorms with light snow
                'TSGR' : 96, #Thunderstorms with hail
                'TSGR-' : 96,#Thunderstorms with hail
                '+TSRA' : 97,#Thunderstorms with heavy rain
                '+TSSN' : 97,#Thunderstorms with snow
                'TSDS' : 98, #Thunderstorms with dust
                'TSSS' : 98, #Thunderstorms with  sand
                '+TSDS' : 98,#Thunderstorms with dust
                '+TSSS' : 98,#Thunderstorms with sand
                'UP' : 121,  #Unknown precipitation from ASOS
                'VA' : 204,  #Volcanic ash
                'BLPY' : 207,#Blowing spray
                'DRDU' : 208,#Drifting dust
                'DRSS' : 208,#Drifting sand
                }

station_type = {
                'MANU' : 1, 
                'AO2A' : 2,
                'AO2'  : 3,
                'AO1A' : 4,
                'AO1'  : 5,
                'AUTO' : 6,
                'WFO'  : 7,
                'UNKN' : 9
                }

needs_enumeration = {
        'TYPE' : get_station_type_enumeration,
        'PRWX1' : get_weather_type_enumeration,
        'PRWX2' : get_weather_type_enumeration,
        'PRWX3' : get_weather_type_enumeration,
        'CA1' : get_cloud_amount_enumeration,
        'CA2' : get_cloud_amount_enumeration,
        'CA3' : get_cloud_amount_enumeration,
        'CA4' : get_cloud_amount_enumeration,
        'CA5' : get_cloud_amount_enumeration,
        'CA6' : get_cloud_amount_enumeration
        }



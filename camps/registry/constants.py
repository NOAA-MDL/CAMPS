#import metpy.constants as const

"""
Module to give symbolic representation to magic strings and numbers.
"""

######################
# Metadata Constants #
######################
PLEV = 'plev'
ELEV = 'elev'
COORD = 'coordinates'
BOUNDS = 'bounds'
TIME_BOUNDS = 'time_bounds'
PLEV_BOUNDS = 'plev_bounds'
ELEV_BOUNDS = 'elev_bounds'
GFS = 'GFS'
NAM = 'NAM'
PROCESS_IDENTIFIER = 'PROV__Activity'
SOURCE_IDENTIFIER = "PROV__Used"

#######################
# Numerical Constants #
#######################

#ratio_of_dry_and_saturated_gas_constant = \
 #       const.dry_air_gas_constant / const.water_gas_constant

saturated_pressure_at_triple_point = 6.1078
randomConst1 = 17.269
randomConst2 = 237.3

################################
# International Standard units #
################################

international_units = {
'DayMaxT' : 'K',
'DewPt' : 'K',
'HtIndex' : 'K',
'KIndex' : 'K',
'MixR' : 'g/kg',
'NightMinT' : 'K',
'PLThick' : 'gpm',
'Precip' : 'kg m**-2',
'RelHum' : '%',
'Temp' : 'K',
'TLapse' : 'K',
'Uwind' : 'm s**-1',
'Vwind' : 'm s**-1',
'WChill' : 'K',
'WindSpd' : 'm/s',
'Wwind' : 'Pa s**-1'
}



var headerHgt = 60;
var maxHeight;
var all_vars;
var primary_vars;

var init = function()
{
    adjustSize();
    bindActionEvents();
    getVars();
}
function getTestMetadata()
{
    data = {"all": {"BoundsProcMin": {"process_step": "https://codes.nws.noaa.gov/StatPP/Methods/Arith/Min", "long_name": "Minimum within bounds", "name": "BoundsProcMin", "LE_ProcessStep": "https://codes.nws.noaa.gov/StatPP/Methods/Arith/Min"}, "METAR_TotalPrecip_24__": {"_FillValue": "9999", "scale_factor": "100.0", "name": "METAR_TotalPrecip_24__", "ancillary_variables": "OM_phenomenonTimeInstant OM_resultTime OM_validTime OM_phenomenonTimePeriod24hr BoundsProcSum ", "bounds": "time_bounds", "LE_Source": "METAR", "long_name": "24-hour precipitation amount", "standard_name": "precipitation_amount", "cell_methods": "default_time_coordinate_size :sum", "units": "in", "valid_min": "0", "valid_max": "24", "OM_procedure": "( BoundsProcSum )", "OM_observedProperty": "https://codes.nws.noaa.gov/Data/Met/Moist/TotalPrecip"}, "METAR_Temp_24_2_1": {"comment": "Minimum and maximum values depend on season and region", "_FillValue": "9999", "name": "METAR_Temp_24_2_1", "standard_name": "air_temperature", "ancillary_variables": "OM_phenomenonTimeInstant OM_resultTime OM_validTime OM_phenomenonTimePeriod24hr BoundsProcMin ", "bounds": "time_bounds", "coordinates": "elev0", "long_name": "calendar day minimum temperature", "LE_Source": "METAR", "cell_methods": "default_time_coordinate_size : minimum", "units": "degF", "OM_procedure": "( BoundsProcMin )", "OM_observedProperty": "https://codes.nws.noaa.gov/Data/Met/Temp/Temp"}, "METAR_M2KCodedWxGroup1_instant__": {"comment": "enumeration legend available at:", "_FillValue": "9999", "name": "METAR_M2KCodedWxGroup1_instant__", "standard_name": "precipitation_amount", "ancillary_variables": "OM_phenomenonTimeInstant OM_resultTime OM_validTime ", "LE_Source": "METAR", "long_name": "present weather group 1", "valid_min": "0", "valid_max": "208", "OM_procedure": "( )", "OM_observedProperty": "https://codes.nws.noaa.gov/Data/Met/Wx/M2KCodedWxGroup1"}, "METAR_temperature_6_hour_maximum_6_2_": {"comment": "Minimum and maximum values depend on season and region", "_FillValue": "9999", "name": "METAR_temperature_6_hour_maximum_6_2_", "standard_name": "air_temperature", "ancillary_variables": "OM_phenomenonTimeInstant OM_resultTime OM_validTime OM_phenomenonTimePeriod6hr BoundsProcMax ", "bounds": "time_bounds", "coordinates": "elev0", "long_name": "6-hour maximum temperature", "LE_Source": "METAR", "cell_methods": "default_time_coordinate_size : maximum", "units": "Fahrenheit", "OM_procedure": "( BoundsProcMax )", "OM_observedProperty": "https://codes.nws.noaa.gov/Data/Met/temperature_6_hour_maximum"}, "METAR_Temp_instant_2_": {"_FillValue": "9999", "name": "METAR_Temp_instant_2_", "ancillary_variables": "OM_phenomenonTimeInstant OM_resultTime OM_validTime ", "standard_name": "air_temperature", "coordinates": "elev0", "long_name": "dry bulb temperature", "LE_Source": "METAR", "units": "degF", "valid_min": "-80", "valid_max": "130", "OM_procedure": "( )", "OM_observedProperty": "https://codes.nws.noaa.gov/Data/Met/Temp/Temp"}, "METAR_latitude_instant__": {"_FillValue": "9999.0", "name": "METAR_latitude_instant__", "ancillary_variables": "OM_phenomenonTimeInstant OM_resultTime OM_validTime ", "standard_name": "latitude", "long_name": "latitude", "LE_Source": "METAR", "units": "degrees_north", "valid_min": "-90.0", "valid_max": "90.0", "OM_procedure": "( )"}, "OM_phenomenonTimePeriod24hr": {"_FillValue": "-9999", "name": "OM_phenomenonTimePeriod24hr", "standard_name": "time", "wisps_role": "OM_phenomenonTime", "units": "seconds since 1970-01-01 00:00:00.0", "calendar": "gregorian"}, "OM_validTime": {"_FillValue": "-9999", "name": "OM_validTime", "standard_name": "time", "wisps_role": "OM_validTime", "units": "seconds since 1970-01-01 00:00:00.0", "calendar": "gregorian"}, "OM_phenomenonTimePeriod6hr": {"_FillValue": "-9999", "name": "OM_phenomenonTimePeriod6hr", "standard_name": "time", "wisps_role": "OM_phenomenonTime", "units": "seconds since 1970-01-01 00:00:00.0", "calendar": "gregorian"}, "METAR_CldHght_instant__2": {"_FillValue": "9999", "name": "METAR_CldHght_instant__2", "ancillary_variables": "OM_phenomenonTimeInstant OM_resultTime OM_validTime ", "standard_name": "convective_cloud_base_height", "long_name": "cloud height layer 3", "LE_Source": "METAR", "units": "feet", "OM_procedure": "( )", "OM_observedProperty": "https://codes.nws.noaa.gov/Data/Met/CldHght"}, "METAR_SunDuratn_instant__": {"_FillValue": "9999", "name": "METAR_SunDuratn_instant__", "ancillary_variables": "OM_phenomenonTimeInstant OM_resultTime OM_validTime ", "standard_name": "duration_of_sunshine", "long_name": "minutes of sunshine", "LE_Source": "METAR", "units": "minutes", "OM_procedure": "( )", "OM_observedProperty": "https://codes.nws.noaa.gov/Data/Met/Cloud/SunDuratn"}, "OM_phenomenonTimePeriod3hr": {"_FillValue": "-9999", "name": "OM_phenomenonTimePeriod3hr", "standard_name": "time", "wisps_role": "OM_phenomenonTime", "units": "seconds since 1970-01-01 00:00:00.0", "calendar": "gregorian"}, "METAR_CldHght_instant__4": {"_FillValue": "9999", "name": "METAR_CldHght_instant__4", "ancillary_variables": "OM_phenomenonTimeInstant OM_resultTime OM_validTime ", "standard_name": "convective_cloud_base_height", "long_name": "cloud height layer 5", "LE_Source": "METAR", "units": "feet", "OM_procedure": "( )", "OM_observedProperty": "https://codes.nws.noaa.gov/Data/Met/CldHght"}, "METAR_CldAmt_instant__": {"_FillValue": "9999", "name": "METAR_CldAmt_instant__", "ancillary_variables": "OM_phenomenonTimeInstant OM_resultTime OM_validTime ", "long_name": "sattelite effective cloud amount from GOES-West", "LE_Source": "METAR", "OM_procedure": "( )", "OM_observedProperty": "https://codes.nws.noaa.gov/Data/Met/CldAmt"}, "METAR_M2KCodedWxGroup3_instant__": {"comment": "enumeration legend available at:", "_FillValue": "9999", "name": "METAR_M2KCodedWxGroup3_instant__", "standard_name": "precipitation_amount", "ancillary_variables": "OM_phenomenonTimeInstant OM_resultTime OM_validTime ", "LE_Source": "METAR", "long_name": "present weather group 3", "valid_min": "0", "valid_max": "208", "OM_procedure": "( )", "OM_observedProperty": "https://codes.nws.noaa.gov/Data/Met/Wx/M2KCodedWxGroup3"}, "METAR_longitude_instant__": {"_FillValue": "9999.0", "name": "METAR_longitude_instant__", "ancillary_variables": "OM_phenomenonTimeInstant OM_resultTime OM_validTime ", "standard_name": "longitude", "long_name": "longitude", "LE_Source": "METAR", "units": "degrees_west", "valid_min": "-180.0", "valid_max": "180.0", "OM_procedure": "( )"}, "OM_resultTime": {"_FillValue": "-9999", "name": "OM_resultTime", "standard_name": "time", "wisps_role": "OM_resultTime", "units": "seconds since 1970-01-01 00:00:00.0", "calendar": "gregorian"}, "METAR_station_name_instant__": {"comment": " Only currently archives reports from stations only if the first letter of the ICAO ID is 'K', 'P', 'M', 'C', or 'T'. ", "_FillValue": "_", "name": "METAR_station_name_instant__", "ancillary_variables": "OM_phenomenonTimeInstant OM_resultTime OM_validTime ", "standard_name": "platform_id", "long_name": "ICAO METAR call letters", "LE_Source": "METAR", "OM_procedure": "( )"}, "begin_end_size": {"begin_end_size": "TM_Period:Beginning TM_Period:Ending", "name": "begin_end_size", "long_name": "time bound description"}, "METAR_snow_depth_on_ground_instant__": {"_FillValue": "9999", "name": "METAR_snow_depth_on_ground_instant__", "ancillary_variables": "OM_phenomenonTimeInstant OM_resultTime OM_validTime ", "standard_name": "surface_snow_thickness", "long_name": "snow depth on the ground", "LE_Source": "METAR", "units": "in", "OM_procedure": "( )", "OM_observedProperty": "https://codes.nws.noaa.gov/Data/Met/snow_depth_on_ground"}, "METAR_station_type_instant__": {"_FillValue": "15", "name": "METAR_station_type_instant__", "ancillary_variables": "OM_phenomenonTimeInstant OM_resultTime OM_validTime ", "standard_name": "platform_id", "long_name": "station type", "LE_Source": "METAR", "OM_procedure": "( )"}, "METAR_TotalPrecip_3__": {"_FillValue": "9999", "scale_factor": "100.0", "name": "METAR_TotalPrecip_3__", "ancillary_variables": "OM_phenomenonTimeInstant OM_resultTime OM_validTime OM_phenomenonTimePeriod3hr BoundsProcSum ", "bounds": "time_bounds", "LE_Source": "METAR", "long_name": "3-hour precipitation amount", "standard_name": "precipitation_amount", "cell_methods": "default_time_coordinate_size :sum", "units": "in", "valid_min": "0", "valid_max": "9", "OM_procedure": "( BoundsProcSum )", "OM_observedProperty": "https://codes.nws.noaa.gov/Data/Met/Moist/TotalPrecip"}, "METAR_snowfall_amount_instant__": {"comment": "amount of snowfall that has fallen in the past hour. must be > .5 inch", "_FillValue": "9999", "name": "METAR_snowfall_amount_instant__", "ancillary_variables": "OM_phenomenonTimeInstant OM_resultTime OM_validTime ", "standard_name": "snowfall_amount", "long_name": "snowfall amount", "LE_Source": "METAR", "units": "in", "OM_procedure": "( )", "OM_observedProperty": "https://codes.nws.noaa.gov/Data/Met/snowfall_amount"}, "METAR_Pres_instant__": {"comment": "metar does not include leading 9 or 10. This attribute does", "_FillValue": "9999.0", "name": "METAR_Pres_instant__", "standard_name": "air_pressure_at_sea_level", "ancillary_variables": "OM_phenomenonTimeInstant OM_resultTime OM_validTime ", "LE_Source": "METAR", "long_name": "mean sea level pressure", "valid_min": "875.0", "units": "millibar", "valid_max": "1075.0", "OM_procedure": "( )", "OM_observedProperty": "https://codes.nws.noaa.gov/Data/Met/Mass/Pres"}, "METAR_Temp_24_2_": {"comment": "Minimum and maximum values depend on season and region", "_FillValue": "9999", "name": "METAR_Temp_24_2_", "standard_name": "air_temperature", "ancillary_variables": "OM_phenomenonTimeInstant OM_resultTime OM_validTime OM_phenomenonTimePeriod24hr BoundsProcMax ", "bounds": "time_bounds", "coordinates": "elev0", "long_name": "Calendar day maximum temperature", "LE_Source": "METAR", "cell_methods": "default_time_coordinate_size : maximum", "units": "degF", "OM_procedure": "( BoundsProcMax )", "OM_observedProperty": "https://codes.nws.noaa.gov/Data/Met/Temp/Temp"}, "METAR_M2KCodedWxGroup2_instant__": {"comment": "enumeration legend available at:", "_FillValue": "9999", "name": "METAR_M2KCodedWxGroup2_instant__", "ancillary_variables": "OM_phenomenonTimeInstant OM_resultTime OM_validTime ", "LE_Source": "METAR", "standard_name": "present_weather", "valid_min": "0", "valid_max": "208", "OM_procedure": "( )", "OM_observedProperty": "https://codes.nws.noaa.gov/Data/Met/Wx/M2KCodedWxGroup2"}, "METAR_DewPt_instant_2_": {"_FillValue": "9999", "name": "METAR_DewPt_instant_2_", "ancillary_variables": "OM_phenomenonTimeInstant OM_resultTime OM_validTime ", "standard_name": "dew_point_temperature", "coordinates": "elev0", "long_name": "dew point temperature", "LE_Source": "METAR", "units": "degF", "valid_min": "-85", "valid_max": "80", "OM_procedure": "( )", "OM_observedProperty": "https://codes.nws.noaa.gov/Data/Met/Temp/DewPt"}, "METAR_TotalPrecip_1__": {"comment": "A -4 is used to represent a trace amount\n A -9 is used to represent an indeterminate amount", "_FillValue": "9999", "scale_factor": "100.0", "name": "METAR_TotalPrecip_1__", "standard_name": "precipitation_amount", "ancillary_variables": "OM_phenomenonTimeInstant OM_resultTime OM_validTime OM_phenomenonTimePeriod1hr BoundsProcSum ", "bounds": "time_bounds", "long_name": "Hourly precipitation amount", "LE_Source": "METAR", "cell_methods": "default_time_coordinate_size:sum", "units": "in", "valid_min": "0", "valid_max": "3", "OM_procedure": "( BoundsProcSum )", "OM_observedProperty": "https://codes.nws.noaa.gov/Data/Met/Moist/TotalPrecip"}, "METAR_WSpd_instant_2_": {"comment": "Wind speed is set to -9 if winds are variable.", "_FillValue": "9999", "name": "METAR_WSpd_instant_2_", "standard_name": "wind_speed", "ancillary_variables": "OM_phenomenonTimeInstant OM_resultTime OM_validTime ", "LE_Source": "METAR", "coordinates": "elev0", "long_name": "wind speed", "valid_min": "0", "units": "knot", "valid_max": "75", "OM_procedure": "( )", "OM_observedProperty": "https://codes.nws.noaa.gov/Data/Met/Moment/WSpd"}, "METAR_CldAmt_instant__8": {"_FillValue": "9999", "name": "METAR_CldAmt_instant__8", "ancillary_variables": "OM_phenomenonTimeInstant OM_resultTime OM_validTime ", "standard_name": "cloud_area_fraction_in_atmosphere_layer", "long_name": "cloud amount layer 5", "LE_Source": "METAR", "valid_min": "0", "valid_max": "10", "OM_procedure": "( )", "OM_observedProperty": "https://codes.nws.noaa.gov/Data/Met/CldAmt"}, "METAR_CldAmt_instant__7": {"_FillValue": "9999", "name": "METAR_CldAmt_instant__7", "ancillary_variables": "OM_phenomenonTimeInstant OM_resultTime OM_validTime ", "standard_name": "cloud_area_fraction_in_atmosphere_layer", "long_name": "cloud amount layer 6", "LE_Source": "METAR", "valid_min": "0", "valid_max": "10", "OM_procedure": "( )", "OM_observedProperty": "https://codes.nws.noaa.gov/Data/Met/CldAmt"}, "METAR_Gust_instant_2_": {"_FillValue": "9999", "name": "METAR_Gust_instant_2_", "ancillary_variables": "OM_phenomenonTimeInstant OM_resultTime OM_validTime ", "standard_name": "wind_speed_of_gust", "coordinates": "elev0", "long_name": "wind speed of gust", "LE_Source": "METAR", "units": "knot", "valid_min": "0", "valid_max": "200", "OM_procedure": "( )", "OM_observedProperty": "https://codes.nws.noaa.gov/Data/Met/Moment/Gust"}, "BoundsProcMax": {"process_step": "https://codes.nws.noaa.gov/StatPP/Methods/Arith/Max", "long_name": "Maximum within bounds", "name": "BoundsProcMax", "LE_ProcessStep": "https://codes.nws.noaa.gov/StatPP/Methods/Arith/Max"}, "OM_phenomenonTimePeriod1hr": {"_FillValue": "-9999", "name": "OM_phenomenonTimePeriod1hr", "standard_name": "time", "wisps_role": "OM_phenomenonTime", "units": "seconds since 1970-01-01 00:00:00.0", "calendar": "gregorian"}, "OM_phenomenonTimeInstant": {"_FillValue": "-9999", "name": "OM_phenomenonTimeInstant", "standard_name": "time", "wisps_role": "OM_phenomenonTime", "units": "seconds since 1970-01-01 00:00:00.0", "calendar": "gregorian"}, "METAR_TotalPrecip_6__": {"_FillValue": "9999", "scale_factor": "100.0", "name": "METAR_TotalPrecip_6__", "ancillary_variables": "OM_phenomenonTimeInstant OM_resultTime OM_validTime OM_phenomenonTimePeriod6hr BoundsProcSum ", "bounds": "time_bounds", "LE_Source": "METAR", "long_name": "6-hour precipitation amount", "standard_name": "precipitation_amount", "cell_methods": "default_time_coordinate_size :sum", "units": "in", "valid_min": "0", "valid_max": "12", "OM_procedure": "( BoundsProcSum )", "OM_observedProperty": "https://codes.nws.noaa.gov/Data/Met/Moist/TotalPrecip"}, "METAR_AltimtrStg_instant__": {"_FillValue": "9999.0", "name": "METAR_AltimtrStg_instant__", "ancillary_variables": "OM_phenomenonTimeInstant OM_resultTime OM_validTime ", "standard_name": "altimeter_range", "long_name": "altimiter setting", "LE_Source": "METAR", "units": "mm Hg", "valid_min": "24.0", "valid_max": "32.0", "OM_procedure": "( )", "OM_observedProperty": "https://codes.nws.noaa.gov/Data/Met/AltimtrStg"}, "METAR_CldAmt_instant__4": {"comment": "Enumeration can be found at:", "_FillValue": "9999", "name": "METAR_CldAmt_instant__4", "standard_name": "cloud_area_fraction_in_atmosphere_layer", "ancillary_variables": "OM_phenomenonTimeInstant OM_resultTime OM_validTime ", "LE_Source": "METAR", "long_name": "cloud amount layer 3", "valid_min": "0", "valid_max": "10", "OM_procedure": "( )", "OM_observedProperty": "https://codes.nws.noaa.gov/Data/Met/CldAmt"}, "METAR_CldAmt_instant__5": {"comment": "Enumeration can be found at:", "_FillValue": "9999", "name": "METAR_CldAmt_instant__5", "standard_name": "cloud_area_fraction_in_atmosphere_layer", "ancillary_variables": "OM_phenomenonTimeInstant OM_resultTime OM_validTime ", "LE_Source": "METAR", "long_name": "cloud amount layer 2", "valid_min": "0", "valid_max": "10", "OM_procedure": "( )", "OM_observedProperty": "https://codes.nws.noaa.gov/Data/Met/CldAmt"}, "METAR_CldAmt_instant__6": {"comment": "Enumeration can be found at:", "_FillValue": "9999", "name": "METAR_CldAmt_instant__6", "standard_name": "cloud_area_fraction_in_atmosphere_layer", "ancillary_variables": "OM_phenomenonTimeInstant OM_resultTime OM_validTime ", "LE_Source": "METAR", "long_name": "cloud amount layer 1", "valid_min": "0", "valid_max": "10", "OM_procedure": "( )", "OM_observedProperty": "https://codes.nws.noaa.gov/Data/Met/CldAmt"}, "elev0": {"name": "elev0", "positive": "up", "long_name": "height above surface", "standard_name": "height", "units": "m", "axis": "Z"}, "METAR_CldAmt_instant__1": {"_FillValue": "9999", "name": "METAR_CldAmt_instant__1", "ancillary_variables": "OM_phenomenonTimeInstant OM_resultTime OM_validTime ", "standard_name": "cloud_area_fraction", "long_name": "sattelite effective cloud amount from GOES-East", "LE_Source": "METAR", "OM_procedure": "( )", "OM_observedProperty": "https://codes.nws.noaa.gov/Data/Met/CldAmt"}, "METAR_CldAmt_instant__2": {"_FillValue": "9999", "name": "METAR_CldAmt_instant__2", "ancillary_variables": "OM_phenomenonTimeInstant OM_resultTime OM_validTime ", "standard_name": "cloud_area_fraction", "long_name": "satellite cloud amount category from GOES-East", "LE_Source": "METAR", "OM_procedure": "( )", "OM_observedProperty": "https://codes.nws.noaa.gov/Data/Met/CldAmt"}, "METAR_CldHght_instant__3": {"_FillValue": "9999", "name": "METAR_CldHght_instant__3", "ancillary_variables": "OM_phenomenonTimeInstant OM_resultTime OM_validTime ", "standard_name": "convective_cloud_base_height", "long_name": "cloud height layer 4", "LE_Source": "METAR", "units": "feet", "OM_procedure": "( )", "OM_observedProperty": "https://codes.nws.noaa.gov/Data/Met/CldHght"}, "METAR_CldAmt_instant__3": {"_FillValue": "9999", "name": "METAR_CldAmt_instant__3", "ancillary_variables": "OM_phenomenonTimeInstant OM_resultTime OM_validTime ", "standard_name": "cloud_area_fraction", "long_name": "sattelite cloud amount from GOES-West", "LE_Source": "METAR", "OM_procedure": "( )", "OM_observedProperty": "https://codes.nws.noaa.gov/Data/Met/CldAmt"}, "METAR_Temp_6_2_": {"comment": "Minimum and maximum values depend on season and region", "_FillValue": "9999", "name": "METAR_Temp_6_2_", "standard_name": "air_temperature", "ancillary_variables": "OM_phenomenonTimeInstant OM_resultTime OM_validTime OM_phenomenonTimePeriod6hr BoundsProcMin ", "bounds": "time_bounds", "coordinates": "elev0", "long_name": "6-hour minimum temperature", "LE_Source": "METAR", "cell_methods": "default_time_coordinate_size : minimum", "units": "Fahrenheit", "OM_procedure": "( BoundsProcMin )", "OM_observedProperty": "https://codes.nws.noaa.gov/Data/Met/Temp/Temp"}, "METAR_CldAmt_instant__9": {"comment": "Enumeration can be found at:", "_FillValue": "9999", "name": "METAR_CldAmt_instant__9", "standard_name": "cloud_area_fraction_in_atmosphere_layer", "ancillary_variables": "OM_phenomenonTimeInstant OM_resultTime OM_validTime ", "LE_Source": "METAR", "long_name": "cloud amount layer 4", "valid_min": "0", "valid_max": "10", "OM_procedure": "( )", "OM_observedProperty": "https://codes.nws.noaa.gov/Data/Met/CldAmt"}, "METAR_CldHght_instant__1": {"_FillValue": "9999", "name": "METAR_CldHght_instant__1", "ancillary_variables": "OM_phenomenonTimeInstant OM_resultTime OM_validTime ", "standard_name": "convective_cloud_base_height", "long_name": "cloud height layer 2", "LE_Source": "METAR", "units": "feet", "OM_procedure": "( )", "OM_observedProperty": "https://codes.nws.noaa.gov/Data/Met/CldHght"}, "METAR_CldHght_instant__": {"_FillValue": "9999", "name": "METAR_CldHght_instant__", "ancillary_variables": "OM_phenomenonTimeInstant OM_resultTime OM_validTime ", "standard_name": "convective_cloud_base_height", "long_name": "cloud height layer 1", "LE_Source": "METAR", "units": "feet", "OM_procedure": "( )", "OM_observedProperty": "https://codes.nws.noaa.gov/Data/Met/CldHght"}, "METAR_CldHght_instant__5": {"_FillValue": "9999", "name": "METAR_CldHght_instant__5", "ancillary_variables": "OM_phenomenonTimeInstant OM_resultTime OM_validTime ", "standard_name": "convective_cloud_base_height", "long_name": "cloud height layer 6", "LE_Source": "METAR", "units": "feet", "OM_procedure": "( )", "OM_observedProperty": "https://codes.nws.noaa.gov/Data/Met/CldHght"}, "METAR_Vsby_instant__": {"_FillValue": "9999.0", "name": "METAR_Vsby_instant__", "ancillary_variables": "OM_phenomenonTimeInstant OM_resultTime OM_validTime ", "standard_name": "visibility_in_air", "long_name": "horizontal visiblity", "LE_Source": "METAR", "units": "miles", "valid_min": "0.0", "valid_max": "40.0", "OM_procedure": "( )", "OM_observedProperty": "https://codes.nws.noaa.gov/Data/Met/Phys/Vsby"}, "METAR_WindDir_instant_2_": {"comment": "Wind direction is set to 0 if winds are variable.", "_FillValue": "9999", "name": "METAR_WindDir_instant_2_", "standard_name": "wind_from_direction", "ancillary_variables": "OM_phenomenonTimeInstant OM_resultTime OM_validTime ", "LE_Source": "METAR", "coordinates": "elev0", "long_name": "wind direction", "valid_min": "0", "units": "degrees", "valid_max": "360", "OM_procedure": "( )", "OM_observedProperty": "https://codes.nws.noaa.gov/Data/Met/Moment/WindDir"}, "BoundsProcSum": {"process_step": "https://codes.nws.noaa.gov/StatPP/Methods/Arith/Sum", "long_name": "summation within bounds", "name": "BoundsProcSum", "LE_ProcessStep": "https://codes.nws.noaa.gov/StatPP/Methods/Arith/Sum"}}, "primary": ["METAR_Temp_instant_2_", "METAR_Gust_instant_2_", "METAR_temperature_6_hour_maximum_6_2_", "METAR_SunDuratn_instant__", "METAR_longitude_instant__", "METAR_DewPt_instant_2_", "METAR_WSpd_instant_2_", "METAR_WindDir_instant_2_", "METAR_Pres_instant__", "METAR_Temp_24_2_", "METAR_TotalPrecip_3__", "METAR_CldAmt_instant__", "METAR_TotalPrecip_6__", "METAR_CldAmt_instant__1", "METAR_CldAmt_instant__2", "METAR_CldHght_instant__", "METAR_CldHght_instant__1", "METAR_CldHght_instant__2", "METAR_CldHght_instant__3", "METAR_CldHght_instant__4", "METAR_CldHght_instant__5", "METAR_CldAmt_instant__3", "METAR_Temp_24_2_1", "METAR_TotalPrecip_1__", "METAR_Temp_6_2_", "METAR_M2KCodedWxGroup1_instant__", "METAR_M2KCodedWxGroup2_instant__", "METAR_M2KCodedWxGroup3_instant__", "METAR_snowfall_amount_instant__", "METAR_snow_depth_on_ground_instant__", "METAR_CldAmt_instant__4", "METAR_CldAmt_instant__5", "METAR_CldAmt_instant__6", "METAR_CldAmt_instant__7", "METAR_CldAmt_instant__8", "METAR_CldAmt_instant__9", "METAR_Vsby_instant__", "METAR_TotalPrecip_24__", "METAR_latitude_instant__", "METAR_AltimtrStg_instant__", "METAR_station_type_instant__", "METAR_station_name_instant__"]}
    return data
}
function getVars()
{
    var data;
    d3.json("test2.json", function(error, json) {
    //d3.json("http://seethepeak.com/myapp/", function(error, json) {
    if (error) {
       // return console.warn(error);
      json = getTestMetadata();
    }
    all_vars = json['all'];
    primary_vars = json['primary'];
    d3.select("#vars")
    .selectAll("div")
    .data(primary_vars)
    .enter()
    .append('div')
    .classed('varText', true)
    .on('click', function(d){
        displayMetadata(d)
        centerScreen(d);
    })
    .text(function(d){return d});
    populateGraph(json);
    });
    
}
function centerScreen(varname)
{
    var myele = d3.selectAll('.gfxHolder')
        .filter(function(d){
            return d.name == varname;
        });
    myele.select('circle').transition().delay(500).duration(1000).attr('r', 50).each('end', function(){
        d3.select(this).transition().delay(2000).duration(2000).attr('r', 40);
    });
    var gfxWrapper = document.getElementById('gfxWrapper');
    var offsetLeft = gfxWrapper.offsetLeft; 
    var offsetTop = gfxWrapper.offsetTop;
    var width = gfxWrapper.clientWidth;
    var height = gfxWrapper.clientHeight;
    var trans = d3.transform(myele.attr('transform'));
    var x = trans.translate[0];
    var y = trans.translate[1];
    var z = trans.scale;
    var newX = ((width/2) - x);
    var newY = ((height/2) - y);
    /*console.log(offsetLeft);
    console.log(offsetTop);
    console.log(width);
    console.log(x);
    console.log(y);
    console.log(z);*/
    d3.select('#moveableG')
        .transition().duration(1000)
        .attr('transform', 'translate('+newX+','+newY+') scale('+z+')');
    myzoom.translate([newX,newY]).scale(1);
    

}
var displayHint = function()
{
    hints = {
        'ancillary_variables': 'All the variables that help describe this.',
        'cell_methods' : 'When a dimensional bound is applied to a variable, the cell_method attribute' + 
            ' describes how the values within the bounds are computed.',
        'LE_Source' : 'Where the data comes from',
        'OM_procedure' : 'Defined in ISO standards. The procedures that were applied to this variable. Refer to ancillary_variables for more information',
        'OM_observedProperty' : 'Defined in the ISO standards. The property that has been observed without applied process.',
        '_FillValue' : 'Value that is used where no observable/computable value exists.'

    }
    var marginTop = 20;
    var marginLeft = 20;
    var ele = d3.select(this);
    keyname = ele.text();
    mouseEvt = d3.mouse(this);
    evt = d3.event;
    console.log(mouseEvt);
    var hintText = hints[keyname];
    if(hintText)
    {
    d3.select('#hint')
        .style('visibility', 'visible')
        .style('left', (evt.clientX + marginLeft) + 'px')
        .style('top', (evt.clientY + marginTop) + 'px')
        .text(hintText);
    }

}
var displayMetadata = function(varname)
{
    connectDots(varname);

    metadata = all_vars[varname];
    var desc = d3.select('#desc');
    var table = d3.select('#metatable');
    var button = d3.select('#fetchButton');
    button.style('visibility', 'visible');
    //var keys = d3.select('#metaKeys');
    //var values = d3.select('#metaValues');
    name = metadata['name'];
    d3.select("#metadataHeader")
        .text("Metadata for " + name);
    d3.selectAll('tr').remove();
    // Where 'i' is the name of the key
    for(var i in metadata)
    {
        if(i == 'name')
            continue
        var value = metadata[i]
        var tr = table.append('tr')
        tr.append('td')
       //     .on('mouseover', function(){d3.select('#hint').style('visibility', 'visible');})
            .on('mousemove', displayHint)
            .on('mouseout', function(){d3.select('#hint').style('visibility', 'hidden');})
            .text(i);
        var td = tr.append('td');
        // If it's probably a link
        if(value.substr(0,4) == 'http')
            td.append('a')
                .attr('href', value)
                .attr('target', '_blank')
                .text(value);
        else if(i == 'ancillary_variables')
        {
            console.log("anc here");
            ancVars = value.replace(/^\s+|\s+$/g, '').split(" ");
            console.log(ancVars);
            for(j=0; j < ancVars.length; j++)
            {
                var curVar = ancVars[j];
                td.append("div")
                    .classed("varText", true)
                    .style('display', 'inline-block')
                    .on('click', function(){
                        ancname = d3.select(this).text();
                        console.log(ancname)
                        displayMetadata(ancname);
                        centerScreen(ancname);
                    })
                    .text(curVar);
            }
        }
        else if(i == 'coordinates')
        {
            ancVars = value.split(" ");
            for(j=0; j < ancVars.length; j++)
            {
                var curVar = ancVars[j];
                td.append("div")
                    .classed("varText", true)
                    .style('display', 'inline')
                    .on('click', function(){
                        displayMetadata(curVar);
                        centerScreen(curVar);
                    })
                    .text(curVar);
            }
        }
        else
            td.text(value);
    }
        
}
var myzoom;
function addZoom()
{
    var gfx = d3.select("#outerG");
    myzoom = d3.behavior.zoom()
        .scaleExtent([.3,4])
        .on("zoom", function() {
            d3.select('#moveableG').attr("transform", "translate(" + d3.event.translate + ")" + "scale(" + d3.event.scale + ")")
        })
        gfx.call(myzoom);
       
}
function populateGraph(json)
{
    varsDict = json['all'];
    var values = Object.keys(varsDict).map(function(key){
            return varsDict[key];
    });
    values.sort(function(x,y){
            if( x.name.match(/Time.*/) || x.name.match(/time_bounds\d*/))
                return -1;
            if(x.name.match(/.*Proc.*/))
                return -1;
            return 1;
    });
     
    var moveableG = d3.select('#moveableG');
    //Add a rect so you can grab 'white' space
    moveableG.append('rect')
        .attr('x', -1500)
        .attr('y', -1500)
        .attr('width', 3500)
        .attr('height', 3500)
        .style('fill', 'none')
        .style('pointer-events', 'all');


    var modifier = 0
    var gfxVars = moveableG.selectAll("circle")
        .data(values)
        .enter()
        .append('g')
        .classed('gfxHolder',true)
        .attr('transform', function(d,i)
                {
                    if(i != 0 && i % 6 == 0)
                        modifier += 30
                    //return 'translate('+(Math.random() * 1000)+','+(Math.random() * 500)+')'
                    var DIST_CONST = 100;
                    dist = (Math.floor(i/6) + 1) * DIST_CONST;
                    //dist = i * 40
                    console.log(i)
                    console.log(dist)
                    pos = (i%6 * 60) + modifier;

                    return 'translate('+
                            (Math.cos(pos * Math.PI/180)*dist)+ ","+
                            (Math.sin(pos * Math.PI/180)*dist)+')';

 /*                   if(i != 0 && i % 6 == 0)
                        modifier += 30
                    //return 'translate('+(Math.random() * 1000)+','+(Math.random() * 500)+')'
                    var DIST_CONST = 100;
                    dist = (i * 20) + 50
                    console.log(i)
                    console.log(dist)
                    pos = (i * (30/Math.log10(i+2))) ;

                    return 'translate('+
                            (Math.cos(pos * Math.PI/180)*dist)+ ","+
                            (Math.sin(pos * Math.PI/180)*dist)+')';
                            */
                        })
     console.log(primary_vars);
        gfxVars.append('circle')
        //.attr('cx', function(d,i){ return Math.random() * 500})
        //.attr('cy', function(d,i){ return Math.random() * 500})
        .attr('r', 40)
        .attr('class', function(d) {
            for( i in primary_vars)
            {
                if (i == d['name'])
                    return 'primary';
            }
            if(primary_vars.includes( d['name']) )
            {
                return 'primary';
            }
            if( d['name'].match(/Time.*/) || d.name.match(/time_bounds\d*/))
                return 'time';

            if( d.name.match(/.*Proc.*/))
                return 'proc';

            return 'secondary';
                    });

        gfxVars.on('click', function(d){
            
            displayMetadata(d.name);
        })
        .on('mouseover', function(){
            curVar = d3.select(this).select('circle');
            curVar.transition()
                .attr('r', 45);
            displayText(curVar.datum().name);

        })
        .on('mouseout', function(){
            d3.select(this).select('circle')
                .transition()
                .attr('r', 40);
            undisplayText();
        });
       gfxVars.append('text')
           .attr('text-anchor','middle')
           .style('color', 'white')
           .style('font-size','.30em')
           .text(function(d){return d.name});
}
function displayText(text)
{
    len = text.length;
    d3.select('#gfxText').style('display','block').text(text);
    d3.select('#textbg').style('display','block').attr('width', text.length*9.2);
}
function undisplayText()
{
    d3.select('#gfxText').style('display','none');
    d3.select('#textbg').style('display','none');
}
function linkAll()
{
    for( i=0; i < primary_vars.length; i++)
    {
        connectDots(primary_vars[i],false);
    }
}
function connectDots(varname, remove=true)
{
    if(remove)
        d3.selectAll('.connect').remove()
    var allHolders = d3.selectAll('.gfxHolder');
    var myEle = allHolders.filter(function(d){
            return d.name == varname;
        });
    ancilVars = getAncil(myEle);
    ancilHolders = allHolders.filter(function(d){
            return ancilVars.includes(d.name);
        });
    ancilHolders.each(function(d,i)
            {
               drawLine(myEle,d3.select(this));
            });
    ancilVars.push(varname);
    if (ancilVars.length > 2)
        emphasizeEles(ancilVars);
    else
        unemphasizeEles();

}
function emphasizeEles(names)
{
    var allEles = d3.selectAll('.gfxHolder');
    allEles.style('opacity', 1);
    allEles.filter(function(d){
            return !names.includes(d.name);
        }).style('opacity', .4);

}
function unemphasizeEles()
{
    var myele = d3.selectAll('.gfxHolder')
        .style('opacity',1)
}
function drawLine(nodeA, nodeB)
{
    var radiusA = 40;
    var radiusB = 40;
    var xy1 = d3.transform(nodeA.attr('transform')).translate;
    var xy2 = d3.transform(nodeB.attr('transform')).translate;
    
    var slope = (xy2[1] - xy1[1]) / (xy2[0] - xy1[0]);
    var angle = Math.atan(slope);
    var modifier = -1;
    if(xy1[0] > xy2[0])
        modifier = -1;
    else 
        modifier = 1;
    x1 = xy1[0] + Math.cos(angle) * modifier * radiusA
    y1 = xy1[1] + Math.sin(angle) * modifier * radiusA

    if(xy1[0] < xy2[0])
        modifier = -1;
    else 
        modifier = 1;
    x2 = xy2[0] + Math.cos(angle) * modifier * radiusB
    y2 = xy2[1] + Math.sin(angle) * modifier * radiusB

    var line = d3.select("#moveableG")
        .append('line')
        .classed('connect', true)
        .attr('x1', x1)
        .attr('y1', y1)
        .attr('x2', x2)
        .attr('y2', y2)
        .attr('stroke-width', '2px')
        .attr('stroke', '#333');
}
function getAncil(d)
{
    // Take out white space and split string into array of variables
    var anc = [];
    try
    {
    anc = d.datum().ancillary_variables.replace(/^\s+|\s+$/g, '').split(" ");
    }
    catch(e){}
    // Push the coordinate variable into anc
    try
    {
    anc.push(d.datum().coordinates.replace(/^\s+|\s+$/g, '').split(" "));
    }
    catch(e){}
    return anc;

}
adjustSize = function(event)
{
    var margin = 0;
    var height = window.innerHeight - headerHgt - margin;
    var width = window.innerWidth;
    d3.select("#mainWrapper")
    .style('height', height+'px');
    maxHeight = height;
    var gfx = d3.select("#gfxWrapper");
    var info = d3.select("#desc");
    infoMargin = 3;
    newVal = Math.floor(height/2) - infoMargin + "px";
    info.style('height', newVal);
    gfx.style('height', newVal+4);
    
}



function bindActionEvents()
{
    grabber = d3.select("#grabber")
    var drag = d3.behavior.drag();
    grabber.call(drag);
    drag.on('drag', adjustInfoView);
    var button = d3.select('#fetchButton');
    button.on('click', fetchData)
    var upload = d3.select('#upload');
    upload.on('click', openUpload)
    var closeUpload = d3.select('#closeUploadForm');
    closeUpload.on('click', closeUploadForm)
    addZoom();
}
var closeUploadForm = function()
{
    d3.select('#uploadForm')
            .style('visibility', 'hidden');
}
var openUpload = function()
{    
        d3.select('#uploadForm')
            .style('visibility', 'visible');
}
var fetchData = function()
{
    console.log('fetching data');
}
adjustInfoView = function()
{
    var margin = 50;
    dx = d3.event.dx;
    dy = d3.event.dy;
    var gfx = d3.select("#gfxWrapper");
    var info = d3.select("#desc");
    var gHeight = gfx.style('height');
    var iHeight = info.style('height');
    gNewHeight = parseInt(gHeight.substr(0,gHeight.length - 2)) - dy;
    iNewHeight = parseInt(iHeight.substr(0,iHeight.length - 2)) + dy;
    if ( iNewHeight >= margin && iNewHeight <= (maxHeight - margin))
    {
    gfx.style('height', gNewHeight + 'px');
    info.style('height', iNewHeight + 'px');
    }
}

window.onload = init;
window.onresize = adjustSize;

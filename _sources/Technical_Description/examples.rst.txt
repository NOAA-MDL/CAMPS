********************************
Output Examples
********************************

Sample metar_driver Output
===============================

The example CDL output, from a metar_driver output file, is shown for 2 meter temperature, for 384 hours, and 2584 stations.  
Quality Control was applied to the data, and the metadata variables reflect that procedure application. 
The necessary time and location variables are also included in the output.

::
  
  netcdf camps_metar_output {
  dimensions:
        stations = 2584 ;
        phenomenonTime = 384 ;
        level = 1 ;
        nv = 2 ;
  variables:
        int64 DecodeBUFR ;
                DecodeBUFR:PROV__activity = "StatPP__Methods/Ingest/DecodeBUFR" ;
                DecodeBUFR:PROV__used = "StatPP__Data/Source/NCEPSfcObsMETAR" ;
                DecodeBUFR:long_name = "Ingest BUFR encoded METAR observations from NCEP repository" ;
                DecodeBUFR:standard_name = "source" ;
        int64 METARQC ;
                METARQC:PROV__activity = "StatPP__Methods/QC/METARQC" ;
                METARQC:PROV__wasInformedBy = "DecodeBUFR" ;
                METARQC:long_name = "Apply MDL METAR Quality Control procedure" ;
                METARQC:standard_name = "source" ;
        string stations(stations) ;
                string stations:_FillValue = "_" ;
                stations:long_name = "ICAO METAR call letters" ;
                stations:standard_name = "platform_id" ;
                stations:comment = " Only currently archives reports from stations only if the first letter of the ICAO ID is \'K\', \'P\', \'M\', \'C\', or \'T\'. " ;
                stations:coordinates = "latitude longitude" ;
                stations:missing_value = 9999LL ;
        byte station_type(stations) ;
                station_type:_FillValue = 15b ;
                station_type:standard_name = "platform_id" ;
                station_type:long_name = "station type" ;
                station_type:PROV__hadPrimarySource = "METAR" ;
                station_type:coordinates = "latitude longitude" ;
                station_type:missing_value = 9999LL ;
        double latitude(stations) ;
                latitude:_FillValue = 9999. ;
                latitude:long_name = "latitude" ;
                latitude:units = "degrees_north" ;
                latitude:valid_min = -90. ;
                latitude:valid_max = 90. ;
                latitude:standard_name = "latitude" ;
                latitude:PROV__hadPrimarySource = "METAR" ;
                latitude:coordinates = "latitude longitude" ;
                latitude:missing_value = 9999. ;
        double longitude(stations) ;
                longitude:_FillValue = 9999. ;
                longitude:long_name = "longitude" ;
                longitude:units = "degrees_west" ;
                longitude:valid_min = -180. ;
                longitude:valid_max = 180. ;
                longitude:standard_name = "longitude" ;
                longitude:PROV__hadPrimarySource = "METAR" ;
                longitude:coordinates = "latitude longitude" ;
                longitude:missing_value = 9999. ;
        int64 phenomenonTime(phenomenonTime) ;
                phenomenonTime:_FillValue = 9999LL ;
                phenomenonTime:calendar = "gregorian" ;
                phenomenonTime:units = "seconds since 1970-01-01 00:00:00.0" ;
                phenomenonTime:standard_name = "time" ;
                phenomenonTime:PROV__specializationOf = "( SOSA__phenomenonTime )" ;
        short Temp_instant_2m(phenomenonTime, stations) ;
                Temp_instant_2m:_FillValue = 9999s ;
                Temp_instant_2m:SOSA__observedProperty = "StatPP__Data/Met/Temp/Temp" ;
                Temp_instant_2m:long_name = "dry bulb temperature" ;
                Temp_instant_2m:valid_min = -80s ;
                Temp_instant_2m:valid_max = 130s ;
                Temp_instant_2m:standard_name = "air_temperature" ;
                Temp_instant_2m:units = "degF" ;
                Temp_instant_2m:vertical_coord = "elev0" ;
                Temp_instant_2m:PROV__hadPrimarySource = "METAR" ;
                Temp_instant_2m:coordinates = "phenomenonTime latitude longitude" ;
                Temp_instant_2m:ancillary_variables = "elev0 phenomenonTime DecodeBUFR METARQC " ;
                Temp_instant_2m:missing_value = 9999s ;
                Temp_instant_2m:PROV__wasInformedBy = "( )" ;
                Temp_instant_2m:SOSA__usedProcedure = "( DecodeBUFR METARQC )" ;
  // global attributes:
                :institution = "NOAA/National Weather Service" ;
                :Conventions = "CF-1.7 CAMPS-1.2" ;
                :version = "CAMPS-1.2" ;
                :history = "" ;
                :references = "" ;
                :organization = "NOAA/MDL" ;
                :url = "http://www.nws.noaa.gov/mdl/, https://sats.nws.noaa.gov/~camps/" ;
                :primary_variables = "Temp_instant_2m longitude latitude stations station_type" ;
    // group attributes:
                :PROV__ = "http://www.w3.org/ns/prov/#" ;
                :StatPP__ = "http://codes.nws.noaa.gov/StatPP/" ;
                :SOSA__ = "http://www.w3.org/ns/sosa/" ;
    } // group prefix_list
  }

Sample marine_driver Output
=============================

Marine_driver output is extremely similar to Metar_driver output.  The difference is the procedures, stations, and source of information.  
Everything else is effectively the same, for the same time range and variables.

::
  
  netcdf camps_marine_output {
  dimensions:
        stations = 328 ;
        phenomenonTime = 384 ;
        level = 1 ;
        nv = 2 ;
  variables:
        string stations(stations) ;
                string stations:_FillValue = "_" ;
                stations:long_name = "NDBC station identifiers" ;
                stations:standard_name = "platform_id" ;
                stations:comment = "NDBC stations consist of buoy, C-MAN, and platform drilling sites" ;
                stations:PROV__hadPrimarySource = "NDBC" ;
                stations:coordinates = "latitude longitude" ;
                stations:missing_value = 9999LL ;
        byte station_type(stations) ;
                station_type:_FillValue = 15b ;
                station_type:standard_name = "platform_id" ;
                station_type:long_name = "station type" ;
                station_type:PROV__hadPrimarySource = "NDBC" ;
                station_type:coordinates = "latitude longitude" ;
                station_type:missing_value = 9999LL ;
        double latitude(stations) ;
                latitude:_FillValue = 9999. ;
                latitude:long_name = "latitude" ;
                latitude:units = "degrees_north" ;
                latitude:valid_min = -90. ;
                latitude:valid_max = 90. ;
                latitude:standard_name = "latitude" ;
                latitude:coordinates = "latitude longitude" ;
                latitude:missing_value = 9999. ;
        double longitude(stations) ;
                longitude:_FillValue = 9999. ;
                longitude:long_name = "longitude" ;
                longitude:units = "degrees_west" ;
                longitude:valid_min = -180. ;
                longitude:valid_max = 180. ;
                longitude:standard_name = "longitude" ;
                longitude:coordinates = "latitude longitude" ;
                longitude:missing_value = 9999. ;
        int64 elev0(level) ;
                elev0:long_name = "height above surface" ;
                elev0:units = "m" ;
                elev0:standard_name = "height" ;
                elev0:positive = "up" ;
                elev0:axis = "Z" ;
        int64 phenomenonTime(phenomenonTime) ;
                phenomenonTime:_FillValue = 9999LL ;
                phenomenonTime:calendar = "gregorian" ;
                phenomenonTime:units = "seconds since 1970-01-01 00:00:00.0" ;
                phenomenonTime:standard_name = "time" ;
                phenomenonTime:PROV__specializationOf = "( SOSA__phenomenonTime )" ;
        int64 ProcMarine ;
                ProcMarine:PROV__activity = "StatPP__Methods/Ingest/DecodeTabularText" ;
                ProcMarine:PROV__used = "StatPP__Data/Source/NDBC" ;
                ProcMarine:long_name = "Decode tabular text data" ;
                ProcMarine:standard_name = "source" ;
        int64 MarineQC ;
                MarineQC:PROV__activity = "StatPP__Methods/QC/MarineQC" ;
                MarineQC:PROV__wasInformedBy = "ProcMarine" ;
                MarineQC:long_name = "Marine Observation Quality Control" ;
                MarineQC:standard_name = "source" ;
        short Temp_instant_2m(phenomenonTime, stations) ;
                Temp_instant_2m:_FillValue = 9999s ;
                Temp_instant_2m:SOSA__observedProperty = "StatPP__Data/Met/Temp/Temp" ;
                Temp_instant_2m:long_name = "dry bulb temperature" ;
                Temp_instant_2m:valid_min = -80s ;
                Temp_instant_2m:valid_max = 130s ;
                Temp_instant_2m:standard_name = "air_temperature" ;
                Temp_instant_2m:units = "degF" ;
                Temp_instant_2m:vertical_coord = "elev0" ;
                Temp_instant_2m:PROV__hadPrimarySource = "NDBC" ;
                Temp_instant_2m:coordinates = "phenomenonTime latitude longitude" ;
                Temp_instant_2m:ancillary_variables = "elev0 phenomenonTime ProcMarine MarineQC " ;
                Temp_instant_2m:missing_value = 9999s ;
                Temp_instant_2m:PROV__wasInformedBy = "( )" ;
                Temp_instant_2m:SOSA__usedProcedure = "( ProcMarine MarineQC )" ;
  // global attributes:
                :institution = "NOAA/National Weather Service" ;
                :Conventions = "CF-1.7 CAMPS-1.2" ;
                :version = "CAMPS-1.2" ;
                :history = "" ;
                :references = "" ;
                :organization = "NOAA/MDL" ;
                :url = "http://www.nws.noaa.gov/mdl/, https://sats.nws.noaa.gov/~camps/" ;
                :primary_variables = "Temp_instant_2m longitude latitude stations station_type" ;
  group: prefix_list {
    // group attributes:
                :PROV__ = "http://www.w3.org/ns/prov/#" ;
                :StatPP__ = "http://codes.nws.noaa.gov/StatPP/" ;
                :SOSA__ = "http://www.w3.org/ns/sosa/" ;
    } // group prefix_list
  }

Sample grib2_to_nc_driver output
==================================

This example is CDL output from grib2_to_nc_driver, for 2 meter temperature.  
Primary variables from this driver script will include lead_times in the dimensions, unlike the other 
driver scripts which process model data.  This makes encoding time for grib2_to_nc_driver output look 
slightly different from all the other driver scripts.

::

  netcdf camps_grib2_output {
  dimensions:
        level = 1 ;
        lead_times = 33 ;
        phenomenonTime = 10 ;
        y = 169 ;
        x = 297 ;
        nv = 2 ;
  variables:
        int64 elev0(level) ;
                elev0:long_name = "height above surface" ;
                elev0:units = "m" ;
                elev0:standard_name = "height" ;
                elev0:positive = "up" ;
                elev0:axis = "Z" ;
        int64 phenomenonTimes(lead_times, phenomenonTime) ;
                phenomenonTimes:_FillValue = 9999LL ;
                phenomenonTimes:calendar = "gregorian" ;
                phenomenonTimes:units = "seconds since 1970-01-01 00:00:00.0" ;
                phenomenonTimes:standard_name = "time" ;
                phenomenonTimes:PROV__specializationOf = "( SOSA__phenomenonTime )" ;
        int64 FcstRefTime(phenomenonTime) ;
                FcstRefTime:_FillValue = 9999LL ;
                FcstRefTime:calendar = "gregorian" ;
                FcstRefTime:units = "seconds since 1970-01-01 00:00:00.0" ;
                FcstRefTime:standard_name = "forecast_reference_time" ;
                FcstRefTime:PROV__specializationOf = "( StatPP__Data/Time/FcstRefTime )" ;
        int64 lead_times(lead_times) ;
                lead_times:_FillValue = 9999LL ;
                lead_times:units = "seconds" ;
                lead_times:standard_name = "forecast_period" ;
                lead_times:PROV__specializationOf = "( StatPP__Data/Time/LeadTime )" ;
                lead_times:firstLeadTime = "P0H" ;
                lead_times:PeriodicTime = "P3H" ;
                lead_times:lastLeadTime = "P96H" ;
        int64 FilterGRIB2 ;
                FilterGRIB2:PROV__activity = "StatPP__Methods/Ingest/FilterGRIB2" ;
                FilterGRIB2:PROV__used = "StatPP__Data/Source/GFS13" ;
                FilterGRIB2:long_name = "Filter GRIB2-encoded forecasts" ;
                FilterGRIB2:standard_name = "source" ;
        int64 ResampleGRIB2 ;
                ResampleGRIB2:PROV__activity = "StatPP__Methods/Ingest/ResampleGRIB2" ;
                ResampleGRIB2:PROV__wasInformedBy = "FilterGRIB2" ;
                ResampleGRIB2:long_name = "Resampling of GRIB2 data onto a new grid" ;
                ResampleGRIB2:standard_name = "source" ;
        float Temp_instant_2m_00Z(phenomenonTime, lead_times, y, x) ;
                Temp_instant_2m_00Z:_FillValue = 9999.f ;
                Temp_instant_2m_00Z:SOSA__observedProperty = "StatPP__Data/Met/Temp/Temp" ;
                Temp_instant_2m_00Z:long_name = "temperature instant" ;
                Temp_instant_2m_00Z:standard_name = "air_temperature" ;
                Temp_instant_2m_00Z:units = "K" ;
                Temp_instant_2m_00Z:PROV__hadPrimarySource = "GFS" ;
                Temp_instant_2m_00Z:FcstTime_hour = 0LL ;
                Temp_instant_2m_00Z:grid_mapping = "polar_stereographic_grid" ;
                Temp_instant_2m_00Z:vertical_coord = "elev1" ;
                Temp_instant_2m_00Z:coordinates = "phenomenonTimes latitude longitude" ;
                Temp_instant_2m_00Z:ancillary_variables = "elev1 phenomenonTimes FcstRefTime lead_times FilterGRIB2 ResampleGRIB2 " ;
                Temp_instant_2m_00Z:missing_value = 9999.f ;
                Temp_instant_2m_00Z:PROV__wasInformedBy = "( FilterGRIB2 ResampleGRIB2 )" ;
                Temp_instant_2m_00Z:SOSA__usedProcedure = "( )" ;
        double polar_stereographic_grid ;
                polar_stereographic_grid:_FillValue = 9999. ;
                polar_stereographic_grid:grid_mapping_name = "polar_stereographic" ;
                polar_stereographic_grid:straight_vertical_longitude_from_pole = 255. ;
                polar_stereographic_grid:latitude_of_projection_origin = 90. ;
                polar_stereographic_grid:standard_parallel = 60. ;
                polar_stereographic_grid:scale_factor_at_projection_origin = 1LL ;
                polar_stereographic_grid:PROJ_string = "+a=6371229 +b=6371229 +proj=stere +lat_ts=60.0 +lat_0=90.0 +lon_0=255.0 +x_0=8001120.943743923 +y_0=8001120.943743925" ;
                polar_stereographic_grid:coordinates = "" ;
  // global attributes:
                :institution = "NOAA/National Weather Service" ;
                :Conventions = "CF-1.7 CAMPS-1.2" ;
                :version = "CAMPS-1.2" ;
                :history = "" ;
                :references = "" ;
                :organization = "NOAA/MDL" ;
                :url = "http://www.nws.noaa.gov/mdl/, https://sats.nws.noaa.gov/~camps/" ;
                :primary_variables = "Temp_instant_2m_00Z latitude longitude x y polar_stereographic_grid"" ;
  group: prefix_list {
    // group attributes:
                :PROV__ = "http://www.w3.org/ns/prov/#" ;
                :StatPP__ = "http://codes.nws.noaa.gov/StatPP/" ;
                :SOSA__ = "http://www.w3.org/ns/sosa/" ;
    } // group prefix_list
  }

Sample mospred_driver output (predictors)
==========================================

Mospred_driver will have two potential output files.  This example is the CDL output from processing predictors only.  
Notice that lead_times is no longer a dimension of our primary variable, 2 meter temperature.  
Instead, primary variables will be broken into separate variables based on procedures, level, AND lead_time.

::

  netcdf camps_predictor_output {
  dimensions:
        phenomenonTime = 10 ;
        stations = 20 ;
        level = 1 ;
        lead_times = 1 ;
  variables:
        int64 elev0(level) ;
                elev0:long_name = "height above surface" ;
                elev0:units = "m" ;
                elev0:standard_name = "height" ;
                elev0:positive = "up" ;
                elev0:axis = "Z" ;
        int64 phenomenonTimes(phenomenonTime) ;
                phenomenonTimes:_FillValue = 9999LL ;
                phenomenonTimes:calendar = "gregorian" ;
                phenomenonTimes:units = "seconds since 1970-01-01 00:00:00.0" ;
                phenomenonTimes:standard_name = "time" ;
                phenomenonTimes:PROV__specializationOf = "( SOSA__phenomenonTime )" ;
        int64 FcstRefTime(phenomenonTime) ;
                FcstRefTime:_FillValue = 9999LL ;
                FcstRefTime:calendar = "gregorian" ;
                FcstRefTime:units = "seconds since 1970-01-01 00:00:00.0" ;
                FcstRefTime:standard_name = "forecast_reference_time" ;
                FcstRefTime:PROV__specializationOf = "( StatPP__Data/Time/FcstRefTime )" ;
        int64 lead_times(lead_times) ;
                lead_times:_FillValue = 9999LL ;
                lead_times:units = "seconds" ;
                lead_times:standard_name = "forecast_period" ;
                lead_times:PROV__specializationOf = "( StatPP__Data/Time/LeadTime )" ;
                lead_times:firstLeadTime = "P0H" ;
                lead_times:PeriodicTime = "P3H" ;
                lead_times:lastLeadTime = "P96H" ;
        int64 FilterGRIB2 ;
                FilterGRIB2:PROV__activity = "StatPP__Methods/Ingest/FilterGRIB2" ;
                FilterGRIB2:PROV__used = "StatPP__Data/Source/GFS13" ;
                FilterGRIB2:long_name = "Filter GRIB2-encoded forecasts" ;
                FilterGRIB2:standard_name = "source" ;
        int64 ResampleGRIB2 ;
                ResampleGRIB2:PROV__activity = "StatPP__Methods/Ingest/ResampleGRIB2" ;
                ResampleGRIB2:PROV__wasInformedBy = "FilterGRIB2" ;
                ResampleGRIB2:long_name = "Resampling of GRIB2 data onto a new grid" ;
                ResampleGRIB2:standard_name = "source" ;
        int64 LinSmooth ;
                LinSmooth:PROV__activity = "StatPP__Methods/Arith/LinSmooth" ;
                LinSmooth:long_name = "Linear Smoothing" ;
        int64 BiLinInterp ;
                BiLinInterp:PROV__activity = "StatPP__Methods/Geosp/BiLinInterp" ;
                BiLinInterp:long_name = "Bilinear Interpolation" ;
        byte station_type(stations) ;
                station_type:_FillValue = 15b ;
                station_type:standard_name = "platform_id" ;
                station_type:long_name = "station type" ;
                station_type:PROV__hadPrimarySource = "METAR" ;
                station_type:coordinates = "latitude longitude" ;
                station_type:missing_value = 9999LL ;
        string stations(stations) ;
                string stations:_FillValue = "_" ;
                stations:long_name = "NDBC station identifiers" ;
                stations:standard_name = "platform_id" ;
                stations:comment = "NDBC stations consist of buoy, C-MAN, and platform drilling sites" ;
                stations:PROV__hadPrimarySource = "NDBC" ;
                stations:coordinates = "latitude longitude" ;
                stations:missing_value = 9999LL ;
        double Temp_instant_2m_00Z_12hr_LinSmooth25_BiLinInterp(phenomenonTime, stations) ;
                Temp_instant_2m_00Z_12hr_LinSmooth25_BiLinInterp:_FillValue = 9999. ;
                Temp_instant_2m_00Z_12hr_LinSmooth25_BiLinInterp:SOSA__observedProperty = "StatPP__Data/Met/Temp/Temp" ;
                Temp_instant_2m_00Z_12hr_LinSmooth25_BiLinInterp:long_name = "temperature instant" ;
                Temp_instant_2m_00Z_12hr_LinSmooth25_BiLinInterp:standard_name = "air_temperature" ;
                Temp_instant_2m_00Z_12hr_LinSmooth25_BiLinInterp:units = "K" ;
                Temp_instant_2m_00Z_12hr_LinSmooth25_BiLinInterp:PROV__hadPrimarySource = "GFS" ;
                Temp_instant_2m_00Z_12hr_LinSmooth25_BiLinInterp:FcstTime_hour = 0LL ;
                Temp_instant_2m_00Z_12hr_LinSmooth25_BiLinInterp:vertical_coord = "elev0" ;
                Temp_instant_2m_00Z_12hr_LinSmooth25_BiLinInterp:coordinates = "phenomenonTimes latitude longitude" ;
                Temp_instant_2m_00Z_12hr_LinSmooth25_BiLinInterp:ancillary_variables = "elev0 phenomenonTimes FcstRefTime lead_times FilterGRIB2 ResampleGRIB2 LinSmooth BiLinInterp " ;
                Temp_instant_2m_00Z_12hr_LinSmooth25_BiLinInterp:missing_value = 9999. ;
                Temp_instant_2m_00Z_12hr_LinSmooth25_BiLinInterp:PROV__wasInformedBy = "( FilterGRIB2 ResampleGRIB2 )" ;
                Temp_instant_2m_00Z_12hr_LinSmooth25_BiLinInterp:smooth = "25" ;
                Temp_instant_2m_00Z_12hr_LinSmooth25_BiLinInterp:leadtime = 12LL ;
                Temp_instant_2m_00Z_12hr_LinSmooth25_BiLinInterp:SOSA__usedProcedure = "( LinSmooth BiLinInterp )" ;
  // global attributes:
                :institution = "NOAA/National Weather Service" ;
                :Conventions = "CF-1.7 CAMPS-1.2" ;
                :version = "CAMPS-1.2" ;
                :history = "" ;
                :references = "" ;
                :organization = "NOAA/MDL" ;
                :url = "http://www.nws.noaa.gov/mdl/, https://sats.nws.noaa.gov/~camps/" ;
                :primary_variables = "Temp_instant_2m_00Z_12hr_LinSmooth25_BiLinInterp longitude latitude stations station_type" ;
  group: prefix_list {
    // group attributes:
                :PROV__ = "http://www.w3.org/ns/prov/#" ;
                :StatPP__ = "http://codes.nws.noaa.gov/StatPP/" ;
                :SOSA__ = "http://www.w3.org/ns/sosa/" ;
    } // group prefix_list
  }


Sample mospred_driver output (predictands)
============================================

Mospred_driver will have two potential output files.  This example is the CDL output from processing predictands only.  
The main difference between mospred predictor output and predictand output is how time is encoded.  For predictands, 
there is no lead_time or forecast_reference_time.  Instead, there is only a phenomenonTime.  Predictands are still 
split out by procedure and level.

::
  
  netcdf camps_predictand_output {
  dimensions:
        phenomenonTime = 10 ;
        stations = 20 ;
        level = 1 ;
  variables:
        int64 elev0(level) ;
                elev0:long_name = "height above surface" ;
                elev0:units = "m" ;
                elev0:standard_name = "height" ;
                elev0:positive = "up" ;
                elev0:axis = "Z" ;
        int64 phenomenonTime(phenomenonTime) ;
                phenomenonTime:_FillValue = 9999LL ;
                phenomenonTime:calendar = "gregorian" ;
                phenomenonTime:units = "seconds since 1970-01-01 00:00:00.0" ;
                phenomenonTime:standard_name = "time" ;
                phenomenonTime:PROV__specializationOf = "( SOSA__phenomenonTime )" ;
        int64 DecodeBUFR ;
                DecodeBUFR:PROV__activity = "StatPP__Methods/Ingest/DecodeBUFR" ;
                DecodeBUFR:PROV__used = "StatPP__Data/Source/NCEPSfcObsMETAR" ;
                DecodeBUFR:long_name = "Ingest BUFR encoded METAR observations from NCEP repository" ;
                DecodeBUFR:standard_name = "source" ;
        int64 METARQC ;
                METARQC:PROV__activity = "StatPP__Methods/QC/METARQC" ;
                METARQC:PROV__wasInformedBy = "DecodeBUFR" ;
                METARQC:long_name = "Apply MDL METAR Quality Control procedure" ;
                METARQC:standard_name = "source" ;
        double Temp_instant_2m(phenomenonTime, stations) ;
                Temp_instant_2m:_FillValue = 9999. ;
                Temp_instant_2m:SOSA__observedProperty = "StatPP__Data/Met/Temp/Temp" ;
                Temp_instant_2m:long_name = "dry bulb temperature" ;
                Temp_instant_2m:valid_min = 210.927777777778 ;
                Temp_instant_2m:valid_max = 327.594444444444 ;
                Temp_instant_2m:standard_name = "air_temperature" ;
                Temp_instant_2m:units = "K" ;
                Temp_instant_2m:vertical_coord = "elev0" ;
                Temp_instant_2m:coordinates = "phenomenonTime latitude longitude" ;
                Temp_instant_2m:ancillary_variables = "elev0 phenomenonTime DecodeBUFR METARQC " ;
                Temp_instant_2m:missing_value = 9999. ;
                Temp_instant_2m:PROV__wasInformedBy = "( DecodeBUFR METARQC )" ;
                Temp_instant_2m:PROV__hadPrimarySource = "METAR NDBC" ;
                Temp_instant_2m:SOSA__usedProcedure = "( )" ;
        byte station_type(stations) ;
                station_type:_FillValue = 15b ;
                station_type:standard_name = "platform_id" ;
                station_type:long_name = "station type" ;
                station_type:PROV__hadPrimarySource = "METAR" ;
                station_type:coordinates = "latitude longitude" ;
                station_type:missing_value = 9999LL ;
        string stations(stations) ;
                string stations:_FillValue = "_" ;
                stations:long_name = "ICAO METAR call letters" ;
                stations:standard_name = "platform_id" ;
                stations:comment = " Only currently archives reports from stations only if the first letter of the ICAO ID is \'K\', \'P\', \'M\', \'C\', or \'T\'. " ;
                stations:coordinates = "latitude longitude" ;
                stations:missing_value = 9999LL ;
        double latitude(stations) ;
                latitude:_FillValue = 9999. ;
                latitude:long_name = "latitude" ;
                latitude:units = "degrees_north" ;
                latitude:valid_min = -90. ;
                latitude:valid_max = 90. ;
                latitude:standard_name = "latitude" ;
                latitude:coordinates = "latitude longitude" ;
                latitude:missing_value = 9999. ;
        double longitude(stations) ;
                longitude:_FillValue = 9999. ;
                longitude:long_name = "longitude" ;
                longitude:units = "degrees_west" ;
                longitude:valid_min = -180. ;
                longitude:valid_max = 180. ;
                longitude:standard_name = "longitude" ;
                longitude:coordinates = "latitude longitude" ;
                longitude:missing_value = 9999. ;

  // global attributes:
                :institution = "NOAA/National Weather Service" ;
                :Conventions = "CF-1.7 CAMPS-1.2" ;
                :version = "CAMPS-1.2" ;
                :history = "" ;
                :references = "" ;
                :organization = "NOAA/MDL" ;
                :url = "http://www.nws.noaa.gov/mdl/, https://sats.nws.noaa.gov/~camps/" ;
                :primary_variables = "Temp_instant_2m stations station_type latitude longitude" ;

  group: prefix_list {

    // group attributes:
                :PROV__ = "http://www.w3.org/ns/prov/#" ;
                :StatPP__ = "http://codes.nws.noaa.gov/StatPP/" ;
                :SOSA__ = "http://www.w3.org/ns/sosa/" ;
    } // group prefix_list
  }

Sample equations_driver output
================================

Regression coefficients, and the *Equation_Constant*, are saved as a single variable (*MOS_Equations*), 
dimensioned by the number of stations, the number of coefficients (including the *Equation_Constant*) and the number of Predictands. 

The ancillary_variables attribute, for the *MOS_equations* variable, should contain a reference to the non-data-bearing variables 
*MOS_Predictor_Coeffs* and *Equation_Constant*. These variables contain the appropriate metadata description to identify the type of 
information a *MOS_equations* variable contains.

The auxiliary coordinate variable attribute (coordinates), for a *MOS_equations* variable, references an *Equations_List* and 
*Predictand_List* variable. These variables provide ordered lists that apply to the dimensions of the *MOS_equations* variable.

*Equations_List* corresponds to the dimension *max_eq_terms*, which stores an ordered list of the predictors that provide input 
to the set of equations, along with the equation constant, as a character array. The ordered input list references the 
non-data-bearing predictor variables that appear elsewhere in the file. The attributes assigned to each of those non-data-bearing 
variables, provide all the metadata needed to access and use those predictors contained in the input file to equations_driver.

*Predictand_List* provides an ordered character output array, which plays a complementary role by identifying the predictands 
that are forecast by the equations.

In addition to the MOS_equations variable, ordered input and output lists, and non-data-bearing predictor and predictand variables, 
there are a number of variables that contain diagnostic information about the MOS development process. Each of these variables is 
stored individually, as primary variables, within an equations output file. 

::
 
  netcdf camps_equations_output {
  dimensions:
        stations = 20 ;
        number_of_predictands = 1 ;
        max_eq_terms = 4 ;
        num_char_predictors = 51 ;
        num_char_predictands = 20 ;
        level = 1 ;
        phenomenonTime = 10 ;
        lead_times = 1 ;
  variables:
        char Equations_List(max_eq_terms, num_char_predictors) ;
                Equations_List:PROV__entity = "StatPP__Methods/Stat/OrdrdInpt" ;
                Equations_List:long_name = "Ordered List of Equation Terms" ;
        int64 PolyLinReg ;
                PolyLinReg:PROV__Activity = "StatPP__Methods/Stat/PolyLinReg" ;
                PolyLinReg:long_name = "Polynomial Linear Regression" ;
                PolyLinReg:feature_of_interest = "no" ;
        float Reduction_of_Variance(stations, number_of_predictands) ;
                Reduction_of_Variance:PROV__entity = "StatPP__Methods/Stat/MOS/OutptParams/MOSRedOfVar" ;
                Reduction_of_Variance:standard_name = "source" ;
                Reduction_of_Variance:long_name = "MOS Reduction of Variance" ;
                Reduction_of_Variance:coordinates = "station Predictand_List" ;
                Reduction_of_Variance:SOSA__usedProcedure = "( PolyLinReg )" ;
                Reduction_of_Variance:units = 1LL ;
        float Multiple_Correlation_Coefficient(stations, number_of_predictands) ;
                Multiple_Correlation_Coefficient:PROV__entity = "StatPP__Methods/Stat/MOS/OutptParams/MOSMultiCorCoef" ;
                Multiple_Correlation_Coefficient:standard_name = "source" ;
                Multiple_Correlation_Coefficient:long_name = "MOS Multiple Correlation Coefficient" ;
                Multiple_Correlation_Coefficient:coordinates = "station Predictand_List" ;
                Multiple_Correlation_Coefficient:SOSA__usedProcedure = "( PolyLinReg )" ;
                Multiple_Correlation_Coefficient:units = 1LL ;
        float Predictand_Average(stations, number_of_predictands) ;
                Predictand_Average:PROV__entity = "StatPP__Methods/MOS/Arith/Mean" ;
                Predictand_Average:standard_name = "source" ;
                Predictand_Average:long_name = "Predictand Average" ;
                Predictand_Average:coordinates = "station Predictand_List" ;
                Predictand_Average:SOSA__usedProcedure = "( Mean )" ;
                Predictand_Average:units = 1LL ;
        float MOS_Equations(stations, max_eq_terms, number_of_predictands) ;
                MOS_Equations:PROV__entity = "StatPP__Methods/Stat/MOS/MOSEqn" ;
                MOS_Equations:standard_name = "source" ;
                MOS_Equations:long_name = "MOS Equation Coefficients and Constants" ;
                MOS_Equations:coordinates = "station Equations_List Predictand_List" ;
                MOS_Equations:SOSA__usedProcedure = "( PolyLinReg )" ;
                MOS_Equations:ancillary_variables = "( MOS_Predictor_Coeffs Equation_Constant )" ;
                MOS_Equations:units = 1LL ;
  // global attributes:
                :PROV__entity = "StatPP__Data/Source/MOSEqnFile" ;
                :PROV__wasGeneratedBy = "StatPP__Methods/Stat/MOSDev" ;
                :primary_variables = "MOS_Equations Standard_Error_Estimate Reduction_of_Variance Multiple_Correlation_Coefficient Predictand_Average" ;
                :season = "warm" ;
                :StatPPTime__SeasBeginDay = "0401" ;
                :StatPPTime__SeasEndDay = "0410" ;
                :StatPPTime__SeasDayFmt = "StatPP__Data/Time/SeasDayFmt/MMDD" ;
                :StatPPTime__FcstCyc = "00" ;
                :StatPPTime__FcstCycFmt = "StatPP__Data/Time/FcstCycFmt/HH" ;
                :StatPPSystem__Status = "StatPP__Methods/System/Status/Dev" ;
                :institution = "NOAA/National Weather Service" ;
                :Conventions = "CF-1.7 CAMPS-1.2" ;
                :version = "CAMPS-1.2" ;
                :PROV__wasAttributedTo = "StatPP__Data/Source/MDL" ;
                :url = "http://www.nws.noaa.gov/mdl/, https://sats.nws.noaa.gov/~camps/" ;
                :PROV__generatedAtTime = "2021-02-25T19:00:00" ;

  group: prefix_list {

    // group attributes:
                :PROV__ = "http://www.w3.org/ns/prov/#" ;
                :StatPP__ = "http://codes.nws.noaa.gov/StatPP/" ;
                :StatPPTime__ = "http://codes.nws.noaa.gov/StatPP/Data/Time/" ;
                :StatPPSystem__ = "http://codes.nws.noaa.gov/StatPP/Methods/System/" ;
                :SOSA__ = "http://www.w3.org/ns/sosa/" ;
    } // group prefix_list
  }

Sample forecast_driver output
===============================

The CDL output for forecast_driver should look very similar to that of mospred_driver, for predictors.  
The main exception being the “MOS” identifier prepended to the start of every variable.  
There are also consistency check variables included in forecast_driver output, when appropriate.  

::

  netcdf camps_forecast_output {
  dimensions:
        phenomenonTime = 10 ;
        stations = 20 ;
        level = 1 ;
        lead_times = 1 ;
  variables:
        int64 elev0(level) ;
                elev0:long_name = "height above surface" ;
                elev0:units = "m" ;
                elev0:standard_name = "height" ;
                elev0:positive = "up" ;
                elev0:axis = "Z" ;
        int64 phenomenonTime(phenomenonTime) ;
                phenomenonTime:_FillValue = 9999LL ;
                phenomenonTime:calendar = "gregorian" ;
                phenomenonTime:units = "seconds since 1970-01-01 00:00:00.0" ;
                phenomenonTime:standard_name = "time" ;
                phenomenonTime:PROV__specializationOf = "( SOSA__phenomenonTime )" ;
        int64 FcstRefTime(phenomenonTime) ;
                FcstRefTime:_FillValue = 9999LL ;
                FcstRefTime:calendar = "gregorian" ;
                FcstRefTime:units = "seconds since 1970-01-01 00:00:00.0" ;
                FcstRefTime:standard_name = "forecast_reference_time" ;
                FcstRefTime:PROV__specializationOf = "( StatPP__Data/Time/FcstRefTime )" ;
        int64 lead_times(lead_times) ;
                lead_times:_FillValue = 9999LL ;
                lead_times:units = "seconds" ;
                lead_times:standard_name = "forecast_period" ;
                lead_times:PROV__specializationOf = "( StatPP__Data/Time/LeadTime )" ;
        int64 MOS_Method ;
                MOS_Method:PROV__activity = "StatPP__Methods/Stat/MOS" ;
                MOS_Method:long_name = "Model Output statistical method: Multiple Linear Regression " ;
        double MOS_Temp_instant_2m_00Z_12hr(phenomenonTime, stations) ;
                MOS_Temp_instant_2m_00Z_12hr:_FillValue = 9999. ;
                MOS_Temp_instant_2m_00Z_12hr:SOSA__observedProperty = "StatPP__Data/Met/Temp/Temp" ;
                MOS_Temp_instant_2m_00Z_12hr:long_name = "dry bulb temperature" ;
                MOS_Temp_instant_2m_00Z_12hr:valid_min = 210.927777777778 ;
                MOS_Temp_instant_2m_00Z_12hr:valid_max = 327.594444444444 ;
                MOS_Temp_instant_2m_00Z_12hr:standard_name = "air_temperature" ;
                MOS_Temp_instant_2m_00Z_12hr:units = "K" ;
                MOS_Temp_instant_2m_00Z_12hr:vertical_coord = "elev0" ;
                MOS_Temp_instant_2m_00Z_12hr:coordinates = "phenomenonTime latitude longitude" ;
                MOS_Temp_instant_2m_00Z_12hr:ancillary_variables = "elev0 phenomenonTime FcstRefTime lead_times MOS_Method " ;
                MOS_Temp_instant_2m_00Z_12hr:missing_value = 9999. ;
                MOS_Temp_instant_2m_00Z_12hr:PROV__wasInformedBy = "( )" ;
                MOS_Temp_instant_2m_00Z_12hr:PROV__hadPrimarySource = "GFS13" ;
                MOS_Temp_instant_2m_00Z_12hr:leadtime = 12LL ;
                MOS_Temp_instant_2m_00Z_12hr:FcstTime_hour = 0LL ;
                MOS_Temp_instant_2m_00Z_12hr:SOSA__usedProcedure = "( MOS_Method )" ;
        string stations(stations) ;
                string stations:_FillValue = "_" ;
                stations:long_name = "ICAO METAR call letters" ;
                stations:standard_name = "platform_id" ;
                stations:comment = " Only currently archives reports from stations only if the first letter of the ICAO ID is \'K\', \'P\', \'M\', \'C\', or \'T\'. " ;
                stations:coordinates = "latitude longitude" ;
                stations:missing_value = 9999LL ;
        double latitude(stations) ;
                latitude:_FillValue = 9999. ;
                latitude:long_name = "latitude" ;
                latitude:units = "degrees_north" ;
                latitude:valid_min = -90. ;
                latitude:valid_max = 90. ;
                latitude:standard_name = "latitude" ;
                latitude:coordinates = "latitude longitude" ;
                latitude:missing_value = 9999. ;
        double longitude(stations) ;
                longitude:_FillValue = 9999. ;
                longitude:long_name = "longitude" ;
                longitude:units = "degrees_west" ;
                longitude:valid_min = -180. ;
                longitude:valid_max = 180. ;
                longitude:standard_name = "longitude" ;
                longitude:coordinates = "latitude longitude" ;
                longitude:missing_value = 9999. ;
  // global attributes:
                :institution = "NOAA/National Weather Service" ;
                :Conventions = "CF-1.7 CAMPS-1.2" ;
                :version = "CAMPS-1.2" ;
                :history = "" ;
                :references = "" ;
                :organization = "NOAA/MDL" ;
                :url = "http://www.nws.noaa.gov/mdl/, https://sats.nws.noaa.gov/~camps/" ;
                :file_id = "0e4181eb-9683-4e17-bcd1-a0096fca9b1f" ;
                :primary_variables = "MOS_Temp_instant_2m_00Z_12hr stations latitude longitude" ;
  group: prefix_list {

    // group attributes:
                :PROV__ = "http://www.w3.org/ns/prov/#" ;
                :StatPP__ = "http://codes.nws.noaa.gov/StatPP/" ;
                :SOSA__ = "http://www.w3.org/ns/sosa/" ;
    } // group prefix_list
  }



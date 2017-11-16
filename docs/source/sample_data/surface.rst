Surface Observations
====================

.. only:: builder_html

   This section describes sample surface observation output that can be :download:`downloaded here <./reduced_hre201302.nc>`.
   If you are reading this in a PDF document, then you will need to access a web version to download the sample files.

This sample file contains station data from METAR-encoded hourly surface observations for a set of 2000 stations taken during the 28 days of February 2013.

.. note::
   NOTE:  This file was modified from the original to make it smaller and easier to review.
   The original file contained 3095 unique stations.
   Two thousand of those stations were selected at random to constitute this file.

The observations were processed through MDL's quality control (QC) routines.
Notably, the observation time information was removed in that process.
Thus, all time data in this file are at the "top of the hour."
E.g., a METAR whose time was encoded as 1953 (19:53:00 UTC) is stored in this file with the time 20:00:00 UTC.
This is useful for a number of applications in statistical post-processing, but problematic in a number of other ways.

Here's a CDL fragment for an array of 2-m temperature values.
(Output is captued from the application Panoply.  All atrributes that follow the variable declaration are associated with that variable.)

::

| short METAR_Temp_instant_2_(number_of_stations=2000, default_time_coordinate_size=672, level=1);
|   :_FillValue = 9999S; // short
|   :ancillary_variables = "OM_phenomenonTimeInstant OM_resultTime OM_validTime MetarObProcStep1 MetarObProcStep2 ";
|   :standard_name = "air_temperature";
|   :coordinates = "elev0";
|   :LE_Source = "METAR";
|   :long_name = "dry bulb temperature";
|   :valid_min = -80S; // short
|   :units = "degF";
|   :valid_max = 130S; // short
|   :OM_observedProperty = "https://codes.nws.noaa.gov/StatPP/Data/Met/Temp/Temp";
|   :OM_procedure = "( MetarObProcStep1,MetarObProcStep2 )";
|   :_ChunkSizes = 2000, 672, 1; // int

There are three dimensions.
The first, number_of_stations, of course, indexes the various stations.
The character variable stations contains the ICAO call letters that identify each.
The second dimension, default_time_coordinate, simply counts through the 672 UTC hours in the month of February 2013.
The last dimension is a vertical coordinate that satisfies the requirements of the CF Conventions.

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
It simply indicates 2 meters above the Earth's surface.

The next attribute identifies a number of ancillary variables, most of which are associated with time.
Each of these variables are explained in some detail below.

The attribute OM_observedProperty takes on a value that resolves to a code registry entry for temperature.

The attribute OM_procedure points to a two step process.
The data in this file were first decoded from METAR format.
Then, they were quality controlled with routines developed by MDL.
The attribute OM_procedure takes on a character string value that names one or more value-less integers.
Those integers, in turn, convey metadata in their attributes about each procedureal step.

.. note::
   CDL Fragments and explanation for OM_procedure steps are needed here.

There are three time-related variables associated with METAR_Temp_instant_2_.
They are OM_phenomenonTimeInstant, OM_resultTime, and OM_validTime.
Here are the CDL fragments that declare each of them:

::

| long OM_phenomenonTimeInstant(default_time_coordinate_size=672);
|   :_FillValue = -9999L; // long
|   :calendar = "gregorian";
|   :units = "seconds since 1970-01-01 00:00:00.0";
|   :standard_name = "time";
|   :wisps_role = "OM_phenomenonTime";
|   :_ChunkSizes = 672; // int
| 
| long OM_resultTime(default_time_coordinate_size=672);
|   :_FillValue = -9999L; // long
|   :calendar = "gregorian";
|   :units = "seconds since 1970-01-01 00:00:00.0";
|   :standard_name = "time";
|   :wisps_role = "OM_resultTime";
|   :_ChunkSizes = 672; // int
| 
| long OM_validTime(begin_end_size=2, default_time_coordinate_size=672);
|   :_FillValue = -9999L; // long
|   :calendar = "gregorian";
|   :units = "seconds since 1970-01-01 00:00:00.0";
|   :standard_name = "time";
|   :wisps_role = "OM_validTime";
|   :_ChunkSizes = 2, 672; // int

The declarations we find here are somewhat different than those in the other data types.

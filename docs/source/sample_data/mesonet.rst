Mesonet Observations
====================


.. only:: builder_html

   This section describes sample surface observation output that can be :download:`downloaded here <./reduced_mesohre201207.nc>`.
   If you are reading this in a PDF document, then you will need to access a web version to download the sample files.

This sample file contains mesonet station data from the NWS National Centers for Environmental Prediction (NCEP) Meteorological Assimilation Data Ingest System (MADIS; https://madis.ncep.noaa.gov).
The original MADIS file contained surface observation data from more than 22,000 stations taken during July 2012.

.. note::
   NOTE:  This file was modified from the original to make it smaller and easier to review.
   The original file contained more than 22,000 unique stations.
   Three thousand of those stations were chosen at random to create this file.
   This reduced the size substantially and maintained the diverse collection of station identifiers and metadata.

The observations were processed through MDL's quality control (QC) routines.
Notably, the observation time information was altered in that process.
Specifically, all time data in this file are at the "top of the hour."
E.g., an observation whose time was encoded as 1953 (19:53:00 UTC) is stored in this file with the time 20:00:00 UTC.
This is useful for a number of applications in statistical post-processing, but problematic in a number of other ways.

Here's a CDL fragment for an array of 2-m temperature values.
(Output is captued from the application Panoply.  All atrributes that follow the variable declaration are associated with that variable.)

::

| short Temp_instant_2_(number_of_stations=2000, default_time_coordinate_size=744, level=1);
|   :_FillValue = 9999S; // short
|   :OM__observedProperty = "StatPP__Data/Met/Temp/Temp";
|   :PROV__Used = "MESONET";
|   :ancillary_variables = "OM__phenomenonTimeInstant OM__resultTime ValidTime MesoObProcStep1 MesoObProcStep2 MesoObProcStep3 ";
|   :standard_name = "air_temperature";
|   :coordinates = "elev0, station";
|   :long_name = "dry bulb temperature";
|   :valid_min = -80.0; // double
|   :units = "degF";
|   :valid_max = 130.0; // double
|   :SOSA__usedProcedure = "( MesoObProcStep1 MesoObProcStep2 MesoObProcStep3 )";
|   :_ChunkSizes = 2000U, 744U, 1U; // uint

There are three dimensions.
The first, number_of_stations, of course, indexes the various stations.
The character variable stations contains the ICAO call letters that identify each.
The second dimension, default_time_coordinate, simply counts through the 744 UTC hours in the month of July 2012.
The last dimension is a vertical coordinate that satisfies the requirements of the CF Conventions.
It simply indicates 2 meters above the Earth's surface.

One of the first attributes identifies a number of ancillary variables, most of which are associated with time.
Each of these variables are explained in some detail below.

The attribute OM__observedProperty takes on a value that resolves to a code registry entry for temperature.

The attribute SOSA__usedProcedure points to a three step process.
The data in this file were first decoded from a tabular text format.
(They were likely received by MADIS in a wide variety of formats.)
Then, they were quality controlled with routines developed by MDL.
Finally, they were given a geospatial quality control developed by MDL.
This final step identifies stations with identical MADIS station identifiers that are considered too far apart for our statistical post-processing needs.
These stations are given distinct station identifiers within MDL's system.

The attribute SOSA__usedProcedure takes on a character string value that names one or more value-less integers.
Those integers, in turn, convey metadata in their attributes about each procedureal step.
Here is the CDL that describes the process step integers:

::

| long MesoObProcStep1;
|   :PROV__Activity = "StatPP__Methods/Ingest/DecodeTabularText";
|   :long_name = "Ingest tabular text-encoded mesonet data from MADIS";
|   :PROV__Used = "StatPP__Data/MADISMesonet";
|   :units = 1L; // long
|   :standard_name = "source";
|
| long MesoObProcStep2;
|   :PROV__Activity = "StatPP__Methods/QC/MesoQC";
|   :long_name = "Apply MDL mesonet Quality Control technique";
|   :standard_name = "source";
|   :units = 1L; // long
|
| long MesoObProcStep3;
|   :PROV__Activity = "StatPP__Methods/QC/GeospatialQC";
|   :long_name = "Identify and resolve geospatial inconsistencies";
|   :standard_name = "source";
|   :units = 1L; // long

The attribute strings associated with MesoObProcStep1 document that the data were ingested from mesonet observations in a tabular text format maintained by NCEP's Meteorological Assimilation Data Ingest System (MADIS).
Note that the attribute PROV__Activity shows a tabular text decoding step while the attribute PROV__Used identifies MADISMesonet as the source.
Note that both PROV__Activity and PROV__Used point to entries in the NWS Codes Registry where additional details can be documented.

The attribute strings associated with MesoObProcStep2 document that the data were quality controlled using a procedure developed and maintained by MDL.
The attribute PROV__Activity again points to a codes registry entry.
There is no entry for PROV__Used in this variable.
When PROV__Used is omitted, we presume that the results from the previous process step are the source for the current process step.

The attribute strings associated with MesoObProcStep3 document that the data received a geospatial quality control step developed by MDL.

There are three time-related variables associated with MESONET_Temp_instant_2_.
They are OM__phenomenonTimeInstant, OM__resultTime, and ValidTime.
Here are the CDL fragments that declare each of them:

::

| long OM__phenomenonTimeInstant(default_time_coordinate_size=744);
|   :_FillValue = 9999L; // long
|   :calendar = "gregorian";
|   :units = "seconds since 1970-01-01 00:00:00.0";
|   :standard_name = "time";
|   :PROV__specializationOf = "( OM__phenomenonTime )";
|   :_ChunkSizes = 744U; // uint
|
| long OM__resultTime(default_time_coordinate_size=744);
|   :_FillValue = 9999L; // long
|   :calendar = "gregorian";
|   :units = "seconds since 1970-01-01 00:00:00.0";
|   :standard_name = "time";
|   :PROV__specializationOf = "( OM__resultTime )";
|   :_ChunkSizes = 744U; // uint
|
| long ValidTime(begin_end_size=2, default_time_coordinate_size=744);
|   :_FillValue = 9999L; // long
|   :calendar = "gregorian";
|   :units = "seconds since 1970-01-01 00:00:00.0";
|   :standard_name = "time";
|   :PROV__specializationOf = "( StatPP__concepts/TimeBoundsSyntax/BeginEnd OM2__Data/Time/ValidTime )";
|   :_ChunkSizes = 2U, 744U; // uint

The declarations we find here are quite simlar to those used for METAR-encoded surface observations and marine observations.
OM_phenomenonTimeInstant takes on a value for each hour of the month.
As noted above, the times are set to the top of each hour for all stations and times.
OM__resultTime values are equal to OM__phenomenonTime values.
ValidTime is two-dimensional representing beginning time and ending time.
The beginning times equal the phenomenon times and result times.
(I.e., we don't intend for data consumers to use an observation before it's taken.)
The ending times are set to missing to show that we intend for data consumers to use an observation indefinitely.

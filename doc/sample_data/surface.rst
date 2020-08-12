Surface Observations
====================

.. only:: builder_html

   This section describes sample surface observation output that can be :download:`downloaded here <./reduced_hre201606.nc>`.
   If you are reading this in a PDF document, then you will need to access a web version to download the sample files.

This sample file contains station data from METAR-encoded hourly surface observations for a set of 2000 stations taken during the 30 days of June 2016.

.. note::
   NOTE:  This file was modified from the original to make it smaller and easier to review.
   The original file contained 3095 unique stations.
   Two thousand of those stations were selected at random to constitute this file.

The observations were processed through MDL's quality control (QC) routines.
Notably, the observation time information was altered in that process.
Specifically, all time data in this file are at the "top of the hour."
E.g., a METAR whose time was encoded as 1953 (19:53:00 UTC) is stored in this file with the time 20:00:00 UTC.
This is useful for a number of applications in statistical post-processing, but problematic in a number of other ways.

Here's a CDL fragment for an array of 2-m temperature values.
(Output is captued from the application Panoply.  All atrributes that follow the variable declaration are associated with that variable.)

::

| short Temp_instant_2_(number_of_stations=2000, default_time_coordinate_size=720, level=1);
|   :_FillValue = 9999S; // short
|   :OM__observedProperty = "StatPP__Data/Met/Temp/Temp";
|   :PROV__Used = "StatPP__Data/Source/NCEPSfcObsMETAR";
|   :ancillary_variables = "OM__phenomenonTimeInstant OM__resultTime ValidTime MetarObProcStep1 MetarObProcStep2 ";
|   :standard_name = "air_temperature";
|   :coordinates = "elev0, station";
|   :long_name = "dry bulb temperature";
|   :valid_min = -80S; // short
|   :units = "degF";
|   :valid_max = 130S; // short
|   :SOSA__usedProcedure = "( MetarObProcStep1 MetarObProcStep2 )";
|   :_ChunkSizes = 2000U, 720U, 1U; // uint

There are three dimensions.
The first, number_of_stations, of course, indexes the various stations.
The character variable stations contains the ICAO call letters that identify each.
The second dimension, default_time_coordinate, simply counts through the 720 UTC hours in the month of June 2016.
The last dimension is a vertical coordinate that satisfies the requirements of the CF Conventions.
It simply indicates 2 meters above the Earth's surface.

The next attribute identifies a number of ancillary variables, most of which are associated with time.
Each of these variables are explained in some detail below.

The attribute OM__observedProperty takes on a value that resolves to a code registry entry for temperature.

The attribute SOSA__usedProcedure documents a two-step process.
The data in this file were first decoded from METAR format to BUFR format by NCEP.
MDL routines then decoded the BUFR data and ingested them.
Then, they were quality controlled with routines developed by MDL.
The attribute SOSA__usedProcedure takes on a character string value that names one or more value-less integers.
Those integers, in turn, convey metadata in their attributes about each procedureal step.
Here is a CDL fragment:

::

| long MetarObProcStep1;
|   :PROV__Activity = "StatPP__Methods/Ingest/DecodeBUFR";
|   :long_name = "Ingest BUFR encoded METAR observations from NCEP repository";
|   :PROV__Used = "StatPP__Data/NCEPSfcObsMetar";
|   :units = 1L; // long
|   :standard_name = "source";
|
| long MetarObProcStep2;
|   :PROV__Activity = "StatPP__Methods/QC/METARQC";
|   :long_name = "Apply MDL METAR Quality Control procedure";
|   :standard_name = "source";
|   :units = 1L; // long

The attribute strings associated with MetarObProcStep1 document that the data were ingested from BUFR-endcoded METAR observations in a repository maintained by NCEP.
The attribute PROV__Activity shows a BUFR decoding step while the attribute PROV__Used identifies the repository.
Both PROV__Activity and PROV__Used point to entries in the NWS Codes Registry where additional details can be documented.
The step where NCEP decoded the METAR-encoded observations and stored them in BUFR does not appear in the procedure.
Those steps that happened before the data were ingested are not documented as procedure steps.

The attribute strings associated with MetarObProcStep2 document that the data were quality controlled using a procedure developed and maintained by MDL.
The attribute PROV__Activity again points to a codes registry entry.
There is no entry for PROV__Used in this variable.
When PROV__Used is omitted, we presume that the results from the previous process step are the source for the current process step.

There are three time-related variables associated with METAR_Temp_instant_2_.
They are OM__phenomenonTimeInstant, OM__resultTime, and OM__validTime.
Here are the CDL fragments that declare each of them:

::

| long OM__phenomenonTimeInstant(default_time_coordinate_size=720);
|   :_FillValue = 9999L; // long
|   :calendar = "gregorian";
|   :units = "seconds since 1970-01-01 00:00:00.0";
|   :standard_name = "time";
|   :PROV__specializationOf = "( OM__phenomenonTime )";
|   :_ChunkSizes = 720U; // uint
|
| long OM__resultTime(default_time_coordinate_size=720);
|   :_FillValue = 9999L; // long
|   :calendar = "gregorian";
|   :units = "seconds since 1970-01-01 00:00:00.0";
|   :standard_name = "time";
|   :PROV__specializationOf = "( OM__resultTime )";
|   :_ChunkSizes = 720U; // uint
|
| long ValidTime(begin_end_size=2, default_time_coordinate_size=720);
|   :_FillValue = 9999L; // long
|   :calendar = "gregorian";
|   :units = "seconds since 1970-01-01 00:00:00.0";
|   :standard_name = "time";
|   :PROV__specializationOf = "( StatPP__concepts/TimeBoundsSyntax/BeginEnd OM2__Data/Time/validTime )";
|   :_ChunkSizes = 2U, 720U; // uint

The declarations we find here are somewhat different than those found in model output.
As one might expect, there are fewer dimensions and the values are simpler.
OM_phenomenonTimeInstant takes on a value for each hour of the month.
As noted above, the times are set to the top of each hour for all stations and times.
OM_resultTime values are equal to OM_phenomenonTime values.
OM_validTime is two-dimensional representing beginning time and ending time.
The beginning times equal the phenomenon times and result times.
(I.e., we don't intend for data consumers to use an observation before it's taken.)
The ending times are set to missing to show that we intend for data consumers to use an observation indefinitely.

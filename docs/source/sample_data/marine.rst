Marine Observations
===================

.. only:: format_html

    This section describes sample buoy observation output that can be :download:`downloaded here <./reduced_nbd201305.nc>`.
    If you are reading this in a PDF document, then you will need to access a web version to download the sample files.

This sample file contains marine station data from a selection of ~600 fixed data buoys located in the Great Lakes and coastal waters of the US.  The observations were taken during the month of May 2013.

The observations were processed through MDL's quality control (QC) routines.
Notably, the observation time information was altered in that process.
Specifically, all time data in this file are at the "top of the hour."
E.g., a METAR whose time was encoded as 1953 (19:50:00 UTC) is stored in this file with the time 20:00:00 UTC.
This is useful for a number of applications in statistical post-processing, but problematic in a number of other ways.

Here’s a CDL fragment for an array of 2-m temperature values.
(Output is captued from the application Panoply.
All atrributes that follow the variable declaration are associated with that variable.)

::

| short Temp_instant_2_(number_of_stations=614, default_time_coordinate_size=744, level=1);
|   :_FillValue = 9999S; // short
|   :OM__observedProperty = "StatPP__Data/Met/Temp/Temp";
|   :ancillary_variables = "OM__phenomenonTimeInstant OM__resultTime ValidTime MarineObProcStep1 MarineObProcStep2 ";
|   :standard_name = "air_temperature";
|   :coordinates = "elev0, station";
|   :long_name = "dry bulb temperature";
|   :valid_min = -80S; // short
|   :units = "degF";
|   :valid_max = 130S; // short
|   :SOSA__usedProcedure = "( MarineObProcStep1 MarineObProcStep2 )";
|   :_ChunkSizes = 614U, 744U, 1U; // uint

There are three dimensions.
The first, number_of_stations, of course, indexes the various stations.
The character variable stations contains the ICAO call letters that identify each.
The second dimension, default_time_coordinate, simply counts through the 744 UTC hours in the month of May 2013.
The last dimension is a vertical coordinate that satisfies the requirements of the CF Conventions.
It simply indicates 2 meters above the Earth's surface.

One of the first attributes identifies a number of ancillary variables, most of which are associated with time.
Each of these variables are explained in some detail below.

The attribute OM__observedProperty takes on a value that resolves to a code registry entry for temperature.

The attribute SOSA__usedProcedure points to a two step process.
The data in this file were decoded from a tabular text format.
(They likely were exchanged in a different format before they were encoded in tabular text.)
Then, they were quality controlled with routines developed by MDL.
The attribute SOSA__usedProcedure takes on a character string value that names one or more value-less integers.
Those integers, in turn, convey metadata in their attributes about each procedureal step.

Here is the CDL that describes the process step integers:

::

| long MarineObProcStep1;
|   :PROV__Activity = "StatPP__Methods/Ingest/DecodeTabularText";
|   :long_name = "Decode tabular text data";
|   :PROV__Used = "StatPP__Data/NDBC";
|   :units = 1L; // long
|   :standard_name = "source";
|
| long MarineObProcStep2;
|   :PROV__Activity = "StatPP__Methods/QC/MarineQC";
|   :long_name = "Marine Observation Quality Control";
|   :standard_name = "source";
|   :units = 1L; // long

The attribute strings associated with MarineObProcStep1 document that the data were ingested from marine observations in a tabular text format maintained by the National Data Buoy Center (NDBC).
Note that the attribute PROV__Activity shows a tabular text decoding step while the attribute PROV__Used identifies NDBC as the source.
Note that both PROV__Activity and PROV__Used point to entries in the NWS Codes Registry where additional details can be documented.

The attribute strings associated with MarineObProcStep2 document that the data were quality controlled using a procedure developed and maintained by MDL.
The attribute PROV__Activity again points to a codes registry entry.
There is no entry for PROV__Used in this variable.
When PROV__Used is omitted, we presume that the results from the previous process step are the source for the current process step.

There are three time-related variables associated with MARINE_Temp_instant_2_.
They are OM_phenomenonTimeInstant, OM_resultTime, and ValidTime.
Here are the CDL fragments that declare each of them:

::

| long OM__phenomenonTimeInstant(default_time_coordinate_size=744);
|   :calendar = "gregorian";
|   :units = "seconds since 1970-01-01 00:00:00.0";
|   :standard_name = "time";
|   :PROV__specializationOf = "( OM__phenomenonTime )";
|   :_FillValue = 9999L; // long
|
| long OM__resultTime(default_time_coordinate_size=744);
|   :units = "seconds since 1970-01-01 00:00:00.0";
|   :standard_name = "time";
|   :PROV__specializationOf = "( OM__resultTime )";
|   :calendar = "gregorian";
|   :_FillValue = 9999L; // long
|
| long ValidTime(begin_end_size=2, default_time_coordinate_size=744);
|   :PROV__specializationOf = "( StatPP__concepts/TimeBoundsSyntax/BeginEnd OM2__Data/Time/ValidTime )";
|   :units = "seconds since 1970-01-01 00:00:00.0";
|   :standard_name = "time";
|   :calendar = "gregorian";
|   :_FillValue = 9999L; // long

The declarations we find here are quite simlar to the one used for METAR-encoded surface observations.
OM__phenomenonTimeInstant takes on a value for each hour of the month.
As noted above, the times are set to the top of each hour for all stations and times.
OM_resultTime values are equal to OM_phenomenonTime values.
ValidTime is two-dimensional representing beginning time and ending time.
The beginning times equal the phenomenon times and result times.
(I.e., we don't intend for data consumers to use an observation before it's taken.)
The ending times are set to missing to show that we intend for data consumers to use an observation indefinitely.

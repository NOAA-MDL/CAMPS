.. _ref-to-v1-model-output:

Model output
============

.. only:: builder_html

   This section describes sample model output that can be :download:`downloaded here <./reduced_gfs201607.nc>`.
   If you are reading this in a PDF document, then you will need to access a web version to download the sample files.

This sample file contains gridded data from 2 runs of the NWS spectral Global Forecast System (GFS) that began at 0600 UTC on 01-02 July 2016.
It is interesting to note that the data are not from consecutive runs of the model.
Rather, the data producer has chosen to stratify these data by model cycle time.
Many statistical post-processing techniques stratify their data in this manner to accommodate the diurnally varying error characteristics of the model runs.

.. note::
   NOTE:  This file was modified from the original in a number of ways.
   Most of the modifications were intended to make the file smaller and easier to review.
   Zero values were inserted into large portions of the data arrays.
   The first 20 rows and 20 columns contain the original data.
   A little more than half of the variables were removed from the file.
   The remaining variables should be sufficient to illustrate the concepts.

The values were read from a latitude-longitude grid, and interpolated to a Polar Stereographic grid.

The sections below review sample CDL fragments and explain how the various attributes are used to document the contents of this file.

Here's a CDL fragment for a 2-m temperature field.  (Output is captured from the application Panoply.  All attributes that follow the 
variable declaration are associated with that variable.)

::

| float Temp_instant_2_21600(y=169, x=297, lead_times_3hr=93, default_time_coordinate_size=2, level=1);
|   :_FillValue = 9999.0f; // float
|   :OM__observedProperty = "StatPP__Data/Met/Temp/Temp";
|   :grid_mapping = "polar_stereographic";
|   :long_name = "temperature instant at 2m";
|   :ancillary_variables = "OM__phenomenonTimeInstant OM__resultTime ValidTime1 FcstRefTime LeadTime1 GFSModProcStep1 GFSModProcStep2 ";
|   :coordinates = "elev1, x, y";
|   :FcstTime_hour = 21600L; // long
|   :standard_name = "air_temperature";
|   :units = "K";
|   :SOSA__usedProcedure = "( GFSModProcStep1 GFSModProcStep2 )";
|   :_ChunkSizes = 85U, 149U, 47U, 1U, 1U; // uint

The y and x coordinates, of course, delineate the geogrphic grid.
Lead_times delineate the temporal domain for this variable, and default_time_coordinate_size delineates the two model cycles.
The value for FcstTme_hour equates to 0600 UTC on 01-Jan-1970, and it indicates that all data stored in this variable are 
associated with some 0600 UTC run of the NWP system.

The attribute OM__observedProperty takes on a value that resolves to a codes registry entry for temperature.

The attribute ancillary_variables identifies a number of ancillary variables, most of which are associated with time.  
Each of these variables is explained in some detail below.

The procedure attribute found in [O&M] is not readily available in a web-referenceable form.  Here, we substitute the attribute 
SOSA__usedProcedure.  The attribute SOSA__usedProcedure points to a two step process. The data in this file were decoded from GRIB2 
by MDL routines to ingest them into CAMPS. Then, a bilinear interpolation routine was used to convert from a latitude-longitude grid 
to a Polar Stereographic grid.

The attribute SOSA__usedProcedure takes on a character string value that names two value-less integers. Those integers, in turn, convey 
metadata in their attributes about each procedureal step. Here is the CDL fragment that declares these two integers:

::

|     long GFSModProcStep1;
|       :PROV__Activity = "StatPP__Methods/Ingest/DecodeGRIB2";
|       :long_name = "Ingest GRIB2-encoded GFS13 forecasts from NCEP repository";
|       :PROV__Used = "StatPP__Data/GFS13";
|       :units = 1L; // long
|       :standard_name = "source";
|
|     long GFSModProcStep2;
|       :PROV__Activity = "StatPP__Methods/Geosp/LinInterp";
|       :long_name = "Apply MDL bilinear interpolation technique";
|       :standard_name = "source";
|       :units = 1L; // long

The first step of the procedure decodes the data from GRIB2 and ingests them into CAMPS (PROV__Activity).  The attribute PROV__Used shows the 
input into this step of the procedure.  Of course, it's version 13 of the Global Forecast System (GFS).  The attribute PROV__Activity of 
GFSModProcStep2 shows that the second step was a linear interpolation technique.  Both of these concepts are documented in the NWS Codes Registry.

The next few CDL fragments for Temp_instant_2_21600 illustrate the time variables used within CAMPS.

Here's the CDL fragment that declares LeadTime (a duration measured from forecast_reference_time).  (LeadTime and LeadTime2 are similar.)

::

|  long LeadTime1(lead_times_3hr=93);
|       :_FillValue = 9999L; // long
|       :units = "seconds";
|       :standard_name = "forecast_period";
|       :PROV__specializationOf = "( StatPP__Data/Time/LeadTime )";
|       :_ChunkSizes = 93U; // uint
|       :_CoordinateAxisType = "TimeOffset";

LeadTime1 has only one dimension.  This is because the lead time values are identical for the two forecast cycles.  LeadTime1 is the only 
time-related variable that behaves in this way.  Note the attribute PROV__specializationOf.

LeadTime2 is dimensioned 12, and it is used for data that are forecast every 24 hours.  LeadTime is dimensioned 40, and it is used for data 
that are forecast every six hours.

Here's the CDL fragment that declares OM__phenomenonTimeInstant ("when the weather happens"):

::

| long OM__phenomenonTimeInstant(lead_times_3hr=93, default_time_coordinate_size=2);
|       :_FillValue = 9999L; // long
|       :calendar = "gregorian";
|       :units = "seconds since 1970-01-01 00:00:00.0";
|       :standard_name = "time";
|       :PROV__specializationOf = "( OM__phenomenonTime )";
|       :_ChunkSizes = 93U, 2U; // uint

OM__phenomenonTimeInstant has two dimensions.  The first dimension matches LeadTime, and the second tracks the forecast cycle.  Again, the 
attribute PROV__specializationOf designates the function of this variable.  There are other variables with similar names and functions, 
e.g., OM__PhenomenonTimePeriod6hr and OM__PhenomenonTimePeriod3hr.  As with LeadTime, they are used to care for 3- and 6-hour periods of time.

Here's the CDL fragment that declares OM_resultTime (the time the result became available):

::

|     long OM__resultTime(default_time_coordinate_size=2);
|       :_FillValue = 9999L; // long
|       :calendar = "gregorian";
|       :units = "seconds since 1970-01-01 00:00:00.0";
|       :standard_name = "time";
|       :PROV__specializationOf = "( OM__resultTime )";
|       :_ChunkSizes = 2U; // uint

OM_resultTime has one dimension that tracks the forecast cycle, and uses PROV__specializationOf

Finally, here's the CDL fragment that declares ValidTime (the time of intended use of the result):

::

| long ValidTime(lead_times=40, default_time_coordinate_size=2, begin_end_size=2);
|   :_FillValue = 9999L; // long
|   :calendar = "gregorian";
|   :units = "seconds since 1970-01-01 00:00:00.0";
|   :standard_name = "time";
|   :PROV__specializationOf = "( StatPP__concepts/TimeBoundsSyntax/BeginEnd OM2__Data/Time/ValidTime )";
|   :_ChunkSizes = 40U, 2U, 2U; // uint

As we saw with OM__phenomenonTime, ValidTime has two dimensions that track lead time and forecast cycle.  ValidTime, however, includes a third dimension 
that holds the beginning and end times of this period of time.

Note that the PROV__specializationOf attribute takes on two values.
This is because two different concepts are associated with this variable--the concept of validTime and the BeginEnd concept.
This latter concept makes it clear that a value of 1 in the last dimension indicates the beginning of the period of time, and a value of 2 indicates the end.

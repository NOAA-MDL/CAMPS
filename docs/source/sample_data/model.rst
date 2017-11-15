Model output
============

.. only:: builder_html

   This section describes sample model output that can be :download:`downloaded here <./reduced_gfs0020160700.nc>`.
   If you are reading this in a PDF document, then you will need to access a web version to download the sample files.

This sample file contains gridded data from 8 runs of the NWS spectral Global Forecast System (GFS) that began at 0600 UTC on 01-08 July 2016.  It is interesting to note that the data are not from consecutive runs of the model.
Rather, the data have been stratified by model cycle time.
Many statistical post-processing techniques stratify their data in this manner to accommodate the varying error characteristics of the model runs.

.. note::
   NOTE:  This file was modified from the original in a number of ways.
   Most of the modifications were intended to make the file smaller and easier to review.
   Zero values were inserted into large portions of the data arrays.
   The first 20 rows and 20 columns contain the original data.
   A little more than half of the variables were removed from the file.
   The remaining variables should be sufficient to illustrate the concepts.

The values were read from a latitude-longitude grid, and interpolated to a Lambert Conformal grid.

The sections below review sample CDL fragments and explain how the various attributes are used to document the contents of this file.

Here's a CDL fragment for a 2-m temperature field.  (Output is captured from the application Panoply.  All attributes that follow the variable declaration are associated with that variable.)

::

| short GFS13_Temp_instant_2_21600(y=169, x=297, lead_times=93, default_time_coordinate_size=8, level=1);
|   :_FillValue = 9999S; // short
|   :grid_mapping = "polar_stereographic";
|   :FcstTime_hour = 21600L; // long
|   :ancillary_variables = "OM_phenomenonTimeInstant OM_resultTime OM_validTime forecast_reference_time LeadTime mosLinearInterpolation ";
|   :coordinates = "elev0, x, y";
|   :long_name = "temperature instant at 2m";
|   :standard_name = "air_temperature";
|   :units = "K";
|   :OM_observedProperty = "https://codes.nws.noaa.gov/StatPP/Data/Met/Temp/Temp";
|   :OM_procedure = "( mosLinearInterpolation )";
|   :_ChunkSizes = 85, 149, 47, 3, 1; // int

The y and x coordinates, of course, delineate the geogrphic grid.  Lead_times delineate the temporal domain for this variable, and default_time_coordinate_size delineates the various model cycles.  The value for FcstTme_hour equates to 0600 UTC on 01-Jan-1970, and it indicates that all data stored in this variable are associated with some 0600 UTC run of the NWP system.

The next attribute identifies a number of ancillary variables, most of which are associated with time.  Each of these variables are explained in some detail below.

The attribute OM_observedProperty takes on a value that resolves to a code registry entry for temperature.

The attribute OM_procedure points to a one-step procedure.  The only processing performed by the software that created this file interpolated the data from the latitude/longitude file disseminated by the NWS to the northern polar stereographic grid described by attributes that are not shown in this fragment.  The attribute OM_procedure takes on a character string value that names one or more value-less integers.  Those integers, in turn, convey metadata in their attributes about each procedure step.

Here's the CDL fragment that declares mosLinearInterpolation:

::

| long mosLinearInterpolation;
|   :long_name = "MOS Linear Interpolation";
|   :LE_Source = "https://codes.nws.noaa.gov/NumericalWeatherPrediction/Models/GFS13";
|   :LE_ProcessStep = "https://codes.nws.noaa.gov/StatPP/Methods/Geosp/LinInterp";

The attribute LE_Source shows the input into this step of the procedure.  Of course, it's version 13 of the Global Forecast System (GFS).  The attribute LE_ProcessStep shows that a linear interpolation technique was applied.  Both of these concepts are documented in the NWS Codes Registry.

The next few CDL fragments illustrate the time variables used within WISPS.

Here's the CDL fragment that declares LeadTime.  (LeadTime1 and LeadTime2 are similar.)

::

| long LeadTime(lead_times=93);
|   :_FillValue = -9999L; // long
|   :units = "seconds";
|   :standard_name = "forecast_period";
|   :wisps_role = "LeadTime";
|   :_ChunkSizes = 93; // int

LeadTime has only one dimension.  This is because the lead time values are identical for the various forecast cycles.  LeadTime is the only time-related variable that behaves in this way.  Note the attribute wisps_role.

LeadTime is dimensioned 93, and it is used for data that are forecast every three hours.  LeadTime1 is dimensioned 40, and it is used for data that are forecast every six hours.  LeadTime2 handles 12-hour variables.

Here's the CDL fragment that declares OM_phenomenonTimeInstant:

::

| long OM_phenomenonTimeInstant(lead_times=93, default_time_coordinate_size=8);
|   :_FillValue = -9999L; // long
|   :calendar = "gregorian";
|   :units = "seconds since 1970-01-01 00:00:00.0";
|   :standard_name = "time";
|   :wisps_role = "OM_phenomenonTime";
|   :_ChunkSizes = 93, 8; // int

OM_phenomenonTimeInstant has two dimensions.  The first dimension matches LeadTime, and the second tracks the forecast cycle.  Again, the attribute wisps_role designates the function of this variable.  There are three other variables with similar names and functions--OM_PhenomenonTimeInstant1, OM_PhenomenonTimeInstant2, and OM_PhenomenonTimeInstant3.  As with LeadTime, they are used to care for use cases such as 3-, 6-, and 12-hourly time steps.



***************
4.  Coordinates
***************

.. note::
   CAMPS version 1.0 was built to support an older version of these standards.
   These documents describe a data encoding standard that will be used for CAMPS version 2.0.

4.1 Geospatial Coordinates
==========================

The guidelines set forth in the NetCDF-CF conventions for geospatial coordinates in the horizontal and vertical axes seem to thoroughly cover all use cases envisioned for CAMPS.
No extensions are planned.

4.2 Time Coordinates
====================

The netCDF-CF Conventions provide considerable guidance on the encoding of time coordinates.
The following sections supplement that guidance, define best practices, and encourage those best practices for netCDF-CAMPS.

4.2.1 Time Nomenclature
-----------------------

Time nomenclature seems to be a perennial stumbling block in StatPP.
This often becomes evident as data consumers attempt to process data that has been shared by one or more data producers.
At the risk of becoming tedious, this section will cover first principles and how they are named in the various standards.
The first definitions come from TS.

**TM__Instant**

“An instant is a zero-dimensional geometric primitive that represents position in time.
It is equivalent to a point in space.
In practice, an instant is an interval whose duration is less than the resolution of the time scale”  [TS].

In netCDF-CAMPS, a number of weather elements are usually represented as occurring at a point in time.
These include temperature, wind direction, wind speed, sky cover, and precipitation type.
For some of these elements, this is matter of convenience.
In reality, the systems that assess conditions are conducting time averages.
Moreover, analyses for multiple weather elements are generally associated with a single instant.
In reality, of course, the data that modern analyses process come from a variety of time scales.
In the same way, various weather elements in a METAR-encoded observation are associated with a single instant.

**TM__Period and TM__Duration**

“The period is a one-dimensional geometric primitive that represents extent in time.
The period is equivalent to a curve in space.
Like a curve, it is an open interval bounded by beginning and end points (instants), and has length (duration).
Its location in time is described by the temporal positions of the instants at which it begins and ends; its duration equals the temporal distance between those two temporal positions”  (ISO 19108).

Thus, a period of time has an instant when it begins, an instant when it ends, and a duration.
Generally knowledge of any two of the three will be sufficient to compute the third.

Here are some examples of periods of time:
from 00:00 UTC 24 Feb 2017 to 12:00 UTC 24 Feb 2017
the 12 hours ending at 12:00 UTC 24 Feb 2017

...and some examples of durations of time:

* 30 seconds
* 1 hour
* 2 days

 **Best Practice:**  *Variables that are inherently of type TM__Period should be encoded that way, using the methods outlined below.  We discourage the practice of encoding such fields as TM__Instant and providing human-readable labels that specify duration.*

Periods and durations that are long enough (generally > one day) often encounter encoding issues because of the vagaries associated with various calendar systems (e.g., leap years, non-Gregorian calendars)
The existing netCDF-CF Conventions seem to address these issues thoroughly.
No extensions are planned.

CF describes a method for identifying vertices on a time axis which can then be designated period bounds.
While this method is useful for many applications, we note a number of StatPP applications where it is inadequate.
(E.g., this method cannot describe overlapping time periods.)
Here we describe an alternative which is more general and better-suited to StatPP.

 **Best Practice:**  *When a variable is declared that will define objects of type TM__Period, that variable will have appropriate dimensionality and include a dimension (the one that varies fastest) of 2.
 That dimension can be interpreted as any two of the following three concepts:  TM_Duration, TM_Beginning, TM_Ending.
 This variable will also contain sufficient attributes to remove any ambiguity about the interpretation of that dimension of 2.  Ideally, this disambiguation will use URIs and be machine-readable.*

::

|  OM__phenomenonTimePeriod:PROV__specializationOf = "StatPP__concepts/TimeBoundsSyntax/BeginEnd", "OM__phenomenonTime";

.. note::
   The PROV-O concept specializationOf can take on multiple values.
   In the example above, the variable OM__phenomenonTimePeriod is a spcialization of the O&M concept phenomenonTime and it is also a specialization of the concept of the time bounds syntax named "BeginEnd".
   This is interpreted as dimension 0 contains the TM_Beginning and dimension 1 contains the TM_Ending.


**forecast_reference_time**

The forecast_reference_time is a standard name in the netCDF-CF Conventions.
In that document it is defined as “The ‘data time’, the time of the analysis from which the forecast was made” [CF].
This description seems to draw its origin from NWP.
It has broad applications within StatPP as well.
Clearly, the forecast_reference_time is an instant in time.
It is frequently used to define the epoch of the time coordinate for variables associated with NWP output.

 **Best Practice:**  *In datasets where this concept is meaningful, a variable should contain this time (these times) and the attribute standard_name assigned the value “forecast_reference_time.”  That said, netCDF-CAMPS does not discourage other practices that convey this concept.*

**leadTime**

The term “lead time” is often used to describe a duration of time that is measured from a forecast_reference_time to the time when some phenomenon is observed or forecast to occur.
We are aware of no formal definition of this concept by any Standards Development Organization (SDO; Various WMO standards provide instructions for encoding this concept).
There are a number of expressions that are commonly used to describe this concept (e.g., forecast period, forecast lead, time projection).
The CF Standard Names includes an entry for forecast_period that corresponds well to this concept.
For netCDF-CAMPS, we recommend that data producers adopt the term “lead time” and use it uniformly.

 **Best Practice:**  *In datasets where this concept is meaningful, a variable of appropriate dimensionality should be defined and contain leadTime values.  This variable should be declared as an auxiliary coordinate variable, as needed.  This variable should have the attribute PROV__specializationOf declared with a value that expresses the concept of leadTime.  Ideally this value will use a URI and be machine-readable.  This variable should also have a standard_name of “forecast_period.”*

**periodicTime and cadence**

The “duration of one cycle” (ISO 19108) is defined with the words “periodic time.”  While the term is defined in ISO 19108, it does not appear formally in the data models.  (Hence, we call it periodicTime, not TM__PeriodicTime.)  The concept of periodic time has two primary applications in StatPP.

First, periodic time can describe the duration between successive runs of an NWP system.  We suggest the term “cadence” to describe this characteristic.

Second, periodic time can be used to characterize certain datasets whose data elements have a regular spacing in time.  We suggest the term periodicTime to describe the duration between two successive leadTimes in datasets of this sort.

 **Best Practice:**  *In datasets where this concept is meaningful, the attribute structure should be added to the applicable time coordinates.  The value of the attribute should be a character string of the form “firstLeadTime=value periodicTime=value lastLeadTime=value.”  The values in this string are not intended for automated interpretation.  Rather, they are intended to convey information from data producers to data consumers.  ISO 8601 and 19108 define an encoding scheme for TM__Duration that is readily readable.  It is frequently used in web applications, and suits this purpose quite well.*

 *E.g., “firstLeadTime=P6H periodicTime=P3H lastLeadTime=P24H” describes leadTimes of 6, 9, 12, 15, 18, 21, and 24 hours.*

 *E.g., “firstLeadTime=P12H periodicTime=P24H lastLeadTime=P84H” describes leadTimes of 12, 36, 60, and 84 hours.*

**OM__phenomenonTime**

“The attribute phenomenonTime shall describe the time that the result (6.2.2.9) applies to the property of the feature-of-interest (6.2.2.7). This is often the time of interaction by a sampling procedure (8.1.3) or observation procedure (6.2.2.10) with a real-world feature.  NOTE 1:  The phenomenonTime is the temporal parameter normally used in geospatial analysis of the result.”  [O&M}

While not obvious from this definition, OM__phenomenonTime can be of type TM__Instant or TM__Period.  This makes OM__phenomenonTime appropriate for weather elements valid at both points in time (e.g., temperature, wind speed) and spans of time (e.g., event probabilities, precipitation accumulations).

 **Best Practice:**  *This concept is always meaningful for elements that are either observed, analyzed, or forecast.
 [O&M] requires it for all observations.
 For these elements a variable of appropriate dimensionality should be defined and contain OM__phenomenonTime values.
 This variable should be declared as an auxiliary coordinate variable, as needed.
 This variable should have the attribute PROV__specializationOf declared with a value of the form “(v1 v2 v3 … vn)” where n is a non-zero positive integer.
 (The multi-valued syntax allows these variables to be specializations of more than one concept.)
 One of the tokens v1, etc. will express the concept of phenomenonTime.
 Ideally this value will use a URI and be machine-readable.*

 *Please note the Best Practice described above for all variables that contain the concept TM_Period.*

 *We recognize that in many applications a combination of model_reference_time and leadTime can convey the same content as OM__phenomenonTime.  The Best Practice, however, is to create an auxiliary coordinate variable explicitly for this purpose and assign it the appropriate attribute.  The purpose, of course, is to limit implicit metadata wherever possible.*

**OM__resultTime**

“The attribute resultTime:TM__Instant shall describe the time when the result became available, typically when the procedure (6.2.2.10) associated with the observation was completed For some observations this is identical to the phenomenonTime. However, there are important cases where they differ.
…

EXAMPLE 3 Where sensor observation results are post-processed, the resultTime is the post-processing time, while the phenomenonTime is the time of initial interaction with the world.

EXAMPLE 4 Simulations may be used to estimate the values for phenomena in the future or past. The phenomenonTime is the time that the result applies to, while the resultTime is the time that the simulation was executed.”  [O&M]

OM__resultTime has clear applications to StatPP in general and operational meteorology as well.  This concept provides a clear, standards-based way to label a product with it’s time of production.

 **Best Practice:**  *This concept is always meaningful for elements that are observed, analyzed, or forecast.
 [O&M] requires it for all observations.
 For these elements a variable of appropriate dimensionality should be defined and contain OM__resultTime values.
 This variable should be declared as an ancillary variable, as needed.
 This variable should have the attribute PROV__specializationOf declared with a value of the form “(v1 v2 v3 … vn)” where n is a non-zero positive integer.
 (The multi-valued syntax allows these variables to be specializations of more than one concept.)
 One of the tokens v1, etc. will express the concept of resultTime.
 Ideally this value will use a URI and be machine-readable.*

In general, for observations, OM__resultTime = OM__phenomenonTime; for analyses, OM__resultTime ≥ OM__phenomenonTime; and for forecasts, OM__resultTime ≤ OM__phenomenonTime.

**OM__validTime**

The concepts covered above in this section seem to be clarifications and standardizations of concepts that have been applied to NWP and StatPP for years.  Most English speakers will be able to intuitively grasp the concepts represented by names like phenomenonTime, leadTime, and resultTime.  Unfortunately, the term “valid time” is used widely in NWP and StatPP.  Frequently, it’s common usage differs significantly from the O&M definition, below:

“If present, the attribute validTime:TM__Period shall describe the time period during which the result is intended to be used.

NOTE This attribute is commonly required in forecasting applications.”  [O&M]

OM__validTime is not meaningful in all contexts.  E.g., a temperature observation taken at a TM__Instant can be fruitfully used indefinitely.  In operational meteorology, however, a temperature forecast will probably be replaced by a new (and presumably better) forecast in a matter of hours.  Thus, OM__validTime can provide a standards-based way for data producers to inform data consumers of their intentions for the use of their products.

In applications where confusion is possible, data producers should take care to declare this ancillary variable with a name that will be meaningful to data consumers (e.g. useful_time, time_of_intended_use, validity_time).

 **Best Practice:**  *In datasets where this concept is meaningful, a variable of appropriate dimensionality should be defined and contain OM__validTime values.
 This variable should be declared as an ancillary variable, as needed.
 This variable should have the attribute PROV__specializationOf declared with a value of the form “(v1 v2 v3 … vn)” where n is a non-zero positive integer.
 (The multi-valued syntax allows these variables to be specializations of more than one concept.)
 One of the tokens v1, etc. will express the concept of validTime.
 Ideally this value will use a URI and be machine-readable.*

 *Please note the Best Practice described above for all variables that contain the concept TM_Period.*

*******************
Primary File Format
*******************

Network Common Data Format (NetCDF) will be used as the primary CAMPS file
format, as it supports the creation, access, and sharing of array-oriented
scientific data.  In addition, NetCDF also offers a self-describing data format
with more flexibility than other widely used table driven formats such as
TDLPACK or Gridded Binary (GRIB).   Also, NetCDF seems to have more widespread
support within the StatPP community than other self-describing data formats
like Hierarchical Data Format (HDF).

Use of the CF-Convention
========================

Within the netCDF family, CAMPS has adopted the NetCDF Climate and Forecast
(netCDF-CF) conventions format.  NetCDF-CF shares common goals with CAMPS,
including the processing and sharing of netCDF files and facilitating data
exchange.  NetCDF-CF also provides a controlled vocabulary that guides the
specification of metadata, as well as other spatial and temporal properties of
variables commonly used in StatPP datasets.

First and foremost, a netCDF-CAMPS file must comply with both the netCDF
standard and the associated CF conventions (http://cfconventions.org/).
**The CF conventions recommend the file extension “.nc” and imposes no other
restrictions on file names.** Similarly, netCDF-CAMPS imposes no further
restrictions on variable names or dimensions beyond those established for CF.

Similar to the CF convention, most of the requirements for **netCDF-CAMPS** are
focused on the use of attributes, ancillary variables, and auxiliary coordinate
variables to adequately describe the metadata associated with StatPP variables.
We also recommend the use of a global attribute “Conventions” which should
include the string “CAMPS-1.0” to indicate compliance with this profile. Since
all files that follow the CAMPS application profile also follow the netCDF-CF
Conventions, the conventions attribute should also contain the appropriate CF
string (Ex: Conventions = “CF-1.7 CAMPS 1.0”).

Guidelines for Construction of CF Standard Names <http://cfconventions.org/Data/cf-standard-names/docs/guidelines.html>`_
provides background for how CF Standard Names are constructed and how new prototype
standard names should be developed.  Included in this description are
Transformations which are Standard Names constructed via other Standard Names.
There are cases where there are no CF Standard Names or Transformations that
adequately describe the given StatPP variable, method, or process. In CAMPS when
development of a new Transformation or Standard Name is necessary, we declare an
attribute named **prototype_standard_name** as well as provide the most relevant
CF Standard Name to the given variable, method, or process. the. This conveys our
intent while maintaining conformity with the current standard.

Use of NetCDF-Classic-LD
========================

NetCDF-CAMPS makes use of Linked Data (LD) for encoding and publishing data
wherever possible.  We follow the netCDF Classic Linked Data standard (netCDF-LD)
(http://docs.opengeospatial.org/DRAFTS/19-002.html -- see section 6).
One key aspect of netCDF-LD that CAMPS takes advantage of is the mapping of
global and variable attributes within a NetCDF-CAMPS file to Uniform Resource
Identifiers (URIs), using prefixes and aliases.  Following the netcdf-LD
guidelines will allow NetCDF-CAMPS files to be represented within the Resource
Description Framework (RDF).  This furthers the versatility goal of CAMPS by
allowing the use of other linked data technologies.

An example of how NetCDF-CAMPS utilizes the prefix and alias aspect of netcdf-LD
follows.  The user should specify group attributes which specify the necessary
prefixes within the file.

Prefix definition and use: (from section 6.3.3
(http://docs.opengeospatial.org/DRAFTS/19-002.html).

“A prefix is declared using a name-value-pair that associates a short name
(e.g. cf, bald), with a URI. A single prefix declaration is an attribute and a
value: the attribute name is the prefix name and the attribute value is the full
URI for that prefix."

The 'double underscore' character pair: __ is used as an identifier and as the
termination of the prefix; the double underscore is part of the prefix.

**The following is CDL output showing the prefixes from a NetCDF-CAMPS file:**

::

|  group: prefix_list {
|   // group attributes:
|            :StatPP__ = "http://codes.nws.noaa.gov/StatPP/" ;
|            :OM2__ = "http://codes.nws.noaa.gov/StatPP/" ;
|            :SOSA__ = "http://www.w3.org/ns/sosa/" ;
|            :OM__ = "http://www.w3.org/ns/sosa/" ;
|            :PROV__ = "http://www.w3.org/ns/prov/#" ;
|            :StatppUncertainty__ = "http://codes.nws.noaa.gov/StatPP/Uncertainty" ;
|   } // group prefix_list
|  }

These prefixes are utilized to link metadata within a variable to web
documentation. The following is CDL output for a NetCDF-CAMPS file that shows
how a prefix can be used to link a variables metadata to a NWS codes registry entry.

::

|double Temp_instant_700_21600(default_time_coordinate_size, number_of_stations, level) ;
|          Temp_instant_700_21600:_FillValue = 9999. ;
|          Temp_instant_700_21600:OM__observedProperty = "StatPP__Data/Met/Temp/Temp" ;
|          Temp_instant_700_21600:grid_mapping = "polar_stereographic" ;
|          Temp_instant_700_21600:SOSA__usedProcedure = "( GFSModProcStep1 GFSModProcStep2 LinSmooth BiLinInterp )" ;
|          Temp_instant_700_21600:long_name = "temperature instant at 2m" ;
|          Temp_instant_700_21600:filepath = "/scratch3/NCEPDEV/mdl/Emily.Schlie/inputfiles/greg_test/gfs0020160700.nc" ;
|          Temp_instant_700_21600:ancillary_variables = "OM__phenomenonTimeInstant OM__resultTime ValidTime FcstRefTime LeadTime GFSModProcStep1 GFSModProcStep2 LinSmooth BiLinInterp " ;
|          Temp_instant_700_21600:coordinates = "plev0 station" ;
|          Temp_instant_700_21600:FcstTime_hour = 21600LL ;
|          Temp_instant_700_21600:standard_name = "air_temperature" ;
|          Temp_instant_700_21600:units = "K" ;

In the CDL output above OM__observedProperty is set to the path
StatPP__Data/Met/Temp/Temp.  StatPP__ has been given the prefix definition of
http://codes.nws.noaa.gov/StatPP/.  Thus if one replaces the prefix with it’s
definition they get the full URI to the codes registry entry for temperature --
http://codes.nws.noaa.gov/StatPP/Data/Met/Temp/Temp.  This same technique can
also be applied to the other part of the bolded CDL output above
“OM__observedProperty”.  By replacing OM__ with it’s prefix definition, the user
will be directed to http://www.w3.org/ns/sosa/observedProperty, which is the
documentation describing O&M observedProperty.

The user is encouraged to read through the entirety of section 6 within the
“OGC Encoding Linked Data Graphs in NetCDF Classic Files” documentation and
apply these techniques whenever possible when creating and processing
Netcdf-CAMPS data files.

***********************
Metadata
***********************

A key motivation in establishing the NetCDF-CAMPS metadata structure, has been to develop a well-defined template for incorporating descriptive, 
well established, controlled vocabularies for StatPP output. Here CAMPS introduces an application profile, which utilizes 3 controlled vocabularies: 
`NetCDF Climate and Forecast (CF) Conventions <https://cfconventions.org/>`_, `PROV Family of Documents (PROV-O) <https://www.w3.org/TR/prov-overview/>`_, 
and `Sensor, Observation, Sample, and Actuator (SOSA) <https://www.w3.org/TR/vocab-ssn/>`_. 
These data models and ontologies are already in use outside the U.S., and are hosted on the Web (supported by XML). 
CAMPS also makes use of `NetCDF Linked-Data <https://binary-array-ld.github.io/netcdf-ld/>`_, which allows for the linkage of a given attribute, to an external descriptive source. 

There are several different "types" of variables in a NetCDF-CAMPS file.  Some contain numerical data, while others contain only descriptive metadata. 
The main types of variables are:

- **Primary variable**:  All “primary_variables" are listed as a string, with space delimiters, under the “global attributes” 
  section of a NetCDF-CAMPS file.  These variables should satisfy CF-Convention rules, and be represented as a Camps_data object, 
  with numerical data.
- **Metadata variable**: This type of variable contains no numerical data, only metadata attributes that help describe a procedure 
  or some important characteristic of a primary variable.  
- **Coordinate variable**:  Our definition of a coordinate variable matches the definition outlined in NetCDF CF-Conventions.

  - **Time variable**:  Any variable containing time information.  Examples would be: phenomenonTime, forecast_reference_time, 
    and lead_time.  Most time variables are going to either be coordinate variables, or auxiliary coordinate variables, 
    following CF-Conventions.
  - **Location variable**: These are variables which signify the horizontal axis of a primary variable. 
    These will either be coordinate variables or auxiliary coordinate variables, following CF-Conventions.
- **Vertical coordinate variable**: These variables will contain the numerical data, and metadata, necessary to describe the vertical axis 
  information for a primary variable. This information is attached to a primary variable via the vertical_coord metadata attribute, 
  and is also included in the ancillary_variables attribute list. 
  
By establishing this application profile, our goal is to improve the interoperability within the StatPP and Atmospheric Science community.  
This will also ensure that CAMPS data files contain sufficient metadata to be self-describing for relatively long periods of time. 
We introduce the shorthand NetCDF-CAMPS to describe a file that conforms to this application profile.  The metadata properties outlined in 
this documentation suffice for the intended purposes of StatPP within MDL.  However, any user of CAMPS is welcome, and even encouraged, 
to use any additional metadata properties necessary for their specific use case.  

NetCDF CF-Conventions
=======================

`NetCDF Climate and Forecast (CF) Conventions <https://cfconventions.org/>`_ are meant to encourage the exchange of data created with the NetCDF API.  
These conventions provide a controlled vocabulary (standard names), and a controlled data structure. This allows descriptive metadata, 
and spatial and temporal properties, to be encoded for each variable within a file. These conventions are gaining in popularity in the 
atmospheric science community, with many new programs and applications using them as a standard. CAMPS aims to be fully NetCDF CF compliant, 
while including additional metadata ontologies, and unique CAMPS terminology where necessary.  

While NetCDF CF-Conventions is widely used and a stable resource, it is also actively maintained.  If a specific standard name, 
or method of representing data, is not possible under the current convention rules, 
there is a `discussion page <https://github.com/cf-convention/cf-conventions/issues>`_ where new proposals may 
be submitted.  If approved, they are published in a subsequent version of the 
`CF Standard Name Table <https://cfconventions.org/standard-names.html>`_. The CAMPS team has, and will continue 
to, publish new standard names, as necessary. Additionally, there are 
`guidelines for construction of CF Standard Names <http://cfconventions.org/Data/cf-standard-names/docs/guidelines.html>`_, which provides 
background for how CF Standard Names are constructed, and how new standard names should be developed. Included in this description are 
transformations of existing standard names, which should be utilized, if possible, before new standard names are proposed. If no 
CF standard name, or transformation, adequately describes the given StatPP variable, method, or process, the most appropriate standard 
name should be used, while a proposal for a new standard name should be initiated.

**Primary Variables:** While not an official CF-Convention term, a primary variable within CAMPS should satisfy CF-Convention rules.  
A primary variable should contain the following CF-Conventions metadata attributes:

- standard_name  - Should use the most appropriate standard name from the CF standard name table.
- long_name - A human readable definition of the variable.
- coordinates - Following CF conventions, this attribute specifies the auxiliary coordinate variables for the primary variable.
- ancillary_variables - Following CF conventions, this attribute specifies a variable, or procedure, that contains data, or information, 
  closely associated with the given primary variable. The value should be a blank separated list of variable or procedure names, 
  encoded as a single string.
  
**CF-Convention Ancillary Variables:** These attributes aid in describing the primary variable, and may or may not contain numerical data.

**CF-Convention Coordinate Variables:** A CF-Convention coordinate variable has a very strict definition.  
The variable can only have a single dimension, and that dimension must be the same name as the variable itself (ex: latitude(latitude)). 
The data must be numeric in type and be either monotonically increasing or decreasing, without missing values.  

**CF-Convention Auxiliary Coordinate Variables:**  A CF-Convention auxiliary coordinate variable helps make up for the flexibility that 
a coordinate variable lacks. These variables must contain coordinate data, but can be multi-dimensional, and there are no restrictions on 
the naming of the variable.  

**Globals:**  Every NetCDF-CAMPS file must contain the appropriate string representing the version of CF it follows.  

Example:
::
    // global attributes:
                :Conventions = "CF-1.7" ;

SOSA
=====

`The Semantic Sensor Network Ontology [SSN] <https://www.w3.org/TR/vocab-ssn/>`_, developed by the World Wide Web Consortium (W3C), 
also includes a simple core ontology named SOSA (Sensor, Observation, Sample, and Actuator).
This ontology introduces a data model and a controlled vocabulary that is useful for the description of both 
observations and forecasts of a given StatPP variable. Attributes can be easily recognized and the terminology 
is designed to apply across disciplines.

The most fundamental metadata concept in CAMPS is the **Observation** class.  SOSA defines Observation as: 
“Act of carrying out an (*Observation*) *Procedure* to estimate or calculate a value of a property of a 
`FeatureOfInterest <https://www.w3.org/TR/vocab-ssn/#SOSAFeatureOfInterest>`_. 
Links to a *Sensor* to describe what made the Observation and how; links to an *ObservableProperty* to describe what the 
result is an estimate of, and to a *FeatureOfInterest* to detail what that property was associated with.”

The procedure that estimates a temperature value at some point on the earth could be a human reading a mercury-in-glass thermometer, 
an automated observing platform reading a voltage from a sensor, or an numerical weather prediction system running on a supercomputer. 
All three are procedures; all can estimate temperature values. Thus, one can consider the difference between an observation and a 
forecast to be a difference in the estimating procedure used.

The following SOSA properties are necessary to fully comply and describe NetCDF-CAMPS data (italics represent related SOSA classes 
and properties the user should familiarize themselves with). Every primary_variable should contain these SOSA metadata attributes:

- `observedProperty <https://www.w3.org/TR/vocab-ssn/#SOSAobservedProperty>`_: “Relation linking an Observation to the property that 
  was observed. The ObservableProperty should be a property of the FeatureOfInterest (linked by hasFeatureOfInterest) of this Observation.”
  
  Within a NetCDF-CAMPS file, every unique primary variable will have an observedProperty.  For example: 500 mb temperature has an 
  observedProperty of temperature. The value of the observedProperty attribute will resolve to a URI, usually an entry in the NWS Codes 
  Registry. This URI will refer to a clear description of the primary_variable’s property. The URI need not describe any procedures 
  performed to obtain the variable. 
- `phenomenonTime <https://www.w3.org/TR/vocab-ssn/#SOSAphenomenonTime>`_: “The time that the Result of an Observation, Actuation, or Sampling applies to the FeatureOfInterest. Not necessarily 
  the same as the resultTime. May be an interval or an instant, or some other compound temporal entity [owl-time].”
  
  The unique definition of phenomenonTime, within the SOSA ontology, allows for a standardized time scheme to persist across all driver 
  scripts that make up a CAMPS development.  However, there are slight, but important, differences between the phenomenonTime for forecast 
  model output vs. observations. 

  The phenomenonTime for forecast model output is: forcast_reference_time (initialization date and time) + forecast_period (lead time).  
  This effectively gives the time the phenomenon is forecast to occur.    

  There is no forecast_reference_time, or forecast_period for observational data.  Instead, the phenomenonTime is simply the time at 
  which the phenomenon occurred. 
- `usedProcedure <https://www.w3.org/TR/vocab-ssn/#SOSAusedProcedure>`_: “A relation to link to a reusable Procedure used in making an 
  Observation, an Actuation, or a Sample, typically through a Sensor, Actuator or Sampler.”
  
  To expand on the idea of a Procedure within CAMPS, we look to the PROV-O ontology.  This ontology allows for categorization of procedures. 
  Those being applied to a dataset by the current user, or procedures which were previously applied to a dataset, either by a different user, 
  or the current user at an earlier point in time.  This is specifically relevant when performing a full CAMPS development, as a user 
  executes each subsequent driver script. 
  
  Within a NetCDF-CAMPS object, usedProcedures should be encoded in the same order that the procedures were/are performed.  
  Each usedProcedure is encoded as a separate metadata variable within the file, containing no numerical data, whose attributes describe 
  the usedProcedure.

PROV-O
=======

The PROV Family of Documents (PROV) provides a model for provenance information (entities, activities, production of data).  
This information can be used to form assessments about the quality of the data.  PROV allows for the exchange of such information using 
formats such as RDF and XML. 

`The PROV Ontology (PROV-O) <https://www.w3.org/TR/2013/REC-prov-o-20130430/>`_, “provides a set of classes, properties, 
and restrictions that can be used to represent and interchange provenance information generated in different systems and under 
different contexts. It can also be specialized to create new classes and properties to model provenance information for different applications 
and domains.”

NetCDF-CAMPS utilizes this ontology to specify data sources, procedures, and inherited information about a given dataset.  
The following PROV-O properties are used to encode NetCDF-CAMPS output:

- `entity <https://www.w3.org/TR/2013/REC-prov-o-20130430/#p_entity>`_- Is used exclusively for encoding statistics and coefficients within 
  NetCDF-CAMPS equation output files.  This attribute should resolve to a web based URI with a more robust description of the entity.
- `activity <https://www.w3.org/TR/2013/REC-prov-o-20130430/#p_activity>`_ - This attribute should be included for all procedure metadata 
  variables.  It should resolve to a web based URI providing more detailed information on the given procedure. Likely a NWS codes 
  registry entry.
- `used <https://www.w3.org/TR/2013/REC-prov-o-20130430/#used>`_ - Represents the entity that is being used by the given procedure.  
  Where applicable, provides the source of the data for the procedure. Not required.
- `wasInformedBy <https://www.w3.org/TR/2013/REC-prov-o-20130430/#wasInformedBy>`_ - The value of this attribute will contain strings 
  representing the procedures performed on this data prior to the current application.  This metadata attribute should be present for all 
  primary_variables, but can be empty if appropriate.
- `wasDerivedFrom <https://www.w3.org/TR/2013/REC-prov-o-20130430/#wasDerivedFrom>`_ - The value of this attribute will contain strings 
  representing the individual pieces of information (often other primary variables) that went into deriving the given primary variable. 
  This attribute will only be included for primary variables that have been computed during the current application.  
- `hadPrimarySource <https://www.w3.org/TR/2013/REC-prov-o-20130430/#hadPrimarySource>`_- The originating source of the data for a 
  primary variable.  Should be a predefined string representing source data recognized by CAMPS (Ex: METAR).  
  New sources can easily be added.
- `specializationOf <https://www.w3.org/TR/2013/REC-prov-o-20130430/#specializationOf>`_- Used in NetCDF-CAMPS to link a very specific 
  time variable to a broader time concept. 

NetCDF Classic Linked-Data
============================

NetCDF-CAMPS makes use of `Linked Data (LD) <https://binary-array-ld.github.io/netcdf-ld/>`_ for encoding and publishing data wherever 
possible. One key aspect of netCDF-LD that CAMPS takes advantage of is the mapping of global and variable attributes within a 
NetCDF-CAMPS file to URIs, using prefixes. Following the NetCDF-LD guidelines will allow NetCDF-CAMPS files to be represented within 
the Resource Description Framework (RDF). This furthers the versatility goal of CAMPS by allowing the use of other linked data technologies.

For example, CAMPS uses the SOSA__ prefix to designate concepts that had their origin in SOSA. In order to fully adhere to the Netcdf-CAMPS 
structure, there will be multiple prefixes in any given CAMPS file. The user should include NetCDF group attributes which identify the 
necessary prefixes within the file. The ‘double underscore’ character pair: __ is used as an identifier and as the termination of the prefix; 
the double underscore is part of the prefix.

**CDL output showing the prefixes from a NetCDF-CAMPS file:**

::
    |  group: prefix_list {
    |   // group attributes:
    |            :StatPP__ = "http://codes.nws.noaa.gov/StatPP/" ;
    |            :SOSA__ = "http://www.w3.org/ns/sosa/" ;
    |            :PROV__ = "http://www.w3.org/ns/prov/#" ;
    |   } // group prefix_list
    |  }

CDL output showing how a prefix is used to link a variable's metadata to external web resources:

:: 
    short Temp_instant_2m(phenomenonTime, stations) ;
        Temp_instant_2m:_FillValue = 9999s ;
        Temp_instant_2m:`SOSA__observedProperty <https://www.w3.org/TR/vocab-ssn/#SOSAobservedProperty>`_ = `"StatPP__Data/Met/Temp/Temp" <https://www.w3.org/TR/vocab-ssn/#SOSAobservedProperty>`_ ;
        Temp_instant_2m:long_name = "dry bulb temperature" ;
        Temp_instant_2m:valid_min = -80s ;
        Temp_instant_2m:valid_max = 130s ;
        Temp_instant_2m:standard_name = "air_temperature" ;
        Temp_instant_2m:units = "degF" ;
        Temp_instant_2m:vertical_coord = "elev0" ;
        Temp_instant_2m:`PROV__hadPrimarySource <https://www.w3.org/TR/2013/REC-prov-o-20130430/#hadPrimarySource>`_ = "METAR" ;
        Temp_instant_2m:coordinates = "phenomenonTime latitude longitude" ;
        Temp_instant_2m:ancillary_variables = "elev0 phenomenonTime DecodeBUFR METARQC " ;
        Temp_instant_2m:missing_value = 9999s ;
        Temp_instant_2m:`PROV__wasInformedBy <https://www.w3.org/TR/2013/REC-prov-o-20130430/#wasInformedBy>`_ = "( )" ;
        Temp_instant_2m:`SOSA__usedProcedure <https://www.w3.org/TR/vocab-ssn/#SOSAusedProcedure>`_ = "( DecodeBUFR METARQC )" ;

In the CDL output above SOSA__observedProperty is set to the path StatPP__Data/Met/Temp/Temp. StatPP__ has been given the prefix 
definition of http://codes.nws.noaa.gov/StatPP/. Thus if one replaces the prefix with it’s definition they get the full URI to the 
codes registry entry for temperature (http://codes.nws.noaa.gov/StatPP/Data/Met/Temp/Temp). This same technique is also applied to 
other prefixes followed by double underscores in CDL output above “SOSA__observedProperty”. By replacing SOSA__ with it’s prefix 
definition, the user will be directed to http://www.w3.org/ns/sosa/observedProperty, which is the documentation describing 
SOSA observedProperty.




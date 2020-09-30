5.  Event Probabilities
========================

Event probabilities are commonplace in StatPP applications."http://www.w3.org/ns/sosa/";
Two examples are the probability of a severe thunderstorm and the probability that the temperature will fall within a predefined range.
From a statistical point of view they are both events and both can have probability forecasts.
A data producer, however, will likely choose to provide different metadata for these two examples.
For the severe thunderstorm probability, one should provide, or better yet, refer to a definition of the term "severe thunderstorm."
This definition will likely be written in plain language for human interpretation.
For the temperature, however, the data producer will likely choose to encode the upper and, perhaps, lower bounds of the predefined range in a machine-readable form to maximize transparency for data consumers.

For clarity, we name that class of probability forecasts that can be represented by a categorical distribution “categorical event probabilities,” and we name the class of probability forecasts of yes/no events that are best described in human-readable terms “dichotomous event probabilities.”
Additionally, we recommend that data producers treat probability forecasts of the exceedance or non-exceedance of some threshold value as a one-category case of a categorical event probability.
It is arguably simpler to encode these events as dichotomous events, but the two-category approach provides data consumers with a richer set of machine-readable metadata.

We present a few examples to concretize these abstract concepts:

 - *Categorical Event Probability.*
   Continuous weather elements such as precipitation amount, visibility, and ceiling height can be binned into categories.
   These categories may or may not be mutually exclusive and exhaustive.
   One can then produce a probability that the verifying value will fall into each category.

 - *Categorical Event Probability.*
   One common forecast in the US is named Probability of Precipitation (PoP).
   This is the probability that 0.01” or more of liquid equivalent precipitation will fall at a pre-selected point.
   (This value was chosen for a number of reasons.
   One reason is that this the amount of rainfall required to “wet the sidewalks.”)
   One can argue that the simpler data encoding of a dichotomous event probability is more appropriate for this event.
   Here, however, we present PoP as a one-category case of a categorical event probability.
   We consider the additional metadata to be valuable to data consumers.

 - *Dichotomous Event Probability.*
   Precipitation can be categorized as liquid, freezing, and frozen.
   Since these three phases can coexist, data producers may choose to convey information about three separate dichotomous events, i.e., liquid precipitation vs. no liquid precipitation, freezing precipitation vs. no freezing precipitation, and frozen precipitation vs. no frozen precipitation.

 - *Dichotomous Event Probability.*
   The concept of "convection" is defined by one data producer as either lightning observed nearby or radar echoes stronger than a predetermined limit.
   Rather than encode the complexity of this either/or definition, the data producer chose to describe the event in human-readable terms and encode the forecasts as dichotomous event probabilities.

5.1  Categorical Event Probabilities
--------------------------------------

Categorical event probabilities are commonplace in StatPP applications (e.g., the probability of visibility being in a predefined range named MVFR or the probability of observing 0.01” or more of precipitation during a 12-hour period, PoP12).
They often estimate the probability that the value of some continuous weather element will fall within a predefined range during a period of time or at some instant in time.
The probability that a value will exceed a threshold can be considered a degenerate case with one category.

The categorical event probabilities will be stored in a variable of appropriate dimensionality and have units of unity.
One or more auxiliary variables are needed to identify the predefined threshold boundaries, time boundaries, and a categorical event definition.

.. note::
   The following Best Practices reference two variables, the categorical event probability variable and the categorization variable.
   Their roles can be confusing.
   The **categorical event probability variable** will generally be one of the primary variables in the netCDF file.
   This is the variable that contains probabilities and *conveys data* to the data consumer.
   The **categorization variable** will generally be an ancillary variable and contain no data.
   Rather, the categorization variable will convey the substantial amounts of metadata required to effectively interpret the probabilities contained in the categorical event probability variable.
   The **categorization procedure variable** will generally be an ancillary variable and contain no data.
   Rather, this variable will convey the methods and data needed to assign an arbitrary value to a category without ambibuity.

**Best Practice:**
*The categorical event probability variable should declare the attribute standard_name which takes the form probability_distribution_of_X_over_Z, where X is the standard name of the weather element and Z is likely time.*

**Best Practice:**
*The categorical event probability variable should declare the attribute OM__observedProperty which takes a value that is a URI.  This URI should point to a generic description of categorical event probabilities.  It need not specify the weather element.*

**Best Practice:**
*The categorical event probability variable should declare the attribute OM__procedure (or, equivalently, SOSA__usedProcedure) that takes on the form described above for documenting multi-step processes.  This includes a string of tokens that resolve to the names of auxiliary variables that convey additional information in their attributes.  This multi-step procedure documents the steps the data producer followed to create the categorical event probabilities, not the process of categorization.*

*The units of the categorical event probability variable should be unity.  If time bounds are needed, they should be associated with the categorical event probability.*

**Best Practice:**
*The categorical event probability variable should declare an attribute with a name that conveys the concept of categorization.  Ideally, the attribute name will be a URI that resolves to a more complete description.  The value of this attribute will take the form "( v1 )", where v1 is the name of a variable, the categorization variable, whose metadata will convey the details of the categorization.*

*The units of the categorization variable should be the appropriate meteorological units of the weather element being categorized.  The meteorological category boundaries should be encoded in an auxiliary variable associated with the categorization variable, not the categorical event probability variable.  Otherwise, the units will not match.*

**Best Practice:**
*The categorization variable should declare the attribute OM__observedProperty with a value that takes on the form of a URI.  This URI should provide a description of the weather element that has been categorized.*

**Best Practice:**
*If appropriate, the categorization variable should declare minimum and/or maximum values.  These may be useful in the categorization process described below.*

**Best Practice:**
*The categorization variable should declare the attribute OM__procedure (or, equivalently, SOSA__usedProcedure) with a value that takes on the form "( v1 )", where v1 names a categorization procedure variable.  The attributes of this variable will convey all the information required to interpret the categories.*

**Best Practice:**
*The categorization procedure variable should declare an attribute that conveys the concept of identity.  Ideally, the attribute name will resolve to a URI.  The value of this attribute will also be a URI that describes the method used to form categories from boundary values.  The method must unambiguously assign any valid value of the categorization variable to one and only one category.  Categories should be mutually exclusive and exhaustive.*

*Ideally, each category will also be described by a URI that contains sufficient machine-readable information to fully document the catgorization process.*


5.2  Dichotomous Event Probabilities
--------------------------------------

Dichotomous event probabilities are also common in StatPP applications (e.g., the probability of observing a tornado vs. not observing a tornado or the probability of observing freezing precipitation vs. not observing freezing precipitation).
The metadata required to describe dichotomous events are inherently simpler than those for categorical events.

**Best Practice:**
*The dichotomous event probability variable should declare the attribute standard_name and have a value that bears some relationship to the dichotomous event.*

.. note::
   We note a lack of standard names that seem appropriate to dichotomous event probabilities.

**Best Practice:**
*The dichotomous event probability variable should declare the attribute OM__observedProperty which takes a value that is a URI.  This URI should point to a generic description of dichotomous event probabilities.  It need not specify the weather element.*

**Best Practice:**
*The dichotomous event probability variable should declare the attribute OM__procedure (or, equivalently, SOSA__usedProcedure) that takes on the form described above for documenting multi-step processes.  This includes a string of tokens that resolve to the names of auxiliary variables that convey additional information in their attributes.  This multi-step procedure documents the steps the data producer followed to create the categorical event probabilities.*

*The units of the dichotomous event probability variable should be unity.  If time bounds are needed, they should be associated with this variable.*

5.3 Applying Conditions to Events
-----------------------------------

Conditions can be applied to any event probability.
They seem to be more common for dichotomous event probabilities than for categorical event probabilities.

Examples include the following:
 - The probability of a severe thunderstorm, given a thunderstorm is occurring
 - The probability of freezing precipitation, given precipitation is occurring

To encode a condition, the data producer adds the appropriate attribute to the variable to convey this information.

**Best Practice:**
*The event probability variable should declare an attribute with a name that conveys the concept of condition.  Ideally, the attribute name will be a URI that resolves to a more complete description.  The value of this attribute will also be a URI that resolves to complete description of the condition.*

5.4  Sample CDL
-----------------

.. note::
   We have adopted the  encoding conventions of netCDF-Classic-LD which can be found at https://github.com/opengeospatial/netCDF-Classic-LD.  This allows us to create attribute names and attribute values that resolve to URIs.

Here we present sample encoding for three weather elements, categorical probabilities of precipitation, probability of .01 inch of precipitation (PoP), and probability of freezing precipitation conditional on precipitation occurring.

First, the categorical probabilities of precipitation...  Note that the OM__observedProperty and units attributes make it clear that we are dealing with event probabilities where the various outcomes are defined by dividing a continuous measurement.  The attribute StatPP__concepts/CatOfContVrbl (itself a URI) identitifies the variable that will describe the categorization process.

::

| //  global attributes:
|  :primary_variables = “mos_categorical_qpf06 mos_pop06 mos_poz categorizationOfQPF06 categorizationOfPoP06”;
|  :bald__isPrefixedBy = "prefix_list";
|
| // Prefix definitions
|  group: prefix_list {
|         :OM__ = "http://www.w3.org/ns/sosa/";
|         :SOSA__ = "http://www.w3.org/ns/sosa/";
|         :StatPP__ = "https://codes.nws.noaa.gov/StatPP/";
|         :StatPPUncert__ = "https://codes.nws.noaa.gov/StatPP/Uncertainty/";
|         :PROV__ = "http://www.w3.org/ns/prov#";
|         :NWP__ = "https://codes.nws.noaa.gov/NumericalWeatherPrediction/";
|    }
|
|  dimensions:
|    nsta = 3018 ;
|    time_06h = UNLIMITED ; // (32 currently)
|    nqpf06_categories = 7 ;
|    npop06_categories = 2 ;
|    time_bounds = 2 ;
|
|  variables:
|    float mos_categorical_qpf06(time_06h,nsta,nqpf06_categories) ;
|      mos_categorical_qpf06:standard_name = "precipitation_amount" ;
|      mos_categorical_qpf06:long_name = "Categorical 6-h Quantitative Precipitation Probability" ;
|      mos_categorical_qpf06:units = "1" ;
|      mos_categorical_qpf06:coordinates = "station_longitude station_latitude" ;
|      mos_categorical_qpf06:missing_value = 9999.f ;
|      mos_categorical_qpf06:bounds = "time_06h_bounds" ;
|      mos_categorical_qpf06:OM__observedProperty = "StatPP__Uncertainty/CatProb" ;
|      mos_categorical_qpf06:SOSA__usedProcedure = "( GFSMOSProbStep1 GFSMOSProbStep2 GFSMOSProbStep3 GFSMOSProbStep4 )" ;
|      mos_categorical_qpf06:StatPPUncert__CatOfContVrbl = "( catgorizationOfQPF06 )" ;
|
|    float mos_pop06(time_06h,nsta) ;
|      mos_pop06:standard_name = "precipitation_amount" ;
|      mos_pop06:long_name = "6-h Propability of Precipitation >= 0.01 inches" ;
|      mos_pop06:units = "1" ;
|      mos_pop06:coordinates = "station_longitude station_latitude" ;
|      mos_pop06:missing_value = 9999.f ;
|      mos_pop06:bounds = "time_06h_bounds" ;
|      mos_pop06:OM__observedProperty = "StatPP__Uncertainty/CatProb" ;
|      mos_pop06:SOSA__usedProcedure = "( GFSMOSProbStep1 GFSMOSProbStep2 GFSMOSProbStep3 GFSMOSProbStep4 )" ;
|      mos_pop06:StatPPUncert__CatOfContVrbl = "( catgorizationOfPoP06 )" ;
|
|    float mos_poz(time_03h,nsta) ;
|      mos_poz:standard_name = "precipitation_amount" ;
|      mos_poz:long_name = "Conditional Probability of Freezing Precipitation" ;
|      mos_poz:units = "1" ;
|      mos_poz:coordinates = "station_longitude station_latitude" ;
|      mos_poz:missing_value = 9999.f ;
|      mos_poz:OM__observedProperty = "StatPP__Uncertainty/DichProb" ;
|      mos_poz:SOSA__usedProcedure = "( GFSMOSProbStep1 GFSMOSProbStep2 GFSMOSProbStep3 GFSMOSProbStep4 )" ;
|      mos_poz:StatPPUncert__DescrOfDichVrbl = "StatPP__Uncertainty/DichProbEvents/FrzgPcpn" ;
|      mos_poz:StatPPUncert__CondEvent = "StatPP__Uncertainty/DichProbEvents/PcpnOccur" ;
|
|   long GFSMOSProbStep1 ;
|      GFSMOSProbStep1:PROV__Used = "NWP__Models/GFS13" ;
|      GFSMOSProbStep1:PROV__Activity = "StatPP__Methods/Geosp/MapProjection" ;
|   long GFSMOSProbStep2 ;
|      GFSMOSProbStep2:PROV__Activity = "StatPP__Methods/Geosp/LinInterp" ;
|   long GFSMOSProbStep3 ;
|      GFSMOSProbStep3:PROV__Used = "StatPP__Data/MOSEqns/GFSMOS05" ;
|      GFSMOSProbStep3:PROV__Activity = "StatPP__Methods/Stat/EvalLSREq" ;
|   long GFSMOSProbStep4 ;
|      GFSMOSProbStep4:PROV__Activity = "StatPP__Methods/QC/ProbQC" ;
|
|   long categorizationOfQPF06;
|      categorizationOfQPF06:OM__observedProperty = "StatPP__Data/Met/Wx/TotalPrecip" ;
|      categorizationOfQPF06:SOSA__usedProcedure = "( catProcQPF06 )" ;
|      categorizationOfQPF06:standard_name = "precipitation_amount";
|      categorizationOfQPF06:units = kg m-2;
|
|   long catProcQPF06 ;
|      catProcQPF06:PROV__Entity = "StatPP__Methods/Categorization/QPF06/7categories" ;
|
|   long categorizationOfPoP06;
|      categorizationOfPoP06:OM__observedProperty = "StatPP__Data/Met/Wx/TotalPrecip" ;
|      categorizationOfPoP06:SOSA__usedProcedure = "( catProcPoP06 )" ;
|      categorizationOfPoP06:standard_name = "precipitation_amount";
|      categorizationOfPoP06:units = kg m-2;
|
|   long catProcPoP06 ;
|      catProcPoP06:PROV__Entity = "StatPP__Methods/Categorization/PoP06/2categories" ;
|
|

::

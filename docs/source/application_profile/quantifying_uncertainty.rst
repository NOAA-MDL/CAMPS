5.1  Event Probabilities
========================

Appendix A includes a proposal to add the transformation event_probability_of_X[_over_Z] to [GCSN] to facilitate the encoding of this concept.  Event probabilities seem to fall into two categories--evaluated and specified.  Here, we use the term evaluated event to describe those events defined by evaluating the value of a continuous variable against one or two limits.  Examples include an air temperature below freezing and a precipitation amount that exceeds some predetermined value.  We use the term specified event to include those events that cannot be readily encoded as evaluated events.  Examples include the occurrence of a tornado or some complex combination of evaluated events.

The following sections recommend Best Practices for a number of common applications in StatPP.  There is considerable overlap among these cases.  An evaluated event probability can be considered a degenerate case of a categorical probability, etc.  Our intent is to facilitate the effective exchange of data with sufficient metadata.  We do not intend to offer a formal partitioning of the problem.

We omit techniques the encode time bounds since these are covered well in the existing CF.  Almost all cases that involve event probabilities will require some specification of valid time periods.

5.1.1  Evaluated Event Probabilities of a continuous variable
-------------------------------------------------------------

 **Best Practice:**  *The attribute event_relation should be defined and contain one of the mathematical relations found Table 1, below.    The attribute event_limit1 (and optionally event_limit2) should be defined and contain the name of a variable of appropriate dimensionality that contains this (these) limit(s).  The variable(s) that contain the limit value(s) should be declared as (an) ancillary variable(s), as needed.*

Table 1 Mathematical relations for evaluated event probabilities
of a continuous variable

+-------------------------+
| > limit1                |
+-------------------------+
| >= limit1               |
+-------------------------+
| < limit1                |
+-------------------------+
| <= limit1               |
+-------------------------+
| > limit1 and < limit2   |
+-------------------------+
| >= limit1 and < limit2  |
+-------------------------+
| > limit1 and <= limit2  |
+-------------------------+
| >= limit1 and <= limit2 |
+-------------------------+

**Note:**  *Limit1 and limit2 are intended to be literal strings.  Ancillary variables and attributes should be used to convey the values of limit1 and limit2.*

5.1.2  Specified Event Probabilities
------------------------------------

Best Practice:  The attribute event_specification should be defined and contain a brief, human-readable description of the event.  The attribute event_reference should also be defined and contain a URI that offers a more extensive description of the event definition.

5.2  Categorical Probabilities of a continuous variable
=======================================================

This case is a straightforward application of existing netCDF-CF conventions.

 **Best Practice:**  *A variable of appropriate dimensionality should be declared and contain the limits of the categories.  If needed, a character array can also be declared that contains values found in Table 1 to further define the categories.  These variables should be declared as ancillary variables.*

5.3  Parameterized Probability distributions of a continuous variable
=====================================================================

Parameterized probability distributions have the potential to convey substantial amounts of information economically.  They also bring unique challenges.  In many cases,  the parameters of the distribution have attributes that are quite different from the attributes of the primary variable.  We propose a scheme where the primary variable conveys attribute information and declares one or more Ancillary Variables that convey the parameter values.

In Appendix A, we propose parameterized_probability_distribution_of_X[_over_Z] as a new transformation.  Also, in Appendix B, we propose probability_distribution_parameter as a new CF standard_name.  This will help distinguish the function of the parameter variables from the primary variable.

 **Best Practice:**  *A primary variable of limited dimensionality should be declared.  This variable will convey the metadata (e.g., units, standard_name, long_name) associated with the stored variable.  Distribution parameter variables will also be declared with appropriate dimensionality.  (In general, all distribution parameter variables will have identical dimensionality.)  The variables that convey the parameters should be declared as Ancillary Variables of the primary variable.  The primary variable should have an attribute declared named distribution_name with a value that names the parametric distribution used.  The primary variable should also have an attribute named distribution_reference with a value that contains a URI that points to an authoritative reference describing the distribution and its parameterization.*

 *Each parameter variable should have an attribute declared named parameter_name with a value that names the parameter as it is named in the authoritative reference.  Parameter variables should have appropriate units.  Often, the units of a probability distribution parameter are ill-defined.  In that case, the parameter variable should be encoded as unitless.*

::

 //  global attributes:
    :primary_variables = “mos_temperature mos_pop06 prob_t”;

 dimensions:
    nsta = 3018;
    period_bounds = 2;
    time = UNLIMITED;

 variables:
    int period_bounds;
      period_bounds.wisps_role = “TM_Period:Beginning TM_Period:Ending”;

    float time(time);
      time:long_name = "time";
      time:standard_name = "time";
      time:units = "hours since 2016-05-05 00:00:00.0";
      time:axis = "T";
      time:wisps_role = “leadTime”;

    float forecast_reference_time;
      forecast_reference_time.long_name = “forecast reference time”;
      forecast_reference_time.standard_name = “forecast_reference_time”;
      forecast_reference_time:units = "hours since 1970-01-01 00:00:00.0";

    float phenomenon_time_instant(time);
      phenomenon_time_instant.long_name = “phenomenon time for instants”;
      phenomenon_time_instant.standard_name = “time”;
      phenomenon_time_instant:units = “hours since 1970-01-01 00:00:00.0”;
      phenomenon_time_instant:wisps_role = “OM_phenomenon_time”;

    float phenomenon_time_period(time, period_bounds);
      phenomenon_time_period.long_name = “phenomenon time for periods”;
      phenomenon_time_period.standard_name = “time”;
      phenomenon_time_period:units = “hours since 1970-01-01 00:00:00.0";
      phenomenon_time_period:wisps_role = “OM_phenomenon_time”;

    float product_completion_time;
      product_completion_time:long_name = “product completion time”;
      product_completion_time:standard_name = “time”;
      product_completion_time:units = “seconds since 1970-01-01
        00:00:00.0”;
      product_completion_time:wisps_role = “OM_resultTime”;

    float product_use_period(period_bounds);
      product_use_period:long_name = “product use period”;
      product_use_period:standard_name = “time”;
      product_use_period:units = “seconds since 1970-01-01 00:00:00.0”;
      product_use_period:wisps_role = “OM_validTime”;

    int mos_procstep1;
      mos_procstep1:LE_ProcessStep = 
      “https://codes.nws.noaa.gov/StatPP/Methods/Geospatial/MapProjection”;
      mos_procstep1:LE_Source =
      “https://codes.nws.noaa.gov/NumericalWeatherPrediction/Models/GFS13”;
      mos_procstep1:LE_Processing.runTimeParameter1 =
 “https://codes.nws.noaa.gov/StatPP/Methods/Geospatial/PolarStereographic”;

    int mos_procstep2;
      mos_procstep2:LE_ProcessStep =
        “https://codes.nws.noaa.gov/StatPP/Methods/Analytical/Smoothing”;
      mos_temperature_procstep2:LE_Processing.runTimeParameter1 = “9”;

    int mos_procstep3;
      mos_procstep3:LE_ProcessStep =
        “https://codes.nws.noaa.gov/StatPP/Methods/MOS”;
      mos_procstep3:LE_Algorithm.citation.edition = 
   “https://codes.nws.noaa.gov/StatisticalPostProcessing/Methods/GFSMOS05”;

    float mos_pop06_bound;
      mos_pop06_bound:standard_name = “precipitation_amount”;
      mos_pop06_bound:units = “kg m-2”;
      mos_pop06_bound:long_name = “precipitation threshold of 0.01 inches”;

    float mos_temperature(time, nsta);
      mos_temperature:standard_name = "surface_temperature";
      mos_temperature:units = "degree_Fahrenheit";
      mos_temperature:long_name = "surface_temperature";
      mos_temperature:coordinates = "time station_latitude
        station_longitude station_elevation";
      mos_temperature:ancillary_variables = “forecast_reference_time
        phenomenon_time_instant product_completion_time
        product_use_period mos_procstep1 mos_procstep2 mos_procstep3”;
      mos_temperature:OM_observedProperty = 
        “http://codes.wmo.int/grib2/codeflag/4.2/0-0-0”;
      mos_temperature:OM_procedure = “(mos_procstep1 mos_procstep2
        mos_procstep3)”;

    float mos_pop06(time, nsta);
      mos_pop06:units = "%";
      mos_pop06:standard_name = 
        "probability_distribution_of_precipitation_amount_over_time";
      mos_pop06:proposed_standard_name =
        “event_probability_of_precipitation_amount_over_time”;
      mos_pop06:long_name = "probability_of_precipitation";
      mos_pop06:coordinates = "time station_latitude station_longitude
        station_elevation";
      mos_pop06:ancillary_variables = “forecast_reference_time
        phenomenon_time_period product_completion_time product_use_period
        mos_procstep1 mos_procstep2 mos_procstep3 mos_pop06_bound”;
      mos_pop06:event_relation = “>= limit1”;
      mos_pop06:event_limit1 = “mos_pop06_bound”;
      mos_pop06:OM_observedProperty = 
        “http://codes.wmo.int/grib2/codeflag/4.2/0-0-0”;
      mos_pop06:OM_procedure = “(mos_procstep1 mos_procstep2
        mos_procstep3)”;

    float prob_t;
      prob_t:ancillary_variables = “prob_t_mean prob_t_variance”;
      prob_t:standard_name = 
        “probability_distribution_of_surface_temperature”;
      prob_t:proposed_standard_name = 
        “parameterized_probability_distribution_of_surface_temperature”;
      prob_t:units = “K”;
      prob_t:distribution_name = “Normal 2”;
      prob_t:distribution_reference = 
        “http://www.probonto.org/ontology#PROB_k0000265”;

    float prob_t_mean(time,nsta);
      prob_t_mean:standard_name = “surface_temperature”;
      prob_t_mean:proposed_standard_name =   
        “probability_distribution_parameter”;
      prob_t_mean:units = “K”;
      prob_t_mean:parameter_name = “mean”;
      prob_t_mean:parameter_reference = 
        “http://www.probonto.org/ontology#PROB_k0000268”;

    float prob_t_variance(time,nsta);
      prob_t_variance:standard_name = “surface_temperature”;
      prob_t_variance:proposed_standard_name =
        “probability_distribution_parameter”;
      prob_t_variance:units = “1”;
      prob_t_variance:parameter_name = “variance”;
      prob_t_variance:parameter_reference = “
        “http://www.probonto.org/ontology#PROB_k0000271”;

 data:
  inches_to_millimeter = 25.4;
  mos_pop06_bound = 0.01 * inches_to_millimeter;

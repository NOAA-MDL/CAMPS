6.  Percentiles
===============

Percentiles are commonplace in StatPP applications to express a forecast of a random variable or to express the relative frequencies of a set of observations.
While the term quantile is more general, the encoding guidelines presented here will concentrate on percentiles.
The term percentile is more commonplace more readily understood by a larger audience.
We note that many quantiles can be expressed as percentiles for encoding purposes.

In gneral, all of the characteristics of a variable (and all of the associated metadata) apply to a percentile of that variable.
E.g., the 90th percentile of a temperature forecast is still a temperature forecast.
The 5th percentile of a set of QPF observations is still a QPF observation.
Metadata concepts such as units, OM__observedProperty, and SOSA__usedProcedure apply to the percentiles as well as they do to the orginal variable.

Here we will introduce two methods of encoding percentile data--a "labeled method" and an "indexed method.""
Both are straightforward and follow the general principles outlined above.

Labeled encding is simpler and preferred for a small number of percentiles.
Say, 5-10 variables.
Labelled encoding becomes unwieldy when 100 or more percentiles are encoded.
Indexed encoding is preferred for these larger cases.

6.1  Labeled Encoding
---------------------

For labled encoding of percentiles, the data producer declares multiple variables, one variable for each percentile rank.
Associated metadata document the concept of quantile and the percentile rank for each variable.

**Best Practice:**

*Percentile variables that are encoded using the labeled encoding technique should declare an attribute PROV__specializaionOf or some similar concept.  This attribute will take on the value of a character array of the form " ( v1 v2 ... vn )".  One of these variables should take on a value that expresses the concept of quantile.  Ideally, both the attribute name and its value(s) will take the form of a URI.*

**Best Pracctice:**

*Percentile variables that are encoded using the labeled encoding technique should declare an attribute with the name StatPPUncert__PrcntlRnk or something similar.  This attribute should take on an integer or floating point value that documents the percentile rank (e.g., 10th, 50th, 99.7th) of the data.*

6.2  Indexed Encoding
---------------------

For indexed encoding, the data producer declares an additional array index that represents the percentile.
A new array with a matching index is also declared, and this array contains the matching percentile rank values.

**Best Practice:**

*Percentile variables that are encoded using the indexed encoding technique should include an array index to represent the precentile.  A new array of appropriate type with a matching index, the percentile rank array, will also be declared.*

**Best Practice**

*Percentile variables that are encoded using the indexed encoding technique should declare an attribute PROV__specializaionOf or some similar concept.  This attribute will take on the value of a character array of the form " ( v1 v2 ... vn )".  One of these variables should take on a value that expresses the concept of quantile.  Ideally, both the attribute name and its value(s) will take the form of a URI.*

**Best Practce**

*Percentile variables that are encoded using the indexed encoding technique should declare an attribute StatPPUncert__PrcntlRnk or some similar concept.  This attribute will take on the value of a character array of the form " ( v1 ) ", where the token v1 is replaced with the name of a variable in the file with appropriate dimensionality that serves as the percentile rank variable.

**Best Practce**

*Percentile rank variables should declare the attribute OM__observedProperty or some similar concept.
The value of this atttribute should express the concept of percentile rank.
Ideally, both the attribute name and value will be URIs.*

6.3 Code Samples
----------------

This CDL fragment shows the metadata associated with a QPF-related variable.
In this case, the data producer created a probability distribution of QPF, captured the 10th, 50th, and 90th percentiles and is now disseminating these three variables.
Because the number of quantiles is small, the data produced used labeled encoding.

|  float qpf06p10(time=1, lead_time=40, ya=1172, xa=798);
|    :_FillValue = -99.99f; // float
|    :least_significant_digit = 2L; // long
|    :units = "kg m-2";
|    :standard_name = "precipitation_amount";
|    :long_name = "Blend QMD 6-Hour Precipitation Amount (10th percentile)";
|    :level = "surface";
|    :missing_value = -99.99f; // float
|    :coordinates = "longitude latitude";
|    :ancillary_variables = "OM__phenomenonTimePeriod OM__resultTime OM__validTime forecast_reference_time leadTime Blend_PrecipProcStep1 Blend_PrecipProcStep2 Blend_PrecipProcStep3 Blend_PrecipProcStep4 Blend_PrecipProcStep5 Blend_PrecipProcStep6 Blend_PrecipProcStep7 Blend_PrecipProcStep8 Blend_PrecipProcStep9";
|    :OM__observedProperty = "StatPP__Data/Met/Wx/TotalPrecip";
|    :PROV__specializaionOf = " ( StatPP__Uncertainty/Qntl ) ";
|    :OM__procedure = "( Blend_PrecipProcStep1 Blend_PrecipProcStep2 Blend_PrecipProcStep3 Blend_PrecipProcStep4 Blend_PrecipProcStep5 Blend_PrecipProcStep6 Blend_PrecipProcStep7 Blend_PrecipProcStep8 Blend_PrecipProcStep9)";
|    :StatPPUncert__PrcntlRnk = 10L; // long
|    :_ChunkSizes = 1U, 14U, 391U, 266U; // uint

The attribute OM__observedProperty shows that this is a QPF variable, and PROV__specializaionOf further qualifies the variable as a quantile.
Finally, the attribute StatPPUncert__PrcntlRnk shows that this is the 10th percentile of the distribution.
(The data producer has chosen to document nine steps as part of OM__procedure.
The standard places no limits on these steps.
Data producers are free to document as few or as many steps as they feel are needed to convey this information to their data consumers.)

This CDL fragment illustrates a similar case, but using indexed labeling.
In this case, the data producer created a probability distribution of QPF, and chose to disseminate the 25th, 50th, 75th, 90th, 95th, and 99th percentiles.

|  float qpf06pctl(time=1, lead_time=40, ya=1172, xa=798, percentile=6);
|    :_FillValue = -99.99f; // float
|    :least_significant_digit = 2L; // long
|    :units = "kg m-2";
|    :standard_name = "precipitation_amount";
|    :long_name = "Blend QMD 6-Hour Precipitation Amount Percentiles";
|    :level = "surface";
|    :missing_value = -99.99f; // float
|    :coordinates = "longitude latitude";
|    :ancillary_variables = "OM__phenomenonTimePeriod OM__resultTime OM__validTime forecast_reference_time leadTime Blend_PrecipProcStep1 Blend_PrecipProcStep2 Blend_PrecipProcStep3 Blend_PrecipProcStep4 Blend_PrecipProcStep5 Blend_PrecipProcStep6 Blend_PrecipProcStep7 Blend_PrecipProcStep8 Blend_PrecipProcStep9
qpf06pctlrk ";
|    :OM__observedProperty = "StatPP__Data/Met/Wx/TotalPrecip";
|    :PROV__specializaionOf = " ( StatPP__Uncertainty/Qntl ) ";
|    :OM__procedure = "( Blend_PrecipProcStep1 Blend_PrecipProcStep2 Blend_PrecipProcStep3 Blend_PrecipProcStep4 Blend_PrecipProcStep5 Blend_PrecipProcStep6 Blend_PrecipProcStep7 Blend_PrecipProcStep8 Blend_PrecipProcStep9)";
|    :StatPPUncert__PrcntlRnk = " ( qpf06pctlrk )"
|    :_ChunkSizes = 1U, 14U, 391U, 266U; // uint
|
|  long qpf06pctlrk(percentile);
|    :OM__observedProperty = "StatPPUncert__PrcntlRnk"
|    :units = 1;
|    :standard_name = "source"
|    :long_name = "Percentile ranks"
|    :missing_value = -99L; //long
|
|  data:
|  qpf06pctlrk = 25, 50, 75, 90, 95, 99 ;

The indexed version of the CDL shares much in common with the labeled version, above.
The variable qpf06pctl is dimensioned with an additional index named percentile, and the attribute StatPPUncert__PrcntlRnk now names a variable, qpf06pctlrk.

The new variable, qpf06pctlrk, is dimensioned percentile to match the last dimension of qpf06pctl.
Qpf06pctlrk is initialized with the six percentile levels noted above.

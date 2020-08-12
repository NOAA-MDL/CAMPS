3.  Sample CDL
==============

3.1  Global attributes
----------------------

We begin with a set of global attributes that describe the file itself.

::

  |   :PROV__Entity = "StatPP__Data/Source/MOSEqnFile";
  |   :PROV__wasGeneratedBy = "StatPP__Methods/Stat/MOSDev";
  |   :DCMI__hasVersion = "StatPP__Methods/Stat/GFSMOS/010501";
  |   :DCMI__creator = "StatPP__Data/Source/MDL";
  |   :PROV__generatedAtTime = "2018-07-25T18:00:00";

::

The W3C standard for provenance (PROV-O) and the Dublin Core Metadata Initiative (DCMI) standard terminology both provide key entries to describe the file and its history.
Entries declare what sort of file this is, how it was generated, the file version, the primary source of its contents, who created it, and when.
Many of these entries are entries in a codes registry where they can be more fully described by the data producer.

3.2  Global or parameter-specific attributes
--------------------------------------------

The following attributes can be used as global attributes or parameter-specific attributes, depending on the operational needs of the data producer.
When they are used as global attributes, they are assumed to apply to all parameters contained in the file.
When they appear as both global and parameter-specific attributes, the parameter-specific values override the global values for that one parameter variable.

::

  |   StatPPTime__SeasBeginDay = 7776000;  // 1970-04-1T00:00:00
  |   StatPPTime__SeasEndDay = 23500800;  // 1970-09-30T00:00:00
  |   StatPPTime__SeasDayFmt = "StatPP__Data/Time/SeasDayFmt/Epch"; Unix epoch time used
  |   StatPPTime__FcstCyc = 720;  // 1970-1-1T12:00:00 or 1200 UTC forecast cycle
  |   StatPPTime__FcstCycFmt = "StatPP__Data/Time/FcstCycFmt/Epch"; Unix epoch time used
  |   StatPPSystem__Status = "StatPP__Methods/System/Status/Opnl";
  |   StatPPSystem__Role = "StatPP__Methods/System/Role/Primary";

::

The first three attributes support a common StatPP practice called "seasonal stratification."
Since a number of NWP biases change seasonally as weather patterns (and their simulation) shift, many StatPP techniques repeat their development phase multiple times with seasonal datasets.
Thus, StatPPTime__SeasBeginDay and StatPPTime__SeasEndDay convey the first and last dates (in any year) these parameters should be used.
StatPPTime__SeasDayFmt conveys the encoding format for these dates.
Similarly, many StatPP techniques stratify their development phase by forecast cycle.
The next two attributes, StatPPTime__ForecastCycle and StatPPTime__FcstCycFmt, convey this concept.

All of these attributes convey a temporal concept that returns with periodicity--either a date that occurs annually or a time that occurs daily.
We represent these values here as Unix times and assign the year, month, and date to the values 1970-1-1, as needed.

.. warning::

   For completeness, we have documented a variety of methods that can be used to encode these dates and times.
   As built, however, the CAMPS software will only process dates and times encoded in epoch format.

The last two attributes reflect the practices of the author's institution.
They are presented here as a pattern that other data producers may choose to emulate.
StatPPSystem__Status tracks the maturity of the parameters as they go through their development life cycle.
It can convey values such as *developmental*, *prototype*, *operational*, and *experimental*.
StatPPSystem__Role is also patterned on a specific institution and technique.
StatPPSystem__Role can take on the values *primary* and *backup*, designating primary and backup MOS equations.
(Primary equations are developed in ways that permit the most recent observation to serve as a predictor; backup equations are developed with that predictor withheld..)

3.3  Parameter variables
------------------------

One or more variables within the file contain the StatPP parameters themselves.
The first example, below, contains the coefficients of a set of MOS equations.
Note that the name of this variable and its dimensionality are not part of the CAMPS standard.
Rather, attributes are used to convey the information needed to successfully interpret the variable's contents.
Thus, the variable name (temp_dew_coefficients) and the names of the dimensions (nLeadTimes, npredictors, npredictands) can all be drawn from the MOS nomenclature, enabling transparency.

::

  |    double temp_dew_coefficients(number_of_stations=2519, nLeadTimes = 1, npredictors = 4, npredictands = 2);
  |      :standard_name = source;
  |      :long_name = "Forecast coefficients";
  |      :PROV__Entity = "StatPP__Data/Source/MOSEqCoef";
  |      :PROV__wasGeneratedBy = "StatPP__Methods/Stat/MOSDev";
  |      :DCMI__hasVersion = "StatPP__Methods/Stat/GFSMOS/Temps201805";
  |      :DCMI__creator = "StatPP__Data/Source/MDL";
  |      :PROV__generatedAtTime = "2018-05-25T18:00:00";
  |      :StatPPSource__OrdrdInpt = " ( Temp_instant_950_21600 Temp_instant_500_21600 WSpd_instant_925_21600 RelHum_instant_500_21600 ) ";
  |      :StatPPSource__OrdrdOutpt = " ( Temp_instant_2_ DewPt_instant_2_ ) ";

::

The first, and perhaps most important, attribute we will discuss is PROV__Entity.
In effect, PROV__Entity helps the data producer convey to the data consumer "what it is."
In this case, it is the coefficients of one or more MOS Equations.
Ideally, the technical information found at StatPP__Data/Source/MOSEqCoef will be sufficient to allow a data consumer to read these data and use them effectively.

The four attributes PROV__wasGeneratedBy, DCMI__hasVersion, DCMI__creator, and PROV__generatedAtTime appear again.
This time, however, they are associated with a single variable.
It is not unusual for operational units to combine forecast parameters from different development phases into a single file.

The attribute StatPPSource__OrdrdInpt plays a special role--it identifies the four predictors that provide input to this set of equations.
As we've seen in other applications, the value StatPPSource__OrdrdInpt names four non-data-bearing variables that appear elsewhere in the file.
The attributes assigned to each of those four variables, provide all the metadata needed to access and use these predictors.

The attribute StatPPSource__OrdrdOutpt plays a complimentary role.
It identifies the two predictands that are forecast by these equations.

Another key parameter associated with MOS equations is named the "equation constant."
Equation constants will have different dimensionality than equation coefficients.
Thus, they are stored in a separate variable, below:

::

  |    double temp_dew_equation_constants(number_of_stations=2519, nLeadTimes = 1, npredictands = 2);
  |      :standard_name = source;
  |      :long_name = "equation constants";
  |      :PROV__Entity = "StatPP__Data/Source/MOSEqConst";
  |      :PROV__wasGeneratedBy = "StatPP__Methods/Stat/MOSDev";
  |      :DCMI__hasVersion = "StatPP__Methods/Stat/GFSMOS/Temps201805";
  |      :DCMI__creator = "StatPP__Data/Source/MDL";
  |      :PROV__generatedAtTime = "2018-05-25T18:00:00";
  |      :StatPPSource__OrdrdOutpt = " ( Temp_instant_2_ DewPt_instant_2_ ) ";

::

Of course, there are a number of similarities to temp_dew_coefficients.
Both variables and their component dimensions are formed in the nomenclature of MOS.
PROV__Entity again declares that this variable contains MOS equation constants.
Much of the metadata is identical to temp_dew_coefficients because both variables were created simultaneously by the same process.
StatPPSource__OrdrdOutpt tells us that we will find equation constants for temperature and dew point.

The following CDL applies these principles to three variables that contain diagnostic information about the MOS development process.
These diagnostics are often stored with the equations themselves.

::

  |    double temp_dew_std_err_est(number_of_stations=2519, nLeadTimes = 1, npredictands = 2);
  |      :standard_name = source;
  |      :long_name = "standard error estimate";
  |      :PROV__Entity = "StatPP__Data/Source/MOSStdErrEst";
  |      :PROV__wasGeneratedBy = "StatPP__Methods/Stat/MOSDev";
  |      :DCMI__hasVersion = "StatPP__Methods/Stat/GFSMOS/Temps201805";
  |      :DCMI__creator = "StatPP__Data/Source/MDL";
  |      :PROV__generatedAtTime = "2018-05-25T18:00:00";
  |      :StatPPSource__OrdrdOutpt = " ( Temp_instant_2_ DewPt_instant_2_ ) ";
  |    double temp_dew_reduction_variance(number_of_stations=2519, nLeadTimes = 1, npredictands = 2);
  |      :standard_name = source;
  |      :long_name = "reduction of variance";
  |      :PROV__Entity = "StatPP__Data/Source/MOSROV";
  |      :PROV__wasGeneratedBy = "StatPP__Methods/Stat/MOSDev";
  |      :DCMI__hasVersion = "StatPP__Methods/Stat/GFSMOS/Temps201805";
  |      :DCMI__creator = "StatPP__Data/Source/MDL";
  |      :PROV__generatedAtTime = "2018-05-25T18:00:00";
  |      :StatPPSource__OrdrdOutpt = " ( Temp_instant_2_ DewPt_instant_2_ ) ";
  |    double temp_dew_multiple_corr_coef(number_of_stations=2519, nLeadTimes = 1, npredictands = 2);
  |      :standard_name = source;
  |      :long_name = "multiple correlation coefficient";
  |      :PROV__Entity = "StatPP__Data/Source/MOSMCC";
  |      :PROV__wasGeneratedBy = "StatPP__Methods/Stat/MOSDev";
  |      :DCMI__hasVersion = "StatPP__Methods/Stat/GFSMOS/Temps201805";
  |      :DCMI__creator = "StatPP__Data/Source/MDL";
  |      :PROV__generatedAtTime = "2018-05-25T18:00:00";
  |      :StatPPSource__OrdrdOutpt = " ( Temp_instant_2_ DewPt_instant_2_ ) ";

::

Encoding MOS forecasts ("bulletins") in CAMPS
=============================================

Model Output Statistics (MOS) products issued by the US National Weather Service (NWS) include a diverse set of weather elements.
Many of these weather elements would be readily recognized by any meteorologist.
Others, however, have been specialized to accommodate NWS operations.
Here, we describe the application of CAMPS data encoding principles to MOS forecasts.

.. sidebar:: Why "bulletins?"

   The original MOS forecasts were disseminated via teletype.  The forecasts were encoded into alphanumeric characters and arranged in rows and columns to facilitate transmission.  A current bulletin can be found at  `this URL, <http://www.nws.noaa.gov/cgi-bin/mos/getmav.pl?sta=KBWI>`_  and a guide for interpretation is : `here. <http://www.nws.noaa.gov/mdl/synop/mavcard.php>`_

   While dissemination technologies have changed radically, many of the weather element definitions have persisted.

In general...
-------------

* Entries for OM__observedProperty should match the general ones used for observations where possible.
* A MOS temperature forecast is still a temperature. It used a specific process and came from a specific source.
* Entries for categorical and discrete probabilities should follow the guidelines documented in the application profile.
* The evaluation of one or more MOS equations is a procedure.
* The version of equations used are documented in a PROV__used attribute.

Once the user is at the point of looking at a forecast bulletin, carrying all of the history of the development process (back to the original model data, before the regression) is probably unnecessary.
An individual MOS netCDF bulletin will contain forecasts of several elements; parameter files for each of these will have been developed/implemented at different times.
Information about the particular MOS “version” can be conveyed via the Registry entry under /statPP/source.
The NCO operational release notes can be linked here.  However, these don’t usually contain much in the way of detailed scientific information about the development process for individual weather elements.
We may or may not want the MOS version entry to be a collection containing entries for each of the elements developed/upgraded with the implementation.


Metadata properties:

One OM_observedProperty for each forecast element.  This should be easy and mostly nailed down already.
PROV_used can point to a Registry entry for the particular MOS “version”.
SOSA_usedProcedure will delineate a sequence of procedure steps.  Some weather elements will be as simple as “take model-forecast values of predictors, evaluate the parameter file, generate forecast values”.  Other elements will need post-processing steps (i.e. T/Td consistency, additive law, etc.), or a categorical forecast generation (threshold evaluation) step.
MSA post-meeting thought:  since the categorical forecast step references what today is a separate parameter file (containing thresholds), is this a second, separate entry for PROV_used?  Or should this information be folded into the Registry entry for the particular MOS version?


Random thoughts, seeking organization...

What should procedures look like for MOS elements?

T, Td, Wspd, WDir, Gust
PROV__Activity = StatPP__Methods/Stat/EvalMLREq
PROV__Used = https://codes.nws.noaa.gov/StatPP/Methods/Stat/MOS/GFSMOS/010501
PROV__Activity = StatPP__Methods/QC/TempQC

MaxT, MinT
NetCDF Cell Methods can express a continual max/min over a span of time.  The details of those spans of time are annoying.  Another solution would be to define a new observedProperty named something like NWSZFPMaxT.  Then, we could code phenomenon times in a simple, sane way, and let the Codes Registry explain all of the silliness.

SOSA__observedProperty = NWSZFPMaxT
PROV__Activity = StatPP__Methods/Stat/EvalMLREq
PROV__Used = https://codes.nws.noaa.gov/StatPP/Methods/Stat/MOS/GFSMOS/010501
PROV__Activity = StatPP__Methods/QC/MOS/EnfTTdCons
PROV__Activity = StatPP__Methods/QC/MOS/EnfTMxMnCons


Categorical probs
Discrete event probs

What's the observed property/procedure for ceiling?

How to handle Max/Min Temps?
We've spent some time on probabilities.  We'll see how well it works.

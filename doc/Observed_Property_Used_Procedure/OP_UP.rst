************************************
Observed Property and Used Procedure
************************************

NetCDF-CAMPS requires the two attributes **standard_name** and **long_name**, which are 
introduced in CF-conventions, to standardize the concepts of what is observed/forecast 
and how it was processed. 

**Standard_name** is a controlled vocabulary (http://cfconventions.org/Data/cf-standard-names/65/build/cf-standard-name-table.html).

**Long_name** is intended to be human-readable.

NetCDF-CAMPS also introduces two additional concepts;
**OM__observedProperty** and **SOSA__usedProcedure**. Our intent is to facilitate data
discovery, provide explicit linkages to widely-accepted standards outside the
atmospheric/oceanic/space weather domains, and use widely-accepted standards to
enhance our metadata. StatPP applications frequently apply complex procedures to
datasets, and this increases the importance of these metadata entries.

Recall that in O&M an observation is an event that results in an estimation of
the value (the result) of a property (*OM__observedProperty*) of some entity
(the feature of interest) using a specified procedure (*SOSA__usedProcedure*).

In simple cases, the OM__observedProperty and SOSA__usedProcedure may seem to
be redundant with standard_name and long_name. That said, StatPP applications
often define parameters (e.g., sine of the day of the year) that are useful in
the development phase, but will not be disseminated. In these instances,
careful use of OM__observedProperty and SOSA__usedProcedure can yield a
number of benefits.

 - It can thoroughly document the origins of a variable.
 - It can enhance data exchange among StatPP development organizations.
 - It can improve the quality and utility of data archives.

OM_observedProperty
===================

All primary variables in a netCDF-CAMPS dataset should have an attribute named
**OM__observedProperty** declared with a value that is a URI. This URI will refer
to a clear description of the property contained in the variable. The URI need
not describe any procedures performed to obtain the results contained in the
variable. The procedure description is better contained in OM__procedure
(SOSA__usedProcedure). Ideally, the URI will be web-accessible.

SOSA_usedProcedure
==================

All primary variables in a netCDF-CAMPS dataset should have an attribute
**SOSA__usedProcedure**, declared with a value of the form “(v1 v2 v3 … vn)”
where n is a non-zero integer. 

The order of tokens should be in the same order that the procedures were performed.

Example:
 - For a single step: :SOSA__usedProcedure = “( firststep )”;
 - For two steps: :SOSA__usedProcedure = “( firststep secondstep )”;
 - For three steps: :SOSA__usedProcedure = “( firststep secondstep thirdstep )”;
 - etc...

The tokens v1, etc. will name ancillary variables which are written to the
netCDF-CAMPS file as separate variables whose attributes describe the procedure. 
The names of these attributes should be taken from conformance class schemas found in PROV.
When used, the attribute PROV__Activity should always appear with a value that
is a URI. This URI will refer to a clear description of the processing step.
Other attributes found in PROV are permitted (e.g., PROV__Used). PROV__Used describes 
little more than the ingest of the data. The first token in SOSA_usedProcdure should
usually have a PROV__Used token.

SOSA__usedProcedure step variables are typed short integer, have descriptive, human-readable 
long names, and have units of unity. Unil a more appropriate standard_name becomes available 
“source” should be used".

Data producers should include sufficient detail in the SOSA__usedProcedure steps
to adequately describe the data contained in the variable and distinguish it
from other, similar variables and otherwise identical variables contained in
other datasets. Judicious use of these attributes can add key metadata to a
netCDF-CAMPS database and facilitate collaboration. SOSA_usedProcedure should only
document what a user has done to the data. If highly processed data is received
from outside the users system OM_observedProperty in the ancillary variable metadata 
that points to a code registry entry that describes the external processing.   

SOSA__usedProcedure should not be used to convey a list of routines that were called. 
If needed, those details can be captured in the various entries in the codes registry.

***************
Attribute Names
***************

In netCDF-CAMPS, attributes based on the ISO and other concepts will have names
that concatenate the prefix, two underscore characters, and the model element
name. The double underscore allows CAMPS to integrate the features of
netCDF-Classic-LD. For example, the attribute based on the model element
phenomenonTime (in the Observations and Measurements package) is named
OM__phenomenonTime. Also, the attribute based on the ontology element
prov:Activity (in the PROV-O ontology) is named PROV__Activity.

In at least one case, the SSN/SOSA vocabulary deviates slightly from OM
(i.e., usedProcedure vs. procedure). The CAMPS encodings described here will use
the OM__ prefix to designate concepts that had their origin in OM. In most cases,
the associated attribute name or value will resolve to a concept hosted within
SSN or SOSA. A different prefix (OM2__ or SSN__ or SOSA__) will be used when a
single CAMPS-encoded file must reference two or more of these resources.

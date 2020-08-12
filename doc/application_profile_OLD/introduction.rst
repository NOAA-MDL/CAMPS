****************
1.  Introduction
****************

.. note::
   CAMPS version 1.0 was built to support an older version of these standards.
   These documents describe a data encoding standard that will be used for CAMPS version 2.0.

NetCDF and the CF conventions have served the atmospheric science community quite well.
Many organizations have applied these frameworks to the problem of StatPP.
Unfortunately, these organizations have settled on a variety of solutions with limited success in interoperability.
This document introduces an application profile of the netCDF-CF conventions that provides additional specificity to improve this interoperability.
An additional benefit will be the assurance that compliant data files contain sufficient metadata to be self-describing for relatively long periods of time.
Best practices are recommended along with CDL code fragments as examples.

We introduce the shorthand netCDF-CAMPS to describe a file that conforms to this application profile.

Appendix A proposes some changes to the `Guidelines for Construction of CF Standard Names <http://cfconventions.org/Data/cf-standard-names/docs/guidelines.html>`_.
In our examples, we illustrate the application of these changes by declaring an attribute named prototype_standard_name as well as the attribute standard_name.
This conveys our intent while maintaining conformity with the current standard.

1.1  NetCDF-CAMPS and other standards/conventions
=================================================

First and foremost, a netCDF-CAMPS file must comply with both the netCDF standard and the associated CF conventions.  

NetCDF-CAMPS tries to standardize nomenclature and its representation in metadata by using pre-existing standards from the International Standards Organization (ISO), Open Geospatial Consortium (OGC), and the World Meteorological Organization (WMO).
NetCDF-CAMPS also leverages emerging work that combines netCDF with linked data, the binary-array-ld (bald; https://github.com/binary-array-ld).
The Reference section, below lists the key standards documents that contributed.

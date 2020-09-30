*************************************
2.  NetCDF-CAMPS files and components
*************************************

.. note::
   CAMPS version 1.0 was built to support an older version of these standards.
   These documents describe a data encoding standard that will be used for CAMPS version 2.0.

The CF conventions recommend the file extension “.nc” and impose no other restrictions on file names.
Similarly, netCDF-CAMPS imposes no further restrictions on variable names or dimensions beyond those established for CF.
Like the CF conventions, most of the requirements for netCDF-CAMPS are focused on the use of attributes, ancillary variables, and auxiliary coordinate variables to adequately describe the metadata associated with StatPP variables.

2.1  Identification of convention
=================================

Similar to CF, we suggest that the global attribute Conventions includes the string “CAMPS-1.0” to indicate compliance with this profile.
Since all files that follow the CAMPS application profile also follow the netCDF CF Conventions, the Conventions attribute should also contain the appropriate CF string.


*************************************
2.  NetCDF-WISPS files and components
*************************************

The CF conventions recommend the file extension “.nc” and impose no other restrictions on file names.
Similarly, netCDF-WISPS imposes no further restrictions on variable names or dimensions beyond those established for CF.
Like the CF conventions, most of the requirements for netCDF-WISPS are focused on the use of attributes, ancillary variables, and auxiliary coordinate variables to adequately describe the metadata associated with StatPP variables.

2.1  Identification of convention
=================================

Similar to CF, we suggest that the global attribute Conventions includes the string “WISPS-0.2” to indicate compliance with this profile.
Since all files that follow the WISPS application profile also follow the netCDF CF Conventions, the Conventions attribute should also contain the appropriate CF string.


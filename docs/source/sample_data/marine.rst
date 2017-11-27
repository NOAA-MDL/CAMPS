Marine Observations
===================

.. only:: format_html
   
    This section describes sample buoy observation output that can be :download:`downloaded here <./reduced_nbd201305.nc>`.
    If you are reading this in a PDF document, then you will need to access a web version to download the sample files.

This sample file contains marine station data from a selection of ~600 fixed data buoys located in the Great Lakes and coastal waters of the US.  The observations were taken during the month of May 2013.

The observations were processed through MDL's quality control (QC) routines.
Notably, the observation time information was removed in that process.
Thus, all time data in this file are at the "top of the hour."
E.g., a METAR whose time was encoded as 1953 (19:50:00 UTC) is stored in this file with the time 20:00:00 UTC.
This is useful for a number of applications in statistical post-processing, but problematic in a number of other ways.

Here’s a CDL fragment for an array of 2-m temperature values.
(Output is captued from the application Panoply.
All atrributes that follow the variable declaration are associated with that variable.)

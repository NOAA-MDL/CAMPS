Mesonet Observations
====================


.. only:: builder_html

   This section describes sample surface observation output that can be :download:`downloaded here <./reduced_mesohre201207.nc>`.
   If you are reading this in a PDF document, then you will need to access a web version to download the sample files.

This sample file contains station data from the NWS National Centers for Environmental Prediction (NCEP) Meteorological Assimilation Data Ingest System (MADIS; httpe://madis.ncep.noaa.gov).
The original MADIS file contained surface observation data from more than 22,000 stations taken during July 2012.

.. note::
   NOTE:  This file was modified from the original to make it smaller and easier to review.
   The original file contained 22,419 unique stations.
   Missing data values were inserted into the meteorological variables for thousands of these stations.
   This reduced the size substantially and maintained the diverse collection of station identifiers and metadata.

The observations were processed through MDL's quality control (QC) routines.
Notably, the observation time information was removed in that process.
Thus, all time data in this file are at the "top of the hour."
E.g., a METAR whose time was encoded as 1953 (19:53:00 UTC) is stored in this file with the time 20:00:00 UTC.
This is useful for a number of applications in statistical post-processing, but problematic in a number of other ways.

Here's a CDL fragment for an array of 2-m temperature values.
(Output is captued from the application Panoply.  All atrributes that follow the variable declaration are associated with that variable.)

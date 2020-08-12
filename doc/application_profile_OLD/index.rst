================================================================================================================================================
Application Profile for Encoding Data in netCDF-CF to inter-operate with the Community Atmospheric Model Post-processing System (CAMPS) v0.2
================================================================================================================================================

.. toctree::
   :maxdepth: 2
   :glob:

   introduction
   files_components
   description_data
   coordinates
   quantifying_uncertainty
   percentiles
   enhancements_construction_standard_names
   proposed_standard_names
   references

The Community Atmospheric Model Post-processing System (CAMPS) is a software infrastructure that supports Statistical Post-processing (StatPP) and is maintained as community code.
This infrastructure includes conventions and tools for data representation as well as software repositories that facilitate the use of these conventions.
The purpose of this document is to propose conventions for encoding binary data in CAMPS.

.. note::
   CAMPS version 1.0 was built to support an older version of these standards.
   These documents describe a data encoding standard that will be used for CAMPS version 2.0.

  NetCDF (CF) is a set of software libraries and self-describing, machine-independent data formats that support the creation, access, and sharing of array-oriented scientific data
  The conventions for climate and forecast (CF) metadata are designed to promote the processing and sharing of netCDF files
  The conventions define metadata that provide a definitive description of what the data represents, and the spatial and temporal properties of the data.
  (Excerpt from the OGC netCDF standards suite web page, http://www.opengeospatial.org/standards/netcdf)

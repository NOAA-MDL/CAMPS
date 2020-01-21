===================================
Towards a new NetCDF-CAMPS Standard
===================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:
   :glob:

   primary_file_format/formats
   camps_metadata_standards/metadata

This document introduces an application profile for CAMPS utilizing  the netCDF-CF
conventions, and other data models, and controlled vocabularies that improve
interoperability within the StatPP community. By following this application profile,
we ensure that CAMPS compliant data files contain sufficient metadata to be
self-describing for relatively long periods of time.  We introduce the shorthand
netCDF-CAMPS to describe a file that conforms to this application profile.

NetCDF-CAMPS tries to standardize the nomenclature and its representation in
metadata by using pre-existing standards from the International Organization of
Standards (ISO), World Wide Web (W3), Open Geospatial Consortium (OGC), and the
World Meteorological Organization (WMO). The reader is encouraged to download
and review **Guidelines on Data Modelling for WMO Codes** (available in English
only from http://wis.wmo.int/metce-uml), especially section 1.6 and chapters
4 and 5. These foundational concepts will be applied to the development of
metadata within CAMPS data files. Chapter 5 describes the WMO Codes Registry.
We note that the NWS has created a Codes Registry at https://codes.nws.noaa.gov,
and the NWS plans to use that registry to support local applications within CAMPS.
Further, the WMO hosts a similar Codes Registry at https://codes.wmo.int.
Both registries are considered authoritative.

Coincidentally, the OGC’s netCDF Standards Working Group (SWG) has been
developing a NetCDF Classic Linked Data encoding standard (NetCDF-LD)
(http://docs.opengeospatial.org/DRAFTS/19-002.html), which combines netCDF with
linked data, the binary-array-ld (bald; https://github.com/binary-array-ld).
Where possible, CAMPS 1.0 complies with this emerging standard.

An Introduction to the Community Atmospheric Model Post-processing System (CAMPS)
=====================================================================================
The Community Atmospheric Model Post-processing System (CAMPS) is a Python-based software package 
that supports Statistical Post-Processing (StatPP) of atmospheric data and is maintained as community code. 
This package includes frameworks for metadata standards, and tools for data representation.

The original vision for CAMPS put priority on achieving the functionality to reproduce a station-based 
`Model Output Statistics (MOS) <https://vlab.ncep.noaa.gov/web/mdl/mos-documentation/>`_ forecast development. 
In its current form, CAMPS has the capability to produce a limited MOS forecast for the variables: 
Temperature, Dewpoint, Daytime Maximum Temperature, and Nighttime Minimum Temperature.

While replicating a *complete* "MOS forecast development" is still a long term goal, the main focus of CAMPS going forward has 
shifted towards supporting the `National Blend of Models (NBM) <https://vlab.ncep.noaa.gov/web/mdl/nbm/>`_.  

As CAMPS matures and makes progress towards fully supporting the NBM, updates will be added to these 
documentation pages accordingly.  

Current Scope of CAMPS:
===========================
- Provide structured metadata for encoding Statistical Post Processing (StatPP) data.
- Provide capability to convert observations and model output to netCDF.
- Provide capability to apply select procedures to data (ex: smoothing, interpolations, etc...).
- Perform a multiple linear regression (MLR), based on the legacy MOS-2000 software.
- Generate forecasts based on MLR output.
- Foster community involvement.
- Provide accessible, documented, robust, and portable code.
- Allow for user created utilities to be easily incorporated into the software (Ex: statistical post-processing techniques, interpolations, atmospheric variable calculations, etc).
- Utilize NetCDF-Linked Data to expand on metadata within CAMPS output files by pointing 
  directly to metadata ontology documentation, as well as codes registries.

.. toctree::
    :maxdepth: 2
    :caption: Contents:
    :glob:

    users_guide
    technical_description
    statPP_background/index
    codes_registry/index





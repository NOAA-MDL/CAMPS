An Introduction to the Community Atmospheric Model Post-processing System (CAMPS)
=====================================================================================
**CAMPS** is a software infrastructure that supports Statistical Post-Processing and is maintained as community code. This infrastructure includes standards and tools for data representation as well as software repositories that facilitate the use of these standards.
This document is intended to describe the goals, standards, and structure for the development and maintenance of CAMPS. It will also serve as a link to a number of other documents that will capture considerably more detail about aspects of CAMPS.

Overall Goals
=============
- Follow NOAA’s standards for Statistical Post-processing (StatPP) of output from Numerical Weather Prediction (NWP) systems.
- Maintain all components of CAMPS as community code.  This implies the following:

  - CAMPS is a free and shared resource with distributed development and centralized support.
  - Ongoing development of CAMPS is maintained under version control
  - Periodic releases, which include the latest in developments of new capabilities and techniques, are made available to the user community.
  - Insofar as policy permits, major organizations (i.e. NOAA) that participate in the CAMPS community and perform StatPP operationally will maintain the currently operational code in a public repository
- Foster community involvement, experimentation, and improvement.
- Promote accessible, documented, robust, and portable code.

.. toctree::
    :maxdepth: 2
    :caption: Contents:
    :glob:

    statPP_background/index
    netcdf_CAMPS_standard
    Netcdf_CAMPS_Structure
    codes_registry/index
    technical/index





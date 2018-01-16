======================================================================================
An Overview of the Weather Information Statistical Post-processing System (WISPS) v0.1
======================================================================================

***********
1.  Purpose
***********

This document is intended to describe the goals, nature, and strategy for the development and maintenance of the Weather Information Statistical Post-processing System (WISPS).  It will also serve as a guide to a number of other documents that will capture considerably more detail about aspects of WISPS.

1.1  Overall Goals
==================

- Ensure that NOAA’s goals for Statistical Post-processing of output from Numerical Weather Prediction (NWP) systems (StatPP) are met.
- Maintain all components of WISPS as community code.  This implies the following:

  - WISPS is a free and shared resource with distributed development and centralized support.
  - Ongoing development of WISPS is maintained under version control
  - Periodic releases, which include the latest in developments of new capabilities and techniques, are made available to the user community.
  - Insofar as policy permits, major organizations (i.e. NOAA) that participate in the WISPS community and perform StatPP operationally will maintain the currently operational code in a public repository
- Foster community involvement, experimentation, and improvement.
- Promote accessible, documented, robust, and portable code.

**********************************
2.  Key Terminology and Background
**********************************

**WISPS** is a software infrastructure that supports StatPP and is maintained as community code.  This infrastructure includes standards and tools for data representation as well as software repositories that facilitate the use of these standards.

**Statistical post-processing (StatPP)** refers to the adjustment of current real-time forecast guidance using the discrepancies noted between past forecasts and observations/analyses.
Past experience has shown that statistical post-processing is capable of modifying real-time NWP guidance that is biased, somewhat unskillful, and unreliable into guidance that is unbiased, much more skillful, downscaled to local conditions, and highly reliable, thus making it suitable for use in decision support with little or no manual modification by forecasters.”  StatPP can also ameliorate deficiencies due to finite ensemble size and infer forecasts for weather elements that are not directly forecast by the NWP system.  (Cf. Hamill and Peroutka, 2016:  High-Level Functional Requirements for Statistical Post-Processing in NOAA.)

For many StatPP techniques, the **Training Phase** or **Development Phase** is a set of processes and software that notes discrepancies between past forecasts and observations/analyses and distills them into a set of parameters.  The Model Output Statistics (MOS) and Kalman Filter techniques both have distinct training phases.  Most bias-correction techniques, however, do not.

All StatPP techniques have a **Production Phase** or **Implementation Phase** which is the set of processes and software that creates output forecasts.

The **Proxy for Truth** is the set of observations/analyses that guides the StatPP process.  The name recognizes the biases and errors that afflict our best observing platforms and analytical techniques.  The proxy for truth is generally accepted to be adequate for the task of StatPP.

**Numerical Weather Prediction (NWP)** generally begins with some form of **Data Assimilation (DA)** which is followed by one or more runs of a **NWP** system.  Additional steps may be required to breed perturbed inputs to facilitate an **ensemble** of **NWP** runs.  The final step of an **NWP** run is named the **Model Post**; this step generally converts output from the specialized coordinate reference systems used in NWP (e.g., spherical harmonics and sigma levels) to more standard coordinate reference systems.  StatPP applications generally work with these standard outputs.

Many StatPP applications use some form of **Statistical Pre-processing** step where NWP output from multiple runs is captured in a **StatPP Archive**.  This **Statistical Pre-processing** captures the data needed for the **Training Phase**.  Often, NWP output is transformed in ways that facilitate statistical training.  In general, if a **Statistical Pre-processing** step is required in the **Training Phase**, that same step will also appear in the **Production Step**.  

A **Training Phase**, if present, will use one or more **Statistical Development Engines** to note discrepancies between past NWP output and a selected **Proxy for Truth**.  These discrepancies are then captured in a set of **StatPP Parameters** which can be used in the **Production Phase**.  

Figure 1, below, attempts to capture some of these concepts in a data flow diagram.

.. image:: StatPPTrainingPhasev0.1.png
    :alt: a data flow diagram of a generic statistical post-processing training phase

A data flow diagram of the training phase of a generic statistical post-processing technique

Figure 2, below, also captures these concepts, but applies them to the **Production Phase**.

.. image:: StatPPProductionPhasev0.1.png
   :alt: a data flow diagram of a generic statistical post-processing implementation phase

A data flow diagram of the implementation phase of a generic statistical post-processing technique

2.1  Metadata Concepts
======================

It is a truism among StatPP developers that they spend 10% of their time in science, 10% in statistics, and 80% in bookkeeping.
Indeed, metadata storage and use are key aspects to any successful StatPP project.
Daunting amounts of data characterize the training phase of many techniques.
Some techniques defer these challenges to the production phase.

WISPS has tentatively adopted NetCDF-CF as format for storing data for both the proxy for truth and StatPP archive.
Other formats (especially HDF) were considered, but the level of support available for NetCDF suggested we use it.  

When designing the metadata portions of WISPS, it seemed wise to build on key concepts that were emerging in widely-recognized Standards Development Organizations (e.g., WMO, OGC, and ISO).
In 2015, the WMO issued *Volume I.3, Annex II to the WMO Technical Regulations, Part D--Representations derived from data models* (Available from the WMO Library at `http://library.wmo.int/pmb_ged/wmo_306-I3_en.pdf <http://library.wmo.int/pmb_ged/wmo_306-I3_en.pdf>`_).
This document is quite focused on the representation of aviation products such as METAR and TAF.
However, it points to a second document that is far more general, *Guidelines on Data Modelling for WMO Codes* (available in English only from `http://wis.wmo.int/metce-uml <http://wis.wmo.int/metce-uml>`_).

The reader is encouraged to download and review the *Guidelines*, especially section 1.6 and chapters 4 and 5.
These foundational concepts will be applied to the development of metadata within WISPS NetCDF files.
Chapter 5 describes the WMO Codes Registry.
We note that the NWS has created a Codes Registry at `https://codes.nws.noaa.gov <https://codes.nws.noaa.gov>`_, and the NWS plans to use that registry to support local applications within WISPS.
Further, the WMO hosts a similar Codes Registry at `https://codes.wmo.int <https://codes.wmo.int>`_.

The technical specifics of data encoding will be deferred to other documents.
Some high-level concepts will be reviewed here.

- Where possible, NetCDF attributes will be named with well-defined ISO concepts (e.g., OM_observedProperty, LE_ProcessStep, OM_phenomenonTime).
- Often, attributes will be assigned Uniform Resource Identifiers (URI) that point to a codes registry.
- Multiple time variables will be declared and populated, as needed, to provide ease of access to data consumers.
- Every effort will be made to document multi-step procedures within the metadata.

This will be prefered over defining a new OM_observedProperty.
The following time-related terms will follow these definitions.  Historically, these terms have not been defined with sufficient precision or used consistently in meteorology.  Ideally, this problem will be addressed early in the lifespan of WISPS.

+---------------------------+----------------------------------------------------+--------------------------------------------+
| The term                  | Means this,                                        | Not this.                                  |
+===========================+====================================================+============================================+
| forecast_reference_time   | The "data time", the time of the analysis from     | the time for which the forecast is valid   |
|                           | which the forecast was made (from the CF Standard  |                                            |
|                           | Name Table).  Must be an instant in time.          |                                            |
+---------------------------+----------------------------------------------------+--------------------------------------------+
| OM_phenomenonTime         | Colloquially, “when the weather happens.”  Can be  |                                            |
|                           | either an instant in time or a period of time.     |                                            |
+---------------------------+----------------------------------------------------+--------------------------------------------+
| OM_resultTime             | When the result (analysis, forecast) became        |                                            |
|                           | available to data consumers.  Must be an instant   |                                            |
|                           | in time.                                           |                                            |
+---------------------------+----------------------------------------------------+--------------------------------------------+
| OM_validTime              | Time of intended use.  Must be a period of time.   | the time for which the forecast is valid   |
+---------------------------+----------------------------------------------------+--------------------------------------------+
| leadTime                  | Length of time (a duration) from                   | an instant in time                         |
|                           | forecast_reference_time to OM_phenomenonTime.      |                                            |
|                           |  Must be a duration.                               |                                            |
+---------------------------+----------------------------------------------------+--------------------------------------------+

************************
CAMPS Metadata Standards
************************

A number of attributes that will be used in netCDF-CAMPS have their origins in
vocabularies that are external to netCDF and the CF conventions. One of the key
motivations in establishing netCDF-CAMPS has been to develop a well-defined
template for incorporating these very rich external vocabularies into files
that conform to netCDF-CF. Since netCDF-CAMPS is intended to support StatPP
specifically, we focus on vocabularies that have been useful for this work in
the past. Sections 3.2.0 through 3.2.3 outline the vocabularies utilized in CAMPS
and our justification for including them.

As a starting point, CAMPS has adopted the use of the International Organization
of Standards (ISO) standard for Observation and Measurements (O&M), ISO 19156.
This introduces a data model and a controlled vocabulary that is useful for the
description of both observations and forecasts of a given StatPP variable within
NetCDF-CF.  Many elements can be easily recognized and the terminology is
designed to apply across disciplines.

CAMPS will also make use of other international standards, which include
additional data models and vocabularies that are web-accessible. The inclusion
of these standards will help simplify atmospheric science applications and
promote more widespread acceptance of CAMPS as “community” code.  These
standards include a data model for the ontology of provenance information
(PROV-O; [PROV]) and the Semantic Sensor Network Ontology [SSN] developed by
the World Wide Web Consortium (W3C). SSN also includes a simple core ontology
named SOSA (Sensor, Observation, Sample, and Actuator).  Many of the key
concepts found in O&M have been integrated into SSN in formats that are hosted
on the web (https://www.w3.org/2015/spatial/wiki/Alignment_to_O%26M).  In many
cases, the W3C vocabularies express these key concepts in a simpler, more
compact format.  In addition, the W3C models also seem a bit more stable and
robust than O&M.

ISO standards
=============

The International Organization of Standards (ISO) is the world’s largest
developer of international standards, they facilitate world trade by providing
common standards between nations.  Today, some 20,000 standards have been set
by ISO.  Of particular importance, the WMO, OGC, and ICAO have all adopted the
use of ISO standards for Observations and Measurements (ISO 19156) and Metadata
(TC211) for key applications. These standards are very relevant for weather
data, so it  seems appropriate for us to illustrate the use of these concepts
in netCDF attribute names.

**OM_Observation:**

It may appear counterintuitive to apply the O&M standard when encoding data that
are forecasts. Despite its name, the O&M class (OM_Observation) is remarkably
well suited to the representation of forecasts as well as observations.
Meteorological examples of forecasts include NWP and StatPP output and Terminal
Aerodrome Forecasts (TAFs).  Meteorological examples of observations include
analyses, METARs, and Pilot Reports

The **OM_Observation** class provides a framework to describe the event of an
observation or measurement. In O&M, an observation is defined as: *“An event
that results in an estimation of the value (the result) of a property
(the observed property) of some entity (the feature of interest) using a
specified procedure”.*

The **procedure** that estimates a temperature value at some
point on the earth could be a human reading a mercury-in-glass thermometer, an
automated observing platform reading a voltage from a sensor, or an NWP system
running on a supercomputer. All three are procedures; all can estimate
temperature values. Thus, one can consider the difference between an observation
and a forecast to be a difference in the estimating procedure used.

Several model elements used in O&M are defined in other ISO geographic
information standards. With the exception of basic data type classes, the names
of Unified Modeling Language (UML) classes (within ISO/TC 211) include a two or
three letter prefix that identifies the relevant international standard and the
UML package in which the class is defined. (Ex: “OM” would be the international
standard and “ObservedProperty” would be the class.  Together this is OM_ObservedProperty).
UML can be thought of as thesuccessor to object-oriented (OO) analysis and design.  An object contains both
data and methods that control the data. The data represents the state of the
object. A class describes an object and also forms a hierarchy to model the
real-world system.

W3C standards
=============

The World Wide Web Consortium (W3C) is an international community of members
that work together to develop web standards.  The W3C has developed two standards
that are useful for StatPP applications. They are the **ontology for provenance
information (PROV-O; [PROV])** and the **Semantic Sensor Network Ontology [SSN]**.
SSN includes a core ontology named **SOSA (Sensor, Observation, Sample, and Actuator)**.
Many of the key concepts found in O&M have been integrated into SSN in formats
that are hosted on the web.

Many of the attributes used in netcdf-CAMPS are rooted in PROV-O and SSN/SOSA.
There are a number of reasons why netCDF-CAMPS makes use of both SSN/SOSA and PROV-O, they are:

- Helps promote a more widespread acceptance of our “community” code by incorporating other data models already in use outside the U.S. and which are hosted on the Web (supported by XML).
- The W3C vocabularies incorporate many key concepts of OM in a simpler, more compact format.

  - This simplicity is especially useful when describing dataset provenance and lineage; OM constructs (LI,LE classes) are very cumbersome when trying to describe multi-step processes.
  - Furthermore, some essential properties that are necessary to accurately describe meteorological and StatPP variables are not available within the O&M vocabulary, specifically with regards to time variables.
- The W3C models seem a bit more stable and robust than O&M.

Integration of user-defined concepts
====================================

Data producers who use NetCDF-CAMPS should give preference to concepts published
by the WMO and other Standards Development Organizations wherever possible.
However, in many cases, data producers will need to identify concepts that fall
exclusively within their provenance. Examples include data processing techniques
that are not widely used, weather element definitions that are not widely
accepted, etc. For these cases, the data producer should define and publish, in
some manner, a number of URIs that identify and document these concepts. The
preferred solution would be for the data producer to make this information
web-accessible and machine readable. The WMO Code Registry (http://codes.wmo.int)
and the NWS Code Registry (https://codes.nws.noaa.gov) both provide these capabilities.

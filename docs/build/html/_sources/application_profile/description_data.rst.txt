***************************
3.  Description of the data
***************************

The reader who is unfamiliar with netCDF-WISPS is encouraged to review WISPS Overview, especially the sections on metadata concepts, as well as the WMO’s Guidelines on Data Modelling for WMO Codes [DMWMO].  These documents provide key foundational information for the conventions that follow.

3.1 Syntax for integration of externally-defined vocabularies
=============================================================

A number of attributes that will be used in netCDF-WISPS have their origins in vocabularies that are external to netCDF and the CF conventions.  Indeed, one of the key motivations in establishing netCDF-WISPS has been to develop a well-defined template for incorporating these very rich external vocabularies into files that conform to netCDF-CF.  Since netCDF-WISPS is intended to support StatPP specifically, the following sections focus on vocabularies that have proven to be useful for this work in the past.

3.1.1 Integration of ISO standards
----------------------------------

The WMO, OGC, and ICAO have all adopted the ISO standards for Observations and Measurements and Metadata for key applications.  This applies to products that have been traditionally described as both observations (e.g., analyses, METARs, Pilot Reports) and forecasts (e.g., NWP and StatPP output, TAFs).  Thus, it seems appropriate for us to illustrate the use of these concepts in attribute names.

  Aside:

  Some find it counter-intuitive to apply the O&M standard when encoding data that are forecasts.  Despite its name, the O&M class named OM_Observation is remarkably well suited to the representation of forecasts as well as observations.  The OM_Observation class provides a framework to describe the event of an observation or measurement.  In O&M, an observation is defined as an event that results in an estimation of the value (the result) of a property (the observed property) of some entity (the feature of interest) using a specified procedure. 

  E.g., the procedure that estimates the temperature value at some point on the earth could be a human reading a mercury-in-glass thermometer, an automated observing platform reading a voltage from a sensor, or an NWP system running on a supercomputer.  All three are procedures; all can estimate temperature values.  Thus, one can consider the difference between an observation and a forecast to be a difference in the estimating process used.

Model element names that are defined within the ISO Geographic information/Geomatics (ISO Technical Committee [TC] 211) series are assigned to UML classes.  The model element names are case sensitive and contain no whitespace.  They use “terminology...designed to apply across disciplines,” and the terminology does not “correspond precisely with any single discipline.”  This leads to some important variations between ISO standard terminology and common meteorological practice.  These variations are noted elsewhere in this document.  The UML classes are associated with packages within the ISO documents.  “By convention within ISO/TC 211, names of UML classes...include a two or three letter prefix that identifies the International Standard and the UML package in which the class is defined.”  E.g., the Observation and Measurements [O&M] class has the prefix OM; the Lineage class [MD1 and MD2] has the prefix LI; and the Extended Lineage class has the prefix LE.  Examples of model element names include phenomenonTime, procedure, and Source.  We note that capitalization patterns seem to vary somewhat among the documents.

In netCDF-WISPS, attributes based on these concepts will have names that concatenate the prefix, a single underscore character, and the model element name.  Thus, the attribute based on the model element phenomenonTime (in the Observations and Measurements package) is named OM_phenomenonTime.

3.1.2 Integration of NetCDF-U and Probonto concepts
---------------------------------------------------

The OGC published a Discussion Paper named NetCDF Uncertainty Conventions (NetCDF-U) in 2013 [NCU].  The document did not progress past a discussion paper, but a number of the concepts presented seem to be useful to netCDF-WISPS.  The NetCDF-U paper makes references to a project named UncertML to provide an authoritative ontology for probability terms.  As of this writing (February 2017), UncertML appears to be unsupported.  As an alternative, we have chosen to use the ontology of probability distributions named Probonto [PO].  Documentation is available for download at this URL.  The European Bioinformatics Institute hosts an Ontology Lookup Service (OLS; http://www.ebi.ac.uk/ols/ontologies/probonto) that provides online access to Probonto.  

3.1.3 Integration of concepts defined by data producers
-------------------------------------------------------

In many cases, data producers will need to identify concepts that fall exclusively within their provenance.  Examples include data processing techniques that are not widely used, weather element definitions that are not widely accepted,  etc.  For these cases, the data producer should define and publish, in some manner, a number of URIs that identify and document these concepts.  One preferred solution, of course would be for the data producer to make these data web-accessible and machine readable.  The WMO Code Registry (http://codes.wmo.int) and the NWS Code Registry (https://codes.nws.noaa.gov) both provide these capabilities.

3.1.4 Integration of vocabularies controlled by WMO
---------------------------------------------------

Data producers who use NetCDF-WISPS should give preference to concepts published by the WMO wherever possible.

3.2 Primary and ancillary variables
===================================

We quote here from NCU:

  A netCDF file typically contains several variables. Some of these may depend on others, i.e. contain ancillary information referred to or qualifying concepts encoded by other variables...

  Dually, netCDF-U files may declare a primary_variables global attribute, whose value is a white-separated list of variable identifiers.

  The intended use of the primary_variables attribute is to support applications in directly accessing their presumable data of interest, particularly since netCDF-U files are likely to contain a large number of ancillary variables, as in the example below.

The sections below will describe a number of best practices that involve ancillary variables and auxiliary coordinate variables.  Most netCDF-WISPS files will contain many ancillary variables that are used to fully describe the complexities of time, properties, and procedures used.  This makes the use of the primary_variables global attribute especially useful.

  **Best Practice:**  *A netCDF-WISPS file should declare a global attribute named primary_variables and assign it the value of a whitespace-separated list of variable identifiers.  This attribute will help data consumers identify presumable data of interest.*

::

 //  global attributes:
    :primary_variables = “mos_temperature mos_pop06”;

3.3  Observed property and procedure
====================================

The CF conventions introduce the attributes standard_name and long_name to standardize the concepts of what is observed/forecast and how it was processed.
The standard_name is a controlled vocabulary, and long_name is intended to be human-readable.
NetCDF-WISPS maintains these two attributes and introduces two additional concepts--OM_observedProperty and OM_procedure.
Our intent is to facilitate data discovery, provide explicit linkages to widely-accepted standards outside the atmospheric/oceanic/space weather domains, and uses widely-accepted standards to enhance our metadata.
StatPP applications frequently apply complex procedures to datasets, and this increases the importance of these metadata entries.

OM_observedProperty and OM_procedure
------------------------------------

The O&M definitions of OM_observedProperty and OM_procedure are quite abstract.
Rather than quote them here, we recall that in O&M an observation is an event that results in an estimation of the value (the result) of a property (OM_observedProperty) of some entity (the feature of interest) using a specified procedure (OM_procedure).
We declare attributes with the names OM_observedProperty and OM_procedure and assign them values that resolve to URIs that contain complete information.
(Ideally, the URIs will be web-accessible as well.  We note that many of the WMO code tables for GRIB and BUFR are hosted on the web at http://codes.wmo.int.)

In simple cases, the OM_observedProperty and OM_procedure may seem to be redundant with standard_name and long_name.
That said, StatPP applications often define parameters (e.g., sine of the day of the year) that are useful in the development phase, but will not be disseminated.
In these instances, careful use of OM_observedProperty and OM_procedure can yield a number of benefits.

- It can thoroughly document the origins of a variable.
- It can enhance data exchange among StatPP development organizations.
- It can improve the quality and utility of data archives.

  **Best Practice:**  *All primary variables in a netCDF-WISPS dataset should have an attribute named OM_observedProperty declared with a value that is a URI.  This URI will refer to a clear description of the property contained in the variable.  The URI need not describe any procedures performed to obtain the results contained in the variable.  The procedure description is better contained in OM_procedure, below.  Ideally, the URI will be web-accessible.*

  **Best Practice:**  *All primary variables in a netCDF-WISPS dataset should have an attribute named OM_procedure declared with a value of the form “(v1 v2 v3 … vn)” where n is a non-zero integer.  The tokens v1, etc. will name ancillary variables whose attributes describe the numbered steps of the procedure.  The names of these attributes should be taken from MD1 and MD2.  The attribute LE_ProcessStep should always appear with a value that is a URI.  This URI will refer to a clear description of that processing step.  Other attributes found in MD1 and MD2 are permitted (e.g., LE_Source, LI_ProcessStep.rationale, LI_ProcessStep.dateTime, LE_Processing.softwareReference, LE_Algorithm.citation.edition, LE_Algorithm.citation.editionDate, LE_Processing.runTimeParameters).*

Data producers should include sufficient detail in the OM_procedure steps to adequately describe the data contained in the variable and distinguish it from other, similar variables and otherwise identical variables contained in other datasets.
Judicious use attributes can add key metadata to a netCDF-WISPS database and facilitate collaboration.

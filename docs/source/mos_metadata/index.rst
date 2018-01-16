Metadata Guidelines for MOS Datasets
====================================

The following guidelines were developed to help developers apply WISPS metadata principles to the practical problem of encoding data that support a MOS system.
They are presented here, hoping they will prove useful to other groups who deal with similar problems.

#.  In OM_procedure, we only document what we do.
    If we received highly-processed data from outside our system, OM_observedProperty can be set to a code registry entry that describes the external processing.

#.  No blank OM_procedures.  
    There must be at least one step.

#.  The first step in OM_procedure describes little more than the ingest of the data.

#.  The first step in OM_procedure should have an LE_Source. 
    It documents where we accessed the data.

#.  Here's the syntax for OM_procedure string:

    * One step :OM_procedure  = “( firststep )”;

    * Two step :OM_procedure  = “( firststep,secondstep )”;

    * Three step :OM_procedure = "( firststep,secondstep,thirdstep )";

    * ...

#.  OM_procedure step variables are typed short integer, have descriptive,
    human-readable long names, have units of unity, and have the standard name “source."
    (It isn't the best fit, but it's the best we could find.)

#.  OM_procedure is used by the data producer to tell the data consumer
    what happened to the data at a conceptual level.
    OM_procedure should not be used to convey a list of routines that were called.
    If needed, those details can be captured in the various entries in the codes registry.

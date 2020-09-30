Metadata Guidelines for MOS Datasets
====================================

The following guidelines were developed to help developers apply CAMPS metadata principles to the practical problem of encoding data that support a MOS system.
They are presented here, hoping they will prove useful to other groups who deal with similar problems.

#.  In SOSA__usedProcedure, we only document what we do.
    If we received highly-processed data from outside our system, OM_observedProperty can be set to a code registry entry that describes the external processing.

#.  No blank entries for SOSA__usedProcedure.
    There must be at least one step.

#.  For observations and NWP output, the first step in SOSA__usedProcedure describes little more than the ingest of the data.

#.  The first step in SOSA__usedProcedure should usually have a PROV_used.
    It documents where we accessed the data.

#.  Here's the syntax for SOSA__usedProcedure string:

    * One step :SOSA__usedProcedure  = “( firststep )”;

    * Two step :SOSA__usedProcedure  = “( firststep secondstep )”;

    * Three step :SOSA__usedProcedure = "( firststep secondstep thirdstep )";

    * ...

#.  SOSA__usedProcedure step variables are typed short integer, have descriptive,
    human-readable long names, have units of unity, and have the standard name “source."
    (It isn't the best fit, but it's the best we could find.)

#.  SOSA__usedProcedure is used by the data producer to tell the data consumer
    what happened to the data at a conceptual level.
    SOSA__usedProcedure should not be used to convey a list of routines that were called.
    If needed, those details can be captured in the various entries in the codes registry.

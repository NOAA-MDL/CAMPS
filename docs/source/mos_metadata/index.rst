Metadata Guidelines for MOS Datasets
====================================

The following guidelines were developed to help developers apply WISPS metadata principles to the practical problem of encoding data that support a MOS system.
They are presented here, hoping they will prove useful to other groups who deal with similar problems.

#.  In OM_procedure, we only document what we do.
    If we received highly-processed data from outside our system, OM_observedProperty can be set to a code registry entry that describes all of that.

#.  No blank OM_procedures.  
    There must be at least one step.

#.  The first step in OM_procedure says little more than we got it.

#.  The first step in OM_procedure should have an LE_Source. 
    It says where we found the data.

#.  Here's the syntax for OM_procedure string:

    * One step :OM_procedure  = “( firststep )”;

    * Two step :OM_procedure  = “( firststep,secondstep )”;

    * Three step :OM_procedure = "( firststep,secondstep,thirdstep )";

#.  Step variables are typed short integer.

#.  Step variables have long names of the form “Step #1”.

#.  Step variables all have the standard name “source”.
    (It isn't the best fit, but it's the best we could find.)

#.  OM_procedure is where the data producer tells the data consumer what happened to the data.
    It doesn’t matter how many different routines were called.
    If needed, those details can be captured in the codes registry.

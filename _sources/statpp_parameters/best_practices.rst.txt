2.  Best practices for encoding parameter files
===============================================

  **Best Practice** *Files that potentially contain parameters from more than one development phase should contain global attributes that describe the origin of the file itself.  Some useful attributes include PROV__Entity, PROV__wasGeneratedBy, DCMI__hasVersion, DCMI__creator, and PROV__generatedAtTime.*

  **Best Practice** *Parameters that are used in StatPP and the names of their dimensions should have names that are drawn from the nomenclature of the technique.*

  **Best Practice** *All parameter variables should include the attribute PROV__Entity or something similar that indicates the nature of the variable and its use.  Ideally, both the attribute name and value will be web-referencible URIs.*

  **Best Practice** *Other useful attributes for parameter variables include PROV__wasGeneratedBy, DCMI__hasVersion, DCMI__creator, and PROV__generatedAtTime.*

  **Best Practice** *Testing for new Sphinx script*

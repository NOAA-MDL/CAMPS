*******************************
Primary and Ancillary Variables
*******************************

NetCDF files often contain a large quantity of variables.  These variables
sometimes depend upon other variables, often referred to as **ancillary variables**.
Because of this, NetCDF-CAMPS requires a global attribute called **primary_variables**
to be declared. By declaring primary variables we make it easy to differentiate
between the main variables from a large data file vs the ancillary variables
that are mostly meant to describe aspects of the primary variables.

**Primary_variables** is a list, separated by white space, of variable identifiers.
These primary variables make accessing data of interest more streamlined,
especially when a file contains a large number of ancillary variables.

**Example:**

::

|  //  global attributes:
|
|     :primary_variables = "mos_temperature mos_pop06";

Section 4 describes a number of requirements and best practices
that involve ancillary variables and auxiliary coordinate variables. Most
netCDF-CAMPS files will contain many ancillary variables that are used to fully
describe the complexities of time, properties, and procedures used. This makes
the use of the primary_variables global attribute especially useful.

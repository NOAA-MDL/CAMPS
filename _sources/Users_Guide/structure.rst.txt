************************
CAMPS Package Structure
************************

**camps/camps/core**

Contains code that defines a Camps_data object. Also stored here are composite classes such as Time and Location, along with I/O modules. 
Additionally, the directory with data conversion modules resides within core.

**camps/camps/core/data_conversion/grib2_to_nc**

Grib2 to netCDF conversion code.

**camps/camps/core/data_conversion/marine_to_nc**

Marine buoy observations to netCDF code.

**camps/camps/core/data_conversion/metar_to_nc**

Metar observations to netCDF code. Also includes QC.

**camps/camps/scripts**

This contains all of the driver scripts. Running all driver scripts constitutes a “CAMPS development”.  
All scripts require a control file to be used as an argument when running the script.

There are six driver scripts in a CAMPS development:

    1. grib2_to_nc_driver.py
    2. Metar_driver.py
    3. Marine_driver.py
    4. Mospred_driver.py
    5. equations_driver.py
    6. forecast_driver.py

**camps/camps/registry**

Contains all the example control files for the various drivers. Also, contains several configuration files. 

The registry directory in CAMPS can be broken down into 4 categories of files:

1. Control files for each driver script
    a. metar_control.yaml
    b. marine_control.yaml
    c. grib2_to_nc_control.yaml
    d. mospred_control.yaml
    e. equations_control.yaml
    f. forecast_control.yaml
    g. graphs.yaml - this controls the graphing functions held within the GUI directory.  This feature is currently being updated.

2. Configuration files, aiding in various aspects of the CAMPS development process
    a. netcdf.yaml - Serves a comprehensive list of accepted variables within CAMPS.  A user must modify to this configuration file using the correct formatting, to add a new supported variable to CAMPS.
    b. constants.py - A collection of constants and unit information used within CAMPS.
    c. marine_to_nc.yaml - key/value pairs that decode marine txt files for the desired variables.
    d.  nc_to_metar.yaml - key/value pairs that decode metar txt files for the desired variables.
    e. pred.yaml - Configuration file that informs CAMPS which predictors, predictands and leadtimes to process, and what procedures to apply. 
    f. predictands_graphs.yaml - This configures graph features for predictands, this is part of the graphing feature that is currently being updated.
    g. predictors_graphs.yaml - This configures graph features for predictors, this is part of the graphing feature that is currently being updated.
    h. procedures.yaml - A comprehensive list of accepted procedures within CAMPS.  A user must modify this configuration file, using the correct formatting, to add a new supported procedure to CAMPS.

3. List and table files, with station information, which may or may not be of use to the user.  Each user may decide which station information they wish to use.  
For example, the file “short.lst” is a small subset of stations often used by CAMPS developers for testing.  Alldevsites.lst is a grouping of all stations from alldevsites.tbl.  A user could develop their own desired station list, as was done with short.lst.  As long as the station information exists in the .tbl file specified in the driver script control file, then it should work.

4. Util.py is a utility module that aids the CAMPS software in interfacing with yaml files.  

**camps/camps/StatPP/regression**

Contains the modules used for regressions.  Currently there is only one multiple linear regression module.  

**camps/camps/gui**

Various modules used to display data are here.  The modules in this directory are currently broken and will be fixed in a subsequent release of the software.

**camps/camps/mospred**

Contains modules that aid in the processing, and calculation, of predictors and predictands (ie. mospred_driver.py).

Examples of mospred support modules would be smooth.py and interp.py.  These modules contain procedures for smoothing and interpolating gridded model data onto stations.

.. note:: For those familiar with MOS-2000, the functionality of this driver script is essentially equivalent to u201.  

**camps/camps/libraries/mathlib**

Contains modules used when calculating new predictors/predictands. Modules contained here are largely used during the mospred (u201 equivalent) step in a CAMPS development.

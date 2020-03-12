# Version 1.0.0 January 20, 2020

First release.  CAMPS is a software infrastructure that supports Statistical Post-Processing (StatPP) and is maintained as community code. CAMPS currently offers the ability to replicate a limited Model Output Statistics (MOS) 2000 development.  Currently, CAMPS only produces forecasts for the following predictands; 2 meter Temperature, 2 meter Dew Point, Daily Maximum Temperature, and Nighttime Minimum Temperature.  Additional limitations such as; functional regressions, interpolations, and accepted map projections also exist.

CAMPS provides a structured method of encoding formatted metadata for StatPP.  It aids in processing predictands from observational data and predictors from model output.  CAMPS offers modules for converting observational data in ascii format (METAR and Marine data) and model output in Grib2 format (GFS data) to netCDF.

## Current package breakdown:

* __camps/core__: Where the module that defines the Camps_data object is held. Also stored here are composite classes such as Time and Location, along with I/O modules. Additionally, the directory with data conversion modules resides within core (camps/core/data_conversion).
	* __camps/core/data_conversion__: Directories where data conversion modules are held.
		* __camps/core/data_conversion/grib2_to_nc__: Modules for grib2 conversion to netcdf.
		* __camps/core/data_conversion/metar_to_nc__: Modules for METAR to netcdf conversion.
		* __camps/core/data_conversion/marine_to_nc__: Modules for Marine data to netcdf conversion.
* __camps/registry__: Contains all the example configuration/control files for the various drivers.
	* __camps/registry/db__: Functions that are used to access and interact with the sqlite3 database are here. The database stores all accepted variables and their metadata and is updated upon each reading or writing of a new netcdf file.
* __camps/scripts__: Contains all the driver scripts required to perform a full CAMPS development.
* __camps/StatPP/regression__: Code used for the multiple linear regression is held here.
* __camps/gui__: Various GUIs and modules used to display data are here.  GUI and display features are not fully functional currently.
* __camps/mospred__: Contains all modules that support the capabilities of the MOS-200 u201 equivalent code. These modules aid in creating new predictors and predictands – typically from model and observational output. They apply procedures to the variables, such as smoothing and interpolating and organize the variables into appropriate dimensions.
* __camps/libraries/mathlib__: Modules used when creating new predictors/predictands are here. These are largely used during the mospred (u201 equivalent) step in a CAMPS development.

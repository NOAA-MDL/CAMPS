# Version 1.1.0 September 30, 2020
Minor release

## Main Features:
* Python 2 to 3 conversion (3.6 or greater)
* grib2_to_nc now supports Lambert Conformal, Polar Stereographic, Mercator, and regular latitude-longitude coordinate systems.
	* GRIB2 Grid Definition Section metadata is now being converted into CF and PROJ metadata.
* Components metadata feature
	* A new metadata attribute called __wasGeneratedBy__ has been added to primary variables metadata where appropriate.This attribute denotes primary variables used in the  calculation of the new primary variable.  
Extra component information can be written to the mospred_driver output file. Set preference (True/False) in mospred_control.
		* If set to True then the variables used in the calculation of other variables will be written separately to the file with their original (before any procedures applied) metadata information ONLY included.  
* New feature for equations_driver which writes out an easier to decipher summary from equations_driver, denoting which predictors are chosen when generating equations and their coefficients.  Also optional, set preference in equations_control.
* Expanded grid-to-station interpolation schemes.
	* bilinear
	* biquadratic
	* budget
	* nearest-neighbor
* Addition of grid binary process and associated metadata.
* Several changes to allow for more flexible input/output options for driver scripts.
	* Allow for multiple input and output files for mospred_driver and forecast_driver.  Functionality already existed for equations_driver.
	* Allow for multiple date ranges to be set for mospred_driver.  Equations_driver already had this functionality.
* Updated the equation parameters in equations_control to only include those that are used, and denote those that are not yet used.  Some code correction done to ensure these are being used properly.
* The beginning of a major metadata restructuring.
	* Added unique calculation procedures in procedures.yaml, with pre-set metadata information to be encoded in output files.
	* Added new metadata attribute __wasInformedBy__ to denote procedures applied to a specific variable, that were performed prior to the current iteration of: read, process variables, write. This is usually done by running a driver script.

## Bug Fixes:
* Adding all applied procedures to primary variable names, with the exception of variable creation calculations.
* Fixed issue in interp.py that resulted in incorrect distances between grid and data points for bilinear interpolation 
* Fixed an issue for budget interpolation where the grid coordinates for a station were not being computed correctly, leading to bad interpolation values.   

## Known Issues:
* GUI graphing modules have errors.  Display.py may work (untested) if Basemap and Basemap-data-hires are installed.  
* Current netcdf.yaml has errors in paths leading out to NWS codes registry and in CF standard names.  An updated version will be pushed out soon.  Updates will be somewhat frequent as more CF standard names are submitted and approved to the CF standard name table.
* Some metadata prefixes used for NetCDF-Linked Data are incorrect in our output files.  These will be fixed/updated when the full CAMPS metadata restructuring is complete.

# Version 1.0.2 May 12, 2020
Patch release

## Main Features:
* Graphing module updates
* Minor bug fixes

__Graphing module updates:__
* The graphing module in camps/gui was not fully functional before.  These changes make it possible to produce numerous plots from METAR_to_nc output and Mospred_driver output (for predictors).
* Made graphs.py into a driver script and added it to setup.py to make it a console script so it can run outside of a python interface.

__Minor bug fix details:__
* Fixed issue in Time.py with result time during 00Z-01Z hour.
* Fixed a couple issues regarding get_source module.  More to come with this.
* Small spelling error in plr_new.py
* Change in netcdf.yaml to support NAM data 


# Version 1.0.1 March 17, 2020
Patch release.

## Main Features:
* Minor bug fixes
* Some additional in-code documentation updates
* Addition of RELEASE_NOTES.md and update to README.md

__Minor bug fix details:__
* Small fix to budget interpolation
* Bilinear introplation fixes.
    1) Calculates dx and dy after conversion to indices
    2) Aligning handling of edge of grid with mos2k methods
* Removed unnecessary stations input argument in plr_new.main_camps
* Fixed typo in plr_new that was causing issues
* Fixes to Time.py for  handling of naming variables with otherwise identical names.  Removed period information for dimension variable names.
* Additional fix to PhenomenonTimePeriod variable duplicate naming convention with wrong period information appended to variable

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

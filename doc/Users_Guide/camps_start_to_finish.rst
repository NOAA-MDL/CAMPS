**********************************************
CAMPS Forecast Development - start to finish
**********************************************

To run a CAMPS development, aside from the initial import step, there is no need to interact directly with Python.  
CAMPS makes use of a feature called “console scripts”, which allows a user to run the driver scripts directly from the command line.

Each CAMPS driver script has a subsequent console script: 

* metar_driver.py –> *camps_metar_to_nc* 
* marine_driver.py –> *camps_marine_to_nc* 
* grib2_to_nc_driver.py –> *camps_grib2_to_nc* 
* mospred_driver.py –> *camps_mospred* 
* equations_driver.py –> *camps_equations* 
* forecast_driver.py –> *camps_forecast*

Input files for driver scripts have metadata and format requirements. When using CAMPS interactively, 
the same metadata requirements still exist, but input file requirements could be circumvented. 
If a file is not read using the internal CAMPS reader module, the user could still instantiate a Camps_data object, 
populate it with data, and add the required metadata.  

CAMPS driver scripts require formatted input files. 
While the sources of input data are currently somewhat limited, as the software matures, additional sources 
and flexibility of input data will be added. In the spirit of being a community, open source, software package, 
CAMPS is being designed so that users can easily add their own features if desired. This could include additional data conversion methods.

Every driver script in CAMPS will have an accompanying control file(s) that configures certain aspects of the associated driver script. 
Without the appropriate control file(s) passed as an argument, CAMPS software will error out.  

After installation, template control files can be found in the automatically generated directory:  ``$HOME/.camps/control``

They can also be viewed in the `CAMPS Github Repository <https://github.com/NOAA-MDL/CAMPS/tree/master/camps/registry>`_ 
in the registry directory.

A CAMPS forecast development can be broken into 4 steps:

Step 1: Data conversion
*************************

To start a CAMPS development, you’ll need to convert observation and model data into CAMPS compliant NetCDF files, and apply quality 
control where necessary.

.. note:: There is no order required for converting data.

**METAR observations:**

MDL Hourly Table Text Files (METAR) are ASCII text, fixed-width, and colon-delimited. 
The data are decoded from METAR reports and a first-pass quality control is performed.

Go to ``$HOME/.camps/control/metar_conrol.yaml`` to view an example control file. 

Then execute the console script, providing the control file as standard input.
::

    $ camps_metar_to_nc /path/to/controlfile/metar_control.yaml

.. note:: For more information on METAR reports, see sections A-D (pages 13.1 to 13.13) of chapter 13 in 
          the following office note document: https://www.weather.gov/media/mdl/TDL_OfficeNote00-1.pdf

**Marine observations:**

NBDC QC Marine Observations Text Files are ASCII text , fixed-width, and colon-delimited. These files are 
from the National Buoy Data Center (NBDC) and are quality controlled by NBDC.

Go to ``$HOME/.camps/control/marine_conrol.yaml`` to view an example control file.

Then execute the driver script:
::

    $ camps_marine_to_nc /path/to/controlfile/marine_control.yaml

**Model data:**

Model data will also need to be processed and converted to NetCDF. The input file must only contain 
GRIB2 Messages that the user wishes to convert to NetCDF. For now, grib2_to_nc_driver only 
accepts GRIB2 data that has already been filtered by level, and the GRIB2 Messages Grid Definition 
Template must be one of the acceptable coordinate systems. 

Currently accepted projections/grids:
    a. Lambert Conformal 
    b. Polar Stereographic 
    c. Mercator
    d. Regular Latitude/Longitude 
  
We recommend wgrib2 (https://www.cpc.ncep.noaa.gov/products/wesley/wgrib2/) to filter and interpolate GRIB2 Messages 
outside of CAMPS. 

The ability to do filtering and grid-to-grid interpolation internally, within CAMPS, is currently under development.

Once again, create your control file based on the 
`provided template <https://github.com/NOAA-MDL/CAMPS/blob/master/camps/registry/grib2_to_nc_control.yaml>`_. 
``$HOME/.camps/control/grib2_to_nc_control.yaml``

Run the console script:
::

    $ camps_grib2_to_nc /path/to/controlfile/grib2_to_nc_control.yaml
  
Step 2: Data Processing
************************* 

During this step, the user will choose what predictors and predictands to process and/or derive, and what procedures to apply.
Input files must be in NetCDF-CAMPS format, and have the necessary metadata. The source of this input data will more than likely 
be the output files produced by grib2_to_nc_driver, Metar_driver, and Marine_driver.
 
Currently CAMPS only interpolates from select map projections, to stations.  The ability to process gridded 
predictors is being developed for a future release. Mospred_driver can be run for processing predictors and/or 
predictands. Be sure to specify which (or both) you want to run for in the control file. 

.. note:: Reminder that for a linear regression, predictand is the dependent variable, and the predictor is the independent variable.

Inside the control file for this driver script, paths to other input and control files should be provided. 
The template control file itself ``$HOME/.camps/control/mospred_conrol.yaml`` should provide adequate instruction for proper configuration.  

.. note:: In mospred_control.yaml, of unique importance is the “pred_file” declaration. The pred_file provided should contain information about the predictors and predictands for the current development. See the template control file “pred.yaml” for more information on configuration.

::

    $ camps_mospred /path/to/controlfile/mospred_control.yaml

Step 3: Generate equations
****************************

Now we’re ready for the regression. The control file $HOME/.camps/control/equation_conrol.yaml will give an example of how to tune regression parameters.  
You will again specify the predictors and predictands you want to generate equations for by specifying the path to your “pred_file”.

.. note:: Required input files are the output files from Mospred_driver.

Execute the driver script::

    $ camps_equations path/to/controlfile/equations_control.yaml

Step 4: Generate Forecast
***************************

Finally, we will want to generate some forecast output and apply basic consistency checks.

.. note:: Required input files are the output files from Mospred_driver and Equations_driver.

The template control file to follow:
:: 

    $HOME/.camps/control/forecast_control.yaml

And the driver,
::

    $ camps_forecast /path/to/controlfile/forecast_control.yaml

**Finished!**

That’s it! That is all you need for a CAMPS forecast development! All output files are saved in NetCDF format 
and can be found in the output paths specified inside each driver script control file.

This repository is a scientific product and is not official communication of the National Oceanic and Atmospheric Administration, or the United States Department of Commerce. All NOAA GitHub project code is provided on an ‘as is’ basis and the user assumes responsibility for its use. Any claims against the Department of Commerce or Department of Commerce bureaus stemming from the use of this GitHub project will be governed by all applicable Federal law. Any reference to specific commercial products, processes, or services by service mark, trademark, manufacturer, or otherwise, does not constitute or imply their endorsement, recommendation or favoring by the Department of Commerce. The Department of Commerce seal and logo, or the seal and logo of a DOC bureau, shall not be used in any manner to imply endorsement of any commercial product or activity by DOC or the United States Government.

**It is important to note that CAMPS is under active development at MDL.  Check the release notes for more details on new features, bug fixes, and known issues.  Our documentation page will be undergoing a significant update in the coming weeks as well.  Check back for more updates soon!**

# Welcome to the Community Atmospheric Model Post-Processing System (CAMPS) Repository

CAMPS is a software infrastructure that supports Statistical Post-Processing (StatPP) and is maintained as community code.  CAMPS utilizes standards and tools for data representation and incorporates widely recognized metadata standards.  For more information about the development, structure, and the functionality of CAMPS please visit our [documentation page.](https://noaa-mdl.github.io/CAMPS/)

 ## Anaconda Python for CAMPS

CAMPS software is currently compatible with Python 3.6 or above . It is strongly recommended that the user install Anaconda3 Version 5.3.1, as CAMPS relies on many of the built in packages that are included. The Anaconda archive is [here](https://repo.anaconda.com/archive/).

In addition to Anaconda3, CAMPS requires the following Python packages be installed:

| Package | Version |
|--|--|
| netCDF4 | 1.4.2 |
| pyproj | 1.9.6 |
| MetPy | 0.12.0 |
| pygrib | 2.0.4 |

The user is not required to use an Anaconda distribution.  In that case, in addition to the Python packages in the table above, the following must also be installed:

| Package | Version |
|--|--|
| numpy | 1.17.3 |
| scipy | 1.3.1 |
| pandas | 0.23.4 |
| seaborn | 0.9.0 |
| PyYaml | 3.13 |
| matplotlib | 3.1.1 |



## Notes:
* If you have issues installing Pygrib, check your Linux distribution to make sure that it supports Pygrib.  You may need
  to update your Linux distribution.
* We are still working on supporting CAMPS for windows.  More to come on that in the future.

## Installing CAMPS

If you are working on a shared computing system, your system administrators may install CAMPS directly into the system's main Python distribution (either Anaconda or a custom library with all necessary dependencies met for CAMPS). This should make the CAMPS package available for any user on that system, just like any other Python package.

However, if you would like to interact with the CAMPS source code directly, it is recommended that you clone the CAMPS repository onto your local work-space, and create a separate location for your own CAMPS installation. This will make developing new features, and testing them, easier. See further instructions under **CAMPS as Standalone Software** for instructions on how to install CAMPS outside of an Anaconda Python distribution.


**To install CAMPS into an existing Python distribution, perform the following::**

    $ cd /path/to/CAMPS/repository_clone
    $ python setup.py install --prefix=<prefix>

*Note: **`<prefix>`** is the path to the Python distribution where you wish to install CAMPS*

## CAMPS as a 3rd party package

If preferred, you can install CAMPS to a separate directory (outside of an existing Python installation), with expansion out to where Python installs 3rd party packages (`<python-install-path>/lib/pythonX.Y/site-packages/`, where X.Y represents the major.minor version of Python).

You will need to create your own installation folder along with a deeper directory structure that Python uses.  Perform the following::

    $ mkdir -p <abs_path>/lib/pythonX.Y/site-packages

*Note: <abs_path> is the FULL path to wherever you wish to install CAMPS. This could be your home directory or a deeper directory you created to hold your installation.*

Issue the following commands to set the necessary environment variables and install CAMPS::

    $ cd /path/to/CAMPS/repository_clone
    $ export PYTHONPATH=<abs_path>/lib/pythonX.Y/site-packages
    $ python setup.py install --prefix=<abs_path>
    $ export PATH=$PATH:<abs_path>/bin

When installing CAMPS outside of a Python distribution, if the installation path does not exist, and/or the installation directory is not in your PYTHONPATH environment variable, then setup.py will fail. Subsequently if your CAMPS bin directory is not in your PATH then console scripts will not work and you will not be able to run the driver scripts directly from your Unix shell.

## Running CAMPS Driver Scripts
The CAMPS package makes use of something called **console scripts** in setup.py.  This means that you can run any driver script from the command line, anywhere on your machine (so long as your Python library can find CAMPS -- hence setting PYTHONPATH and updating PATH **or** installing into your Python distribution directly)

For detailed information on what each CAMPS driver script does, and a deeper dive into the various features of the CAMPS software, please see the [Technical Description](https://noaa-mdl.github.io/CAMPS/technical/index.html) section of the CAMPS documentation website.

**There are 6 total driver scripts available for CAMPS:**

| CAMPS Module (driver script) | Console Script Name  |
|--|--|
| grib2_to_nc_driver.py        |  camps_grib2_to_nc   |
| metar_driver.py              |  camps_metar_to_nc   |
| marine_driver.py             |  camps_marine_to_nc  |
| mospred_driver.py            |  camps_mospred       |
| equations_driver.py          |  camps_equations     |
| forecast_driver.py           |  camps_forecast      |

To run a CAMPS driver script from the shell you must first launch python and import CAMPS::

    $ python
    Python 3.7.2 (default, Dec 29 2018, 06:19:36)
    [GCC 7.3.0] :: Anaconda, Inc. on linux
    Type "help", "copyright", "credits" or "license" for more information.
    >>> import camps
    >>> quit()

This initial import of CAMPS will create a hidden directory in your home directory named .camps/, if it does not already exist.  This directory (**.camps/**) will contain your local CAMPS database (**camps.db**) and control files in the directory named **control**.

Users are required to edit the necessary control files before running any driver scripts.  **All driver scripts must be run with the appropriate control file passed in as a system argument via the command line.**

Inside your **.camps/control** directory are the template control files needed to run your desired driver script.  The user can edit these directly, or preferrably, create new control files that match the format and level of information provided in the template files.

For example, to run mospred_driver you should edit/create several control files:

* **Mospred_control.yaml** shows the template of how to set all your input and output file paths and things like date range, etc… for mospred_driver. This is the main control file for this driver script.
* **Pred.yaml** is a template of how to specify the predictors and/or predictands you want to use in your run of mospred_driver. The path to this control file should be set in the mospred_control.yaml style control file.
* **Alldevsites.lst and Alldevsites.tbl** are examples of a station list and station table. The user must provide a list of stations for which to process predictors/predictands, and a table of all the possible stations the user wants to process, with information such as location and abbreviation. The path to these files are also set in the main mospred_driver control file (ex: mospred_control.yaml).

Control files do not require a specific name. As long as you provide the correct paths/names and format to the control files you are all set. You can even rename the control files. When running a driver script, simply pass in a control file with the same format as the example control files found inside .camps/control as the system argument.

Anytime you run a CAMPS driver script it will create and/or populate the database in your **.camps/** directory, which was created in your home directory upon installation. The CAMPS update function will check to see if your current input file(s) already exist in the database and add them if they do not.

Once you have your control files properly configured you are ready to run your driver script(s)!

If you are running mospred_driver you would issue the following command::

    $ camps_mospred /path/to/home/.camps/control/mospred_control.yaml

*Note: Make sure you give the full path to your control file as the only system argument!*

Once the script finishes it should put your output netCDF file in whatever directory/file you set in your primary driver script control file.

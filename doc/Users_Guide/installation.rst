.. _installation:

**************
Installation
**************

Python 3.6 or newer is required to run CAMPS.  
Anaconda3-5.3.1 (or newer) is highly recommended for running CAMPS, as many of the additional 
required packages are included within an Anaconda distribution.

**Required Packages (minimum versions):**

+----------+---------+
| Language | Version |
+==========+=========+
| Python   | 3.6     |
+----------+---------+

+-------------------------+---------------------+
|        Packages         |       Version       |
+=========================+=====================+
| netCDF4                 | 1.7.3               |
+-------------------------+---------------------+
| pyproj                  | 1.9.6               |
+-------------------------+---------------------+
| pygrib                  | 2.0.4               |
+-------------------------+---------------------+
| metpy                   | 0.12.0              |
+-------------------------+---------------------+
| scipy                   | 1.3.1               |
+-------------------------+---------------------+
| pandas                  | 0.23.4              |
+-------------------------+---------------------+
| seaborn                 | 0.9.0               |
+-------------------------+---------------------+
| PyYaml                  | 3.13                |
+-------------------------+---------------------+
| numpy                   | 1.17.3              |
+-------------------------+---------------------+
| matplotlib              | 3.1.1               |
+-------------------------+---------------------+

Standard Installation
======================
If you have the correct permissions, you may install CAMPS directly into your system's main Python 
distribution (either Anaconda or a custom library with all necessary dependencies met for CAMPS). 
This should make the CAMPS package available for anyone using that Python distribution, just like any other Python package.

To install CAMPS into an existing Python distribution, perform the following:
::

    $ cd /path/to/CAMPS/repository_clone
    $ python3 setup.py install

When installing CAMPS into an existing Python installation, `console scripts <https://setuptools.readthedocs.io/en/latest/userguide/entry_point.html>`_ will be installed to the 
same bin/ directory as the python executable you are invoking.

Custom Installation
====================
CAMPS can be installed into a separate directory (outside of an existing Python installation).  
A situation where this might occur is if you are working on a shared computing system.  
Given an installation path prefix (<install-path>), Python packages will install packages using the following directory structure:
::

    $ mkdir -p <install-path>/lib/pythonX.Y/site-packages

**Note:** <install-path> should be the absolute path.

Issue the following commands to set the necessary environment variables and install CAMPS:
::

    $ cd /path/to/CAMPS/repository_clone
    $ export PYTHONPATH=<install-path>/lib/pythonX.Y/site-packages
    $ python3 setup.py install --prefix=<install-path>
    $ export PATH=$PATH:<install-path>/bin

When installing CAMPS outside of a Python distribution, if the installation path does not exist, 
and/or the installation directory is not in your PYTHONPATH environment variable, then setup.py will fail.  
Append the CAMPS installation bin/ directory to PATH.  This allows CAMPS console scripts to be available in your shell environment.

Alternatively, you can install CAMPS into your own user space via the following command:
::

    $ python3 setup.py install --user

which will install into `$HOME/.local` on most modern Linux/UNIX systems.

Initializing CAMPS
====================

After successfully installing CAMPS, it is necessary to open a python session, and import the software at least once.  
This first import of the CAMPS module will create a hidden directory, ``$HOME/.camps/control``, which 
will contain all the control and configuration file templates.
::

    $  python
    $  import camps
    $  quit()



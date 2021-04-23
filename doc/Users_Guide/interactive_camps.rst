==================
Interactive CAMPS
==================

CAMPS can also be used via an interactive python session. The user can import CAMPS, instantiate a Camps_data object, apply procedures, and read/write data.

When instantiating a Camps_data object, two arguments are accepted: **name** and **autofill**.  The default for autofill is set to True.  
When autofill is set to True, name must match a variable defined within the netcdf.yaml configuration file. This can be through a direct match, 
or via a predefined alias.  Once identified, the associated metadata will be  automatically added to the object.  
If the name doesn’t match any variable within netcdf.yaml, an error will be raised.  

For example, In netcdf.yaml the following entry exists for wind speed:
::

  wind_speed_instant :  &WindSpd
    data_type : float32
    attribute :
      SOSA__observedProperty : "StatPP__Data/Met/Moment/WindSpd"
      long_name : "horizontal wind speed"
      standard_name : "wind_speed"
      comment : "Wind speed is set to -9 if winds are variable."

A Camps_data object can then be instantiated as follows:
::

    >>> from camps.core.Camps_data import Camps_data
    >>> import numpy
    >>> wspd = Camps_data('wind_speed_instant') # Initializes object
    
Notice that next to the variable name there is a pre-defined alias “WindSpd”.  At the bottom of netcdf.yaml 
there is a list of alternative variable names for some variables, which are linked to the desired alias.  
These aliases act as “pointers” to allow for CAMPS to recognize alternative variable names, and use the metadata pre-defined in netcdf.yaml. 

For example, perhaps your wind speed variable is called “wind_speed_value”.  At the bottom of the netcdf.yaml file one simply would need to add the following: 
``“wind_speed_value” : *WindSpd`` to the list of pointers.  This would link the variable name “wind_speed_value” to the assigned metadata for “wind_speed_instant”.

If autofill is instead set to False, name can be whatever string a user decides.  However, all metadata will need to be added manually by the user.
It is highly recommended that any new variables be added to a users netcdf.yaml file, following the formatting layout contained in that file.  
Otherwise, there may be issues with reading the resulting output using other CAMPS utilities.

Instantiating a CAMPS data object provides you with essentially an empty container, with some basic metadata, either autofilled 
or manually entered. The next steps would be to add actual data to the object, along with associated data such as time or location 
information. This can be added to the Camps_data object in the following way:
::

    >>> wspd.data = numpy.random.rand(10,10)*50 # Assign data
    >>> ptime = Time.PhenomenonTime(start_time='19910518', end_time='20180810')
    >>> wspd.time.append(ptime)

Perhaps the user has a piece of metadata they would like to add that is unique to their data.  Metadata attributes can always be added
to a Camps_data object in the following way: 
::

>>> wspd.metadata['my_important_attribute'] = 42

As the user works with their data, they will likely want to add information about what procedures have been performed on their data. 
To add a procedure to your Camps_data object, a Process object is instantiated, and appended to the Camps_data object.

Using the procedure ‘BiLinInterp’ as an example (predefined in procedures.yaml), there are two ways to add a Process object to your 
Camps_data object:
::

    >>> wspd.add_process('BiLinInterp')
    
Another option is:
::

    >>> p = camps.core.Process.Process(‘BiLinInterp’)
    >>> wspd.processes.append(p)

Similar to netcdf.yaml, metadata for predefined procedures are stored in procedures.yaml.  If the user wishes to take advantage of the “add_process” function, 
they need to add their procedure to that control file, following the format outlined there.  Otherwise “empty” procedure objects can be instantiated, 
and their metadata manually added.

Lastly, since we’re writing to netcdf, dimensions of the variable data must be added to the Camps_data object. Dimensions can generally be named anything, 
but there are a few dimensions that have special properties, that act slightly differently. These are found in netcdf.yaml in the dimensions section. 
To add dimensions to the Camps_data object:
:: 

    >>> wspd.add_dimensions('x','y')

The Camps_data object would now look as follows:
::

    ***** wind_speed ******
    *
    * dtype               : float64
    * processes           : ( )
    * dimensions          : ['x', 'y']
      Metadata:
    * comment             : Wind speed is set to -9 if winds are variable.
    * SOSA__observedProperty: StatPP__Data/Met/Moment/WindSpd
    * name                : wind_speed
    * valid_min           : 0.0
    * coordinates         : elev
    * long_name           : horizontal wind speed
    * standard_name       : wind_speed
    * my_important_attribute: 42
    * valid_max           : 75.0
    Shape:
    (4, 3)
    Data:
    [[ 44.32559503  29.6
    29957  48.87075532]]

The user will likely want to write their data to an output file.  Once the Camps_data object has 
been instantiated and populated with data and metadata, writing output is simple:
::
 
    >>> from camps.core.writer import write
    >>> write(wspd, 'CAMPS_output.nc')

The CDL output from the newly created file would look like this:
::

    $ ncdump output.nc
    
    netcdf CAMPS_output {
    dimensions:
        x = 4 ;
        y = 3 ;
    variables:
        double WindSpd_instant(x, y) ;
                WindSpd_instant:_FillValue = 9999. ;
                WindSpd_instant:SOSA__observedProperty = "StatPP__Data/Met/Moment/WindSpd" ;
                WindSpd_instant:long_name = "horizontal wind speed" ;
                WindSpd_instant:valid_max = 75. ;
                WindSpd_instant:standard_name = "wind_speed" ;
                WindSpd_instant:comment = "Wind speed is set to -9 if winds are variable." ;
                WindSpd_instant:units = "m/s" ;
                WindSpd_instant:my_important_attribute = 42LL ;
                WindSpd_instant:coordinates = "latitude longitude" ;
                WindSpd_instant:ancillary_variables = "" ;
                WindSpd_instant:missing_value = 9999. ;
                WindSpd_instant:PROV__wasInformedBy = "( )" ;
                WindSpd_instant:SOSA__usedProcedure = "( )" ;

    // global attributes:
                :institution = "NOAA/National Weather Service" ;
                :Conventions = "CF-1.7 CAMPS-1.2" ;
                :version = "CAMPS-1.2" ;
                :history = "" ;
                :references = "" ;
                :organization = "NOAA/MDL" ;
                :url = "http://www.nws.noaa.gov/mdl/, https://sats.nws.noaa.gov/~camps/" ;
                :primary_variables = "WindSpd_instant" ;
    data:

      WindSpd_instant =
        9.36115709400316, 40.0805602441551, 4.00665537148,
        40.9072218935792, 16.2853803224382, 23.8285486619925,
        2.557393430461, 18.4436592224694, 26.3832006293729,
        29.9961875737658, 17.9772550713641, 33.5965850685218 ;

    group: prefix_list {

      // group attributes:
                :PROV__ = "http://www.w3.org/ns/prov/#" ;
                :StatPP__ = "http://codes.nws.noaa.gov/StatPP/" ;
                :SOSA__ = "http://www.w3.org/ns/sosa/" ;
      } // group prefix_list
    }


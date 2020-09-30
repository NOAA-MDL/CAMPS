import sys
import os
import numpy as np
import pdb
import re
import logging
from netCDF4 import Dataset

from .nc_writable import nc_writable
from .Process import Process
from . import Time
from ..registry import util as cfg
from ..registry.db import db as db
from ..registry import constants as const



"""Module: Camps_data.py

Methods:

Classes:
    Camps_data
        Methods:
            __init__
            add_coord
            has_plev
            has_elev
            has_bounds
            has_time_bounds
            is_feature_of_interest
            has_plev_bounds
            has_elev_bounds
            get_coordinate
            get_time_bounds
            get_lead_time
            get_result_time
            get_forecast_reference_time
            get_valid_time
            get_phenom_time
            get_time
            add_process
            add_data
            get_data_type
            get_dimensions
            change_property
            get_observedProperty
            change_data_type
            set_dimensions
            add_dimensions
            add_db_metadata
            add_metadata
            add_source
            add_fcstTime
            add_plev_attributes
            add_elev_attributes
            add_plev_bounds_attributes
            add_elev_bounds_attributes
            in_metadata
            get_variable_name
            get_coord_name
            create_dimensions
            _write_coordinate
            add_bounds_process
            _write_elev_bounds
            _write_time_bounds
            _write_plev_bounds
            _write_elev
            _write_plev
            reshape
            create_dimension
            write_to_nc
            add_to_database
            get_chunk_size
            check_correct_shape
            add_nc_data
            get_cell_methods
            check_dimensions
            _add_nc_metadata
            get_source
            is_observation
            is_model
            is_vector
            get_fill_value
            get_process_str
            add
            __add__
            add_times
            __getattr__
            __str__
"""


FILL_VALUE = 9999
coord_str = 'coordinates'


class Camps_data(nc_writable):
    """Camps data object for storing data and metadata describing the variable.

    Attributes:
        name (str): `quick fill` name that can be used to initialize variable from template.
        data (:np.array:): n-dimensional numpy array holding variable data.
        dimensions (:list: of str): The names of the dimensions--ordered by dimension.
        processes (:list: of :obj:Process): Process that modify this variable.
        metadata (dict): Metadata with key-value pairs.
        time (:list: of :obj:Time): Time objects describing this variable
        properties (dict): Metadata that will not be written to NetCDF file
                that may be used internally.
        location (:obj:Location) Location object which describes the first dimensions.

    Note:
        Time objects must have a dimensionality that's compatible with 'data'.
    """


    def __init__(self, name, autofill=True):
        """Initializes object properties and adds metadata from the database
        coresponding to the name if available.

        Args:
            name (str): `quick-fill` name that can be used to initialize variable from template.
            autofill (bool): If there should be an attempt to autofill metadata based on `name`.
        """

        self.name = name
        self.data = np.array([])
        self.dimensions = []  # The name of the dimensions
        self.processes = []
        self.preprocesses = []
        self.metadata = {}
        self.time = []
        self.properties = {}
        self.components = []
        self.location = None
        if autofill:
            self.add_db_metadata()


    def add_coord(self,level1, level2=None, vert_type=None):
        """Add vertical coordinate information into the camps data object.
        Specifically, the type of coordinate is placed in the object's metadata
        and the values in the object's properties.
        """

        #Insert the type of vertical coordinate into metadata if in the argument list.
        if vert_type is not None:
            self.metadata[const.COORD] = vert_type

        #Add the value of the vertical coordinate into properties.  If the forecast variable is
        #defined in a vertical layer, then insert the layer bounding values into metadata.
        if level2 is not None:
            if vert_type is None: #vert_type(coordinates) might be set in the netcdf.yaml file
                try: #First see if coordinates is set in the netcdf.yaml
                    vert_type = self.metadata[const.COORD]
                except: #if it is not in netcdf.yaml then let user know they need to set vert_type somewhere
                    logging.error('Must set a vert_type either in netcdf.yaml or pass in function')
                    raise ValueError
            self.metadata['bounds'] = vert_type+'_bounds'
            self.properties['coord_val1'] = level1
            self.properties['coord_val2'] = level2
        else:
            self.properties['coord_val'] = level1


    def has_plev(self):
        """Returns True if vertical coordinate type is pressure level."""

        if const.COORD in self.metadata:
            return const.PLEV in self.metadata[const.COORD]


    def has_elev(self):
        """Returns True if vertical coordinate type is elevation."""

        if const.COORD in self.metadata:
            return const.ELEV in self.metadata[const.COORD]


    def has_bounds(self):
        """Returns True if the variable is defined in a vertical layer."""

        if 'bounds' in self.metadata:
            return True
        if 'coordinates' in self.metadata:
            return 'bounds' in self.metadata['coordinates']


    def has_time_bounds(self):
        """Returns True if the variable is defined over a time span."""

        return 'hours' in self.properties or db.get_property(self.name, 'hours') is not None


    def is_feature_of_interest(self):
        """Returns True if the variable is a feature of interest."""

        return 'feature_of_interest' in self.properties or db.get_property(self.name, 'feature_of_interest') is not None


    def has_plev_bounds(self):
        """Returns True if variable is defined over a vertical layer bounded by pressure levels."""

        if self.has_bounds():
            if 'bounds' in self.metadata:
                return self.metadata['bounds'] == 'plev_bounds'
            if 'coordinates' in self.metadata:
                return 'plev_bounds' in self.metadata['coordinates']


    def has_elev_bounds(self):
        """Returns True if variable is defined over a vertical layer bounded by elevation levels."""

        if self.has_bounds():
            if 'bounds' in self.metadata:
                return self.metadata['bounds'] == 'elev_bounds'
            if 'coordinates' in self.metadata:
                return 'elev_bounds' in self.metadata['coordinates']


    def get_coordinate(self):
        """Returns the value(s) of the vertical coordinate if it exists.
        Otherwise, returns None.
        """

        #If variable is defined over a vertical layer, returns a tuple of the
        #bounding vertical coordinate values.
        if self.has_elev_bounds() or self.has_plev_bounds():
            try:
                coord1 = self.properties['coord_val1']
                coord2 = self.properties['coord_val2']
            except:
                coord1 = db.get_property(self.name, 'coord_val1')
                coord2 = db.get_property(self.name, 'coord_val2')
            coord1 = int(coord1)
            coord2 = int(coord2)
            return (coord1, coord2)

        #At this point, if it exists, the variable is defined at a single vertical level.
        if self.has_plev() or self.has_elev():
            try:
                coord = self.properties['coord_val']
            except:
                coord = db.get_property(self.name, 'coord_val')
            coord = int(coord)
            return coord

        return None


    def get_time_bounds(self):
        """Returns time object of type PhenomenonTimePeriod if it exists."""

        if not self.has_time_bounds():
            return None

        for i in self.time:
            if 'OM__phenomenonTimePeriod' in i.name:
                return i


    def get_lead_time(self):
        """Returns time object of type LeadTime if it exists."""

        time = self.get_time(Time.LeadTime)
        if time:
            return time

        return None


    def get_result_time(self):
        """Returns time object of type ResultTime if it exists."""

        time = self.get_time(Time.ResultTime)
        if time:
            return time

        return None


    def get_forecast_reference_time(self):
        """Returns time object of type ForecastReferenceTime if it exists."""

        time = self.get_time(Time.ForecastReferenceTime)
        if time:
            return time

        return None


    def get_valid_time(self):
        """Returns time object of type ValidTime if it exists."""

        time = self.get_time(Time.ValidTime)
        if time:
            return time

        return None


    def get_phenom_time(self):
        """Returns either the time object of type PhenomenomTime
        or the time object of type PhenomenonTimePeriod if it exists"""

        time = self.get_time(Time.PhenomenonTime)
        if time:
            return time

        time = self.get_time(Time.PhenomenonTimePeriod)
        if time:
            return time

        return None


    def get_time(self, time_type):
        """Returns a Time object of type time_type or None if there's no such instance"""

        time_arr = [time for time in self.time if type(time) is time_type]

        if len(time_arr) == 0:
            return None

        if len(time_arr) > 1:
            logging.warning("More than one " + str(time_type) +
                    " time describing " + self.name)

        return time_arr[0]


    def add_process(self, process):
        """Adds a Process object to the Processes list or creates one if given a str."""

        if process.__class__ is not Process and type(process) is str:
            process = Process(process)

        self.processes.append(process)

#return statement unnecessary
#        return self


    def add_preprocess(self, process):
        """Adds a Process object to the Preprocesses list or creates one if given a str."""

        if process.__class__ is not Process and type(process) is str:
            process = Process(process)

        self.preprocesses.append(process)


    def add_component(self, c_obj):
        """Adds a Camps data object to the component list of another
        Camps data object.  The variable of the former object is a component
        of the variable of the latter object, i.e. it is used in computing
        the latter object's variable.  For examples, temperature and relative
        humidity are components of dewpoint temperature.  Data of the components
        are suppressed.
        """

        #Add the lead time to the metadata
        c_obj.metadata.update({'leadtime' : int(c_obj.get_lead_time().data.data[0]/3600)})

        #Record the component's data dimensions and sizes in its metadata.
        grid_dimSizes = '( '
        for dim,size in zip(c_obj.dimensions,c_obj.data.shape):
            grid_dimSizes += dim + ' : ' + str(size) + ', '
        c_obj.metadata.update({'grid_dimSizes' : grid_dimSizes[:-2] + ' )'})

        #Remove the metadata key 'filepath' and its value.
        try:
            c_obj.metadata.pop('filepath')
        except:
            pass

        #Remove the component's data.
        c_obj.dimensions = []
        c_obj.data = None

        #Add component's Camps object sans data to component list of
        #computed variable's object.
        self.components.append(c_obj)


    def add_data(self, data):
        """Given a numpy array with the correct dimensions,
        sets it to objects 'data' instance variable.
        """

        if not isinstance(data, type(np.array([]))):
            logging.error(type(data) + "is not a numpy array")
            raise ValueError

        if len(self.dimensions) == 0:
            try:
                set_dimensions()
            except:
                logging.warning('set_dimensions failed')

        if len(data.shape) != len(self.dimensions):
            logging.error("number of dimensions of data is not "
                          "equal to number of object dimensions")
            raise ValueError

        self.data = data

#return not needed
#        return self


    def get_data_type(self):
        """Returns the data type of the data in camps data object,
        gotten either from the properties attribute or, if not there,
        the database table 'properties'.
        """

        try:
            return self.properties['data_type']
        except:
            return db.get_property(self.name, 'data_type')


    def get_dimensions(self):
        """Obtains the dimensions of the variable specified in the
        netcdf.yaml file.
        """

        var = cfg.read_variables()[self.name]
        dimensions = var['dimensions']

        return dimensions


    def change_property(self, property_basename):
        """Changes the value of OM__observedProperty in the variable's metadata."""

        property_basename = os.path.basename(property_basename)
        properties_dict = cfg.read_observedProperties()
        try:
            self.metadata['OM__observedProperty'] = properties_dict[property_basename]
        except KeyError:
            logging.warning("\"" + str(property_basename) + "\" is not defined in registry/ObservedProperties.yaml")
            logging.warning("Using \"" + str(property_basename) + "\" anyway")
        except:
            raise


    def get_observedProperty(self):
        """Returns the parsed OM__observedProperty metadata element."""

        op = self.metadata['OM__observedProperty']
        if op[-1] == '/':
            op = op[0:-1]

        return os.path.basename(op)


    def change_data_type(self, data_type=None):
        """Changes the variable's data type."""

        if data_type is not None:
            self.data = self.data.astype(data_type)

        #If data_type not given, then it gets set to that given in the variable's
        #properties attribut or, failing that, the database table 'properties'.
        else:
            self.data = self.data.astype(self.get_data_type())


    def set_dimensions(self, dimensions=None):
        """Sets the dimension attribute of the camps data object,
        given a tuple of strings describing the dimensions."""

        #Retrieves the dimensions set in netcdf.yaml if the argument
        #'dimensions' is missing.
        if not dimensions:
            dimensions = self.get_dimensions()
            dimensions = tuple(dimensions)

        if type(dimensions) is not tuple:
            logging.error(type(dimensions)+"is not of type tuple")
            raise TypeError

        if len(self.dimensions) > 0:
            logging.debug("overwriting dimensions")

        self.dimensions = list(dimensions) #The dimensions attribute must be a list.

#This return statement is unnecessary.
#        return self


    def add_dimensions(self, *dims):
        """Add dimensions to self, if not already in self."""

        for dim in dims:
            if dim not in self.dimensions:
                self.dimensions.append(dim)


    def add_db_metadata(self):
        """Reads the variable's metadata from the database and inserts it into
        the variable's camps data object."""

        meta_dict = {}
        try:
            meta_dict = db.get_all_metadata(self.name)
        except ValueError:
            logging.warning("'" + self.name + "' not defined in metadata db")

        self.metadata = meta_dict


    def add_metadata(self, key, value):
        """Adds an entry into the metadata."""

        self.metadata[key] = value
#return statement unnecessary
#        return self


    def add_source(self, value):
        """Sets the PROV__Used attribute to 'value'."""

        self.metadata['PROV__Used'] = value


    def add_fcstTime(self, value):
        """Adds an entry for the model cycle time into metadata."""

        self.metadata['FcstTime_hour'] = value


    def add_plev_attributes(self, plev_var):
        """Adds common pressure level attributes."""

        setattr(plev_var, 'long_name', 'pressure')
        setattr(plev_var, 'units', 'hPa')
        setattr(plev_var, 'standard_name', 'air_pressure')
        setattr(plev_var, 'positive', 'down')
        setattr(plev_var, 'axis', 'Z')


    def add_elev_attributes(self, elev_var):
        """Adds common elevation attributes."""

        setattr(elev_var, 'long_name', 'height above surface')
        setattr(elev_var, 'units', 'm')
        setattr(elev_var, 'standard_name', 'height')
        setattr(elev_var, 'positive', 'up')
        setattr(elev_var, 'axis', 'Z')


    def add_plev_bounds_attributes(self, plev_var):
        """Adds common pressure layer bounds attributes."""

        setattr(plev_var, 'long_name', 'pressure layer bounds')
        setattr(plev_var, 'units', 'hPa')
        setattr(plev_var, 'standard_name', 'air_pressure')
        setattr(plev_var, 'positive', 'down')
        setattr(plev_var, 'axis', 'Z')


    def add_elev_bounds_attributes(self, elev_var):
        """Adds common elevation layer bounds attributes."""

        setattr(elev_var, 'long_name', 'height above surface')
        setattr(elev_var, 'units', 'm')
        setattr(elev_var, 'standard_name', 'height')
        setattr(elev_var, 'positive', 'up')
        setattr(elev_var, 'axis', 'Z')


    def in_metadata(self, var):
        """Returns True if key 'var' is in metadata dictionary"""

        return var in self.metadata


    def get_variable_name(self):
        """Returns a uniqueish vairable name such that it looks like,
        <dataSource>_<observedProperty>_<duration>_<verticalCoord>_<fcstReferenceTime>_<fcstLeadTime>_<########>
        """

        if self.is_feature_of_interest():
            return self.name

        #Do not write dataSource
        name = ""

        #Write observedProperty
        try:
            name += self.get_observedProperty()
        except:
            pass

        #Write duration
        if self.has_time_bounds():
            bounds = self.get_time_bounds() #get bounds object
            cell_method = self.get_cell_methods() #get cell method
            method = str(list(cell_method.values())[0]) #grab value from dictionary
            name += '_'+method+'_'+str(bounds.get_duration())+'hr' #will add the duration and type (ex: avg, max, min) to name
        else:
            name += '_instant'

        #Write verticalCoordinate
        if self.has_plev():
            level = self.get_coordinate()
            if self.has_plev_bounds():
                name += '_'+str(level[0])+'mb_'+str(level[1])+"mb"
            else:
                name += '_'+str(level)+'mb'

        elif self.has_elev():
            level = self.get_coordinate()
            if self.has_elev_bounds():
                name += '_'+str(level[0])+'m_'+str(level[1])+"m"
            else:
                name += '_'+str(level)+'m'

        #Write fcstReferenceTime (model cycle hour)
        try:
            name += '_'+str(self.metadata['FcstTime_hour']).zfill(2)+'Z'
        except:
            pass

        #Write leadtime, given in hours.
        try:
            leadtime = self.metadata['leadtime']
            name += '_%shr'%(str(leadtime))
        except:
            pass

        #Include preprocess name pieces that are features of interest.
        proc_names = self.get_preprocess_str().split(' ')
        try:
            proc_names.remove('(')
        except ValueError:
            pass
        try:
            proc_names.remove(')')
        except ValueError:
            pass
        for i, process in enumerate(self.preprocesses):
            if process.attributes['feature_of_interest'] == "yes":
                name += '_' + proc_names[i]
                if re.search('smooth', proc_names[i], re.IGNORECASE):
                    try:
                        name += str(self.metadata['smooth'])
                    except KeyError:
                        pass

        #Include process name pieces that are features of interest.
        proc_names = self.get_process_str().split(' ')
        try:
            proc_names.remove('(')
        except ValueError:
            pass
        try:
            proc_names.remove(')')
        except ValueError:
            pass
        for i, process in enumerate(self.processes):
            if process.attributes['feature_of_interest'] == "yes":
                name += '_' + proc_names[i]
                if re.search('smooth', proc_names[i], re.IGNORECASE):
                    try:
                        name += str(self.metadata['smooth'])
                    except KeyError:
                        pass

        #For MOS forecast output, add either "MOS" or "CmpChk" to variable name
        if 'TmpDewCmpChk' in self.get_process_str():
            name = 'CmpChk_'+name
        elif 'MOS_Method' in self.get_process_str():
            name = 'MOS_'+name

        return name


    def get_coord_name(self, nc_handle, coord_name, is_bounds=False):
        """Produces a unique vertical coordinate name of the form coord_name+'\d+' for
        the variable's vertical coordinate value set, if none exists already.
        """

        #Get vertical coordinate values
        coord_data = self.get_coordinate()

        num = 0
        all_vars = nc_handle.variables
        #Return if name exists for given values of vertical coordinate.
        #Otherwise increment 'num', the digital suffix of the coordinate name.
        for v in list(all_vars.keys()):
            if re.match(r'^' + coord_name + '\d+$',  v, re.I): #match 'coord_name' with 'v' ignoring case.
                if is_bounds:
                    first_num_matches = coord_data[0] == all_vars[v][0][0]
                    second_num_matches = coord_data[1] == all_vars[v][0][1]
                    if first_num_matches and second_num_matches:
                        already_exists = True
                        return (already_exists, v)
                else:
                    first_num_matches = coord_data == all_vars[v][0]
                    if coord_data == all_vars[v][0]:
                        already_exists = True
                        return (already_exists, v)
                # Found a coordinate, but it didn't match this object's
                num += 1

        #At this point, there is no existing name for the given values for the vertical coordinate.
        #Set its unique name and return.
        name = coord_name + str(num)
        already_exists = False

        return (already_exists, name)


    def create_dimensions(self, nc_handle):
        """Creates a netCDF4 dimension from a dimension of the variable
        if there is no netCDF4 Dataset dimension with a matching name.
        """

        dims = nc_handle.dimensions
        for d in self.dimensions:
            if d not in dims:
                self.create_dimension(nc_handle, d)


    def _write_coordinate(self, nc_handle):
        """Writes into a netCDF file the variable's vertical coordinate set and
        its bounding time values.  Also, adds to its metadata 'coordinates' entry appropriate
        dimension names if the variable is defined either on a grid or at stations.
        """

        #Will be returned True if writing to netCDF file succeeds.
        success = False

        #Vertical coordinates
        if self.has_plev_bounds():
            success = self._write_plev_bounds(nc_handle)
        elif self.has_elev_bounds():
            success = self._write_elev_bounds(nc_handle)
        elif self.has_plev():
            success = self._write_plev(nc_handle)
        elif self.has_elev():
            success = self._write_elev(nc_handle)

        #Time bounds
        if self.has_time_bounds():
            success = self._write_time_bounds(nc_handle)
            #self.add_bounds_process() #removing these processes 

        #Add grid dimension names or station dimension names
        #to metadata entry 'coordinates'
        if 'coordinates' in self.metadata:
            coord_str = self.metadata['coordinates']
            coords_to_add = [coord_str]
            if 'grid_mapping' in self.metadata.keys():
                if 'latitude_longitude' in self.metadata['grid_mapping']:
                    if 'x' in self.dimensions:
                        coords_to_add.append('longitude')
                    if 'y' in self.dimensions:
                        coords_to_add.append('latitude')
                else:
                    if 'x' in self.dimensions:
                        coords_to_add.append('x')
                    if 'y' in self.dimensions:
                        coords_to_add.append('y')
            if 'number_of_stations' in self.dimensions:
                coords_to_add.append('station')
            add_str = ' '.join(coords_to_add)
            self.metadata['coordinates'] = add_str

        return success


    def add_bounds_process(self):
        """Adds a process representing the cell_method applied to either
        a vertical coordinate layer or a time span."""

        cell_type = self.metadata['cell_methods'].split(':')[1].strip(' ')

        #Currently, consider only the minimum, maximum, or sum cell methods.
        if cell_type == 'minimum':
            #If process has already been added to the list then we skip it.
            #Otherwise add it to the process list.
            if 'BoundsProcMin' in self.get_process_str():
                pass
            else:
                self.add_process('BoundsProcMin')

        elif cell_type == 'maximum':
            if 'BoundsProcMax' in self.get_process_str():
                pass
            else:
                self.add_process('BoundsProcMax')

        elif cell_type == 'sum':
            if 'BoundsProcSum' in self.get_process_str():
                pass
            else:
                self.add_process('BoundsProcSum')


    def _write_elev_bounds(self, nc_handle):
        """Writes into the netCDF file the elev_bounds variable."""

        elev = 'elev'
        nv = 'nv'

        #Turn the data into a numpy array and
        #reshape so that it has a shape of 1,2 for elev,nv
        coord_data = self.get_coordinate()
        coord_data = np.array(coord_data).reshape(1, 2)

        exists, name = self.get_coord_name(nc_handle, 'elev_bounds', is_bounds=True)
        self.metadata[coord_str] = name
        if not exists:
            if 'level' not in nc_handle.dimensions:
                nc_handle.createDimension('level', 1)
            if nv not in nc_handle.dimensions:
                nc_handle.createDimension(nv, 2)
            elev_var = nc_handle.createVariable(name, int, ('level', nv))
            self.add_elev_bounds_attributes(elev_var)
            elev_var[:] = coord_data

        return True


    def _write_plev_bounds(self, nc_handle):
        """Writes into the netCDF file the pressure level variable."""

        plev = 'plev'
        nv = 'nv'

        #Turn the data into a numpy array and
        #reshape so that it has a shape of 1,2 for plev,nv
        coord_data = self.get_coordinate()
        coord_data = np.array(coord_data).reshape(1, 2)

        #Determine if the variable already exists.
        #Return the existing name, or a new one.
        exists, name = self.get_coord_name(nc_handle, 'plev_bounds', is_bounds=True)
        self.metadata[coord_str] = name
        if not exists:
            if 'level' not in nc_handle.dimensions:
                nc_handle.createDimension('level', 1)
            if nv not in nc_handle.dimensions:
                nc_handle.createDimension(nv, 2)
            plev_var = nc_handle.createVariable(name, int, ('level', nv))
            # Probably need this defined:
            self.add_plev_bounds_attributes(plev_var)
            plev_var[:] = coord_data

        return True


    def _write_elev(self, nc_handle):
        """Writes into the netCDF file the elevation level variable.
        Changes the name to elev[n] where n a number when there are
        multiple plev variables.
        """

        elev = 'elev'
        exists, name = self.get_coord_name(nc_handle, elev)
        self.metadata[coord_str] = name
        if not exists:
            if 'level' not in nc_handle.dimensions:
                nc_handle.createDimension('level', 1)
            elev_var = nc_handle.createVariable(name, int, ('level'))
            self.add_elev_attributes(elev_var)
            elev_var[:] = self.get_coordinate()

        return True


    def _write_plev(self, nc_handle):
        """Writes into the netCDF file the pressure level variable.
        Changes the name to plev[n] where n a number when there are
        multiple plev variables.
        """

        exists, name = self.get_coord_name(nc_handle, 'plev')
        self.metadata[coord_str] = name
        if not exists:
            if 'level' not in nc_handle.dimensions:
                nc_handle.createDimension('level', 1)
            plev_var = nc_handle.createVariable(name, int, ('level'))
            self.add_plev_attributes(plev_var)
            plev_var[:] = self.get_coordinate()

        return True


    def _write_time_bounds(self, nc_handle):
        """Writes the Time bounds variable"""
        #NOTE: this function doesn't really do what it says it does anymore
        #now that we have changed how we write bounded time variables all
        #this does is add hours to self.properties if it isn't already there.
        #Rename this function??

        try:
            hours = self.properties['hours']
        except:
            hours = db.get_property(self.name, 'hours')
            self.properties['hours'] = hours
        hours = int(hours)

        t = self.get_phenom_time()


    def reshape(self, nc_handle): #NOTE: nc_handle is the wrong argument
        """Ensures 'level' is in the variable's attribute 'dimension' if it
        exists in the metadata attribute, and reshapes the data accordingly.
        """

        if 'level' in self.dimensions:
            return

        #Return if neither 'plev' nor 'elev' are in metadata.
        try:
            coord_name = self.metadata[coord_str]
        except KeyError:
            logging.warning("no " + coord_str + "metadata")
            return
        if 'plev' not in coord_name and 'elev' not in coord_name:
            return

        #At this point, it's known that the variable is defined at some vertical level.
        #Add 'level' to dimensions.
        vertical_coordinate_name = "level"
        self.dimensions = list(self.dimensions)
        self.dimensions.append(vertical_coordinate_name)


        #Reshape the data.
        shape = self.data.shape
        new_shape = list(shape)
        new_shape.append(1)
        new_shape = tuple(new_shape)
        self.data = self.data.reshape(new_shape)


    def create_dimension(self, nc_handle, dimension_name):
        """Creates a netCDF dimension for the variable's
        dimension 'dimension_name'.
        """

        index = self.dimensions.index(dimension_name)
        dim_length = self.data.shape[index]
        #dim_length = 0
        #if self.data is not None:
        #    dim_length = self.data.shape[index]
        #elif self.metadata[dimension_name]:
        #    dim_length = self.metadata[dimension_name]
        nc_handle.createDimension(dimension_name, dim_length)


    def write_to_nc(self, nc_handle, write_components=False):
        """Writes a variable into a netCDF file, including its data and metadata.
        Returns variable name.
        """

        #Add the vertical dimension to the variable
        #and ensure that its dimensions exist in netCDF Dataset dimensions.
        success = self._write_coordinate(nc_handle) #add the vertical dimension
        if success and self.data is not None: #reshape the variable's data due to adding vertical dimension.
            self.reshape(self.metadata[coord_str]) #NOTE: argument not used in called function.

        #Create the 'ancillary_variables' of time and process for the variable's metadata
        ancillary_variables = ""
        for t in self.time: #add time ancillary variables
            time_name = t.write_to_nc(nc_handle)
            ancillary_variables += time_name + " "
        for p in self.preprocesses: #add process ancillary variables
            proc_name = p.write_to_nc(nc_handle)
            ancillary_variables += proc_name + " "
        for p in self.processes: #add process ancillary variables
            proc_name = p.write_to_nc(nc_handle)
            ancillary_variables += proc_name + " "
        space = ' '
        av_list = ancillary_variables.split(space)
        av_uniq = []
        for av in av_list:
            if av not in av_uniq:
                av_uniq.append(av)
        ancillary_variables = (space.join(av_uniq))
        self.metadata['ancillary_variables'] = ancillary_variables

        # if true, write components metadata recursively, components of components.
        if write_components:
            comp_names = []
            for c in self.components: #add components of variable
                comp_name = c.write_to_nc(nc_handle, write_components)
                comp_names.append(comp_name)
            if len(comp_names) > 0:
                self.metadata.update({'PROV__wasDerivedFrom' : '( ' + ' '.join(comp_names) + ' )'})

        self.check_correct_shape() #check consistency between variable's dimensions and its data shape
        self.create_dimensions(nc_handle) #add those variable's dimensions with names that do not exist in netCDF.
        self.check_dimensions(nc_handle) #readjust dimension names so that dimensions with matching names
                                         #have equal sizes.

        #Create the netCDF variable.
        fill_value = self.get_fill_value()
        chunksize = self.get_chunk_size()

        if self.data is None:
            dtype = int
        else:
            dtype = self.data.dtype

        #Determine if variable has not already been written into the netCDF file.
        #NOTE: I tried to have this portion at the beginning of the function in order to
        #avoid doing the above code, but I get an error.
        #Get the basename of the variable and collect names of variables already written
        #into the netCDF file with the same basename.
        variable_name = self.get_variable_name()
        var_names = []
        var_name = variable_name
        number = 0
        while var_name in list(nc_handle.variables.keys()):
            var_names.append(var_name)
            number += 1
            var_name = variable_name + str(number)
        variable_name = var_name

        #Determine if the variable is a primary variable or a component.
        #Select from the existing netCDF variables those of the same type.
        is_primary = 'number_of_stations' in self.dimensions
        v_names = []
        if is_primary:
            for v_name in var_names:
                if 'number_of_stations' in nc_handle.variables[v_name].dimensions:
                    v_names.append(v_name)
        else:
            for v_name in var_names:
                if 'number_of_stations' not in nc_handle.variables[v_name].dimensions:
                    v_names.append(v_name)

        #Determine if the variable is identical in substance to one of the collection of
        #existing netCDF variables.  If so, return the name of the identical netCDF variable.
        for v_name in v_names:
            match = True
            #
            for attr in ['OM__observedProperty', 'standard_name', 'long_name', 'units', 'coordinates', \
                'filepath', 'smooth']:
                try:
                    if self.metadata[attr] != nc_handle.variables[v_name].getncattr(attr)[:]:
                        match = False
                        break
                except:
                    pass
            if match: #values of model cycle time and leadtime, and sizes of x, y, and level.
                for attr in ['FcstTime_hour', 'x', 'y', 'level', 'leadtime']:
                    try:
                        if self.metadata[attr] != nc_handle.variables[v_name].getncattr(attr):
                            match = False
                            break
                    except:
                        pass
            if match: #names and order of ancillary variables, including white space.
                if ancillary_variables != nc_handle.variables[v_name].getncattr('ancillary_variables'):
                    match = False
                    break
            #if match:
            #    if not np.array_equal(self.get_forecast_reference_time().data[:], \
            #        nc_handle.variables['FcstRefTime'][:].data[:]):
            #        match = False
            if match:
                return v_name

        #Write the variable into the netCDF file.
        logging.info("Writing " + variable_name + " into the netCDF file.")
        nc_var = nc_handle.createVariable(
            variable_name,
            dtype,
            tuple(self.dimensions),
            chunksizes=chunksize,
            zlib=True,
            complevel=4,
            shuffle=False,
            fill_value=fill_value)

        #Add the metadata
        try:
            self.metadata.pop('SOSA__usedProcedure')
        except KeyError:
            pass
        self._add_nc_metadata(nc_var) #add variable's metadata entries as attributes

        if not self.is_feature_of_interest(): #add variables's preprocesses and processesas attributes
            preprocess_str = self.get_preprocess_str()
            preprocess_list = preprocess_str.split(space)
            preprocess_unique = []
            for proc in preprocess_list:
                if proc not in preprocess_unique:
                    preprocess_unique.append(proc)
            process_str = (space.join(preprocess_unique))
            setattr(nc_var, "PROV__wasInformedBy", process_str)
            process_str = self.get_process_str()
            setattr(nc_var, "SOSA__usedProcedure", process_str)

        #add variable's data
        self.add_nc_data(nc_var)

        #Return the variable name written into the netCDF file
        return variable_name


    def add_to_database(self, filename, file_id=None):
        """Add variable information into the database to facilitate
        accessing its data."""

        #Exclude feature of interests.
        if self.is_feature_of_interest():
            return

        #Exclude components.  Components have their attribute dimensions tuple
        #stripped of elements.
        if not len(self.dimensions):
            return

        #Glean information to be inserted into database.

        #Get variable name.
        var_name = self.get_variable_name()

        #Get time information: start, end, duration, duration_method.
        #First, get start and end.
        try: #get the phenomenon time or phenonomenon time period
            ptime = self.get_phenom_time()
        except IndexError:
            raise AttributeError("No PhenomenonTime")
        ftime = self.get_forecast_reference_time() #get forecast reference time
        if ftime is not None:
            start = ftime.get_start_time() #use the forecast reference time as start
        else:
            start = ptime.get_start_time() #if not forecast ref time, then use the
                                           #phenomenon time or phenomenon time period.
        # Returns date in datetime format, so convert to epoch
        start=Time.epoch_time(start) #convert start from datetime to epoch time.
        end=ptime.get_end_time() #end obtained from the phenomenon time/phenomenon time period
        end=Time.epoch_time(end) #convert end from datetime to epoch time.

        #Second, get time duration and duration method
        try:
            btime = [t for t in self.time if t.name=='OM__phenomenonTimePeriod'][0]
            duration = btime.get_duration()
            time_dim = cfg.read_dimensions()['time']
            duration_method = self.get_cell_methods()[time_dim]
        except IndexError:
            duration = 0
            duration_method = None

        #Get coordinate information: vert_coord1, vert_coord2, and vert_method.
        vertical = self.get_coordinate()
        if type(vertical) is tuple: # then is bounds
            vert_coord1, vert_coord2 = vertical
            vert_method = None

            try: #bounded by elevation
                elev_dim = cfg.read_dimensions()['elev']
                vert_method = self.get_cell_methods()[elev_dim]
                vert_units = 'm'
            except:
                pass

            try: #bounded by pressure levels (isobars)
                plev_dim = cfg.read_dimensions()['plev']
                vert_method = self.get_cell_methods()[plev_dim]
                vert_units = 'mb'
            except:
                pass

            assert vert_method is not None

        elif vertical is not None: #vertical level
            vert_coord1 = vertical
            vert_coord2 = None
            vert_method = None
        else: #in case no coordinate value obtained.
            vert_coord1 = None
            vert_coord2 = None
            vert_method = None

        #Get variable type, whether it is defined at stations or on a grid.
        reserved1 = None
        if self.is_vector():
            reserved1 = "vector"
        else:
            reserved1 = "grid"

        #Get information to be stored in field 'reserved2' that is held
        #in the variable's properties attribute, usually the lead time.
        reserved2 = None
        if 'reserved2' in self.properties:
            if not type(self.properties['reserved2']) == str:
                res2 = str(self.properties['reserved2']) 
            reserved2 = (res2)
        #Add smooth information to database if present in metadata
        if 'smooth' in self.metadata:
            smooth = int(self.metadata['smooth'])
        else:
            smooth = None

        #Get Source information. If Source is None, raise error with information about variable
        src = self.get_source()
        logging.info("Adding "+var_name+" to database.")
        if src is None:
            pdb.set_trace()
            raise ValueError("Source for "+var_name+" returned as "+str(src)+". A source is required.")

        #With the information collected, insert it into the database table 'variable'
        #for variable 'name'.
        db.insert_variable(property=self.get_observedProperty(),
                           source=src,
                           start=start,
                           end=end,
                           duration=duration,
                           duration_method=duration_method,
                           vert_coord1=vert_coord1,
                           vert_coord2=vert_coord2,
                           vert_method=vert_method,
                           file_id=file_id,
                           smooth=smooth,
                           filename=filename,
                           name=var_name,
                           reserved1=reserved1,
                           reserved2=reserved2)


    def get_chunk_size(self):
        """Return an appropriate chunk size tuple given internal data."""

        if self.data is None:
            return None

        if len(self.dimensions) > 0:
            chunksizes = []
            for n,d in enumerate(self.dimensions):
                if d in ["x","y","number_of_stations"]:
                    chunksizes.append(self.data.shape[n])
                else:
                    chunksizes.append(1)
            return tuple(chunksizes)

        else:
            return None


    def check_correct_shape(self):
        """Check that the variable dimensions are consistent with the shape of its data."""

        if self.data is not None and self.data.size > 0 \
                and len(self.data.shape) != len(self.dimensions):
            logging.error(
                "dimensions of data not equal to dimensions attribute")
            logging.error('len of shape is: ' + str(len(self.data.shape)))
            logging.error('len of dims  is: ' + str(len(self.dimensions)))
            logging.error("Will not write " + self.name)

            raise ValueError


    def add_nc_data(self, nc_var):
        """Assign the netCDF variable data to the variable's data."""

#        try:
#            if self.data is None:
#                nc_var[:] = 0
#            else:
#                nc_var[:] = self.data
#        except IndexError as e:
#            logging.error("Cant assign data to netCDF Variable")
#            raise
        if self.data is not None:
            nc_var[:] = self.data


    def get_cell_methods(self):
        """Return a dictionary of cell methods used to create the variable."""

        #The methods must exist in variable's metadata
        if 'cell_methods' not in self.metadata:
            return None

        methods_dict = {}
        cm_str = self.metadata['cell_methods'] #assumed comma-separated string
        methods = cm_str.split(",")
        for method_str in methods: #colon separates dimension name from cell method
            key_val = method_str.split(':')
            dimension = key_val[0].strip(' ')
            cell_method = key_val[1].strip(' ')
            methods_dict[dimension] = cell_method

        return methods_dict


    def check_dimensions(self, nc_handle):
        """Match by name and size each dimension of the variable with one existing
        in the netCDF Dataset object.  If there is no match, create a matching
        dimension in the netCDF Dataset object.  If necessary, the variable dimension's
        name may be changed to be the same as its counterpart in netCDF Dataset dimensions.
        """

        #Return if variable data does not exist.
        if self.data is None:
            return

        #Commence the matching/creating of dimensions
        shape = self.data.shape
        for index, (dim, size) in enumerate(zip(self.dimensions, shape)): #loop through variable's dimensions
            nc_dim_size = len(nc_handle.dimensions[dim]) #get size of netCDF Dataset dimension with matching name.
            #Match occurs if sizes are equal and on to next dimension in loop.  But if sizes don't match ...
            if size != nc_dim_size:
                #Seek a match with all existing dimensions where the variable dimension name is a
                #substring of netCDF Dataset dimension name.
                for nc_dim in list(nc_handle.dimensions.keys()):
                    nc_dim_size = len(nc_handle.dimensions[nc_dim])
                    if dim in nc_dim and nc_dim_size == size: #substring and sizes match, so force names to match
                        self.dimensions[index] = nc_dim       #by setting dimension name to that of its netCDF Dataset.
                        return                                #counterpart and return(!).  NOTE: 'return' to 'break'?
                #At this point, no netCDF Dataset dimension size matches that of the current variable dimension
                try: #create a new dimension for netCDF Dataset and rename its counterpart in the variable.
                    count = 1
                    while True: #loop thru netCDF dimension names with substring '_alt', till KeyError
                        alt_dim_name = dim + "_alt" + str(count)
                        count += 1
                        nc_dim_size = len(nc_handle.dimensions[alt_dim_name]) #KeyError possible.
                        if size == nc_dim_size:
                            self.dimensions[index] = alt_dim_name
                            return
                except KeyError: #rename the variable's dimension and create a netCDF counterpart.
                    self.dimensions[index] = alt_dim_name
                    self.create_dimension(nc_handle, alt_dim_name)


    def _add_nc_metadata(self, nc_var):
        """Adds, with some processing, the variable's metadata to netCDF file handle."""

        for name, value in list(self.metadata.items()):
            if name != 'name' and name != 'fill_value': #skip name and fill_value
                if type(value) is str:  #To prevent 'string' prefix
                    value = str(value)
                #If feature of interest, skip the following metadata attributes
                if db.get_property(self.name, 'feature_of_interest'):
                    if name == 'OM__observedProperty':
                        continue
                    if name == 'ancillary_variables':
                        continue
                #If vector data, skip grid_mapping attribute
                if name == 'grid_mapping' and \
                        self.is_vector() == True:
                    continue
                if name == 'bounds':
                    continue
                if name == 'leadtime':
                    value = value
                setattr(nc_var, name, value)


    def get_source(self):
        """Return the source metadata attribute."""

        #if 'source' in self.metadata.keys():
        #    return os.path.basename(self.metadata['source'])
        if 'PROV__Used' in self.metadata:
            if isinstance(self.metadata['PROV__Used'], list):
                return os.path.basename(' '.join(self.metadata['PROV__Used']))
            else:
                return os.path.basename(self.metadata['PROV__Used'])
        else:
            for proc in self.preprocesses:
                if 'PROV__Used' in proc.attributes:
                    return os.path.basename(proc.attributes['PROV__Used'])
                elif 'source' in proc.attributes:
                    return os.path.basename(proc.attributes['source'])
            for proc in self.processes:
                if 'PROV__Used' in proc.attributes:
                    return os.path.basename(proc.attributes['PROV__Used'])
                elif 'source' in proc.attributes:
                    return os.path.basename(proc.attributes['source'])

        return None


    def is_observation(self):
        """Returns True if the Source is an observation.
        Current observation sources: 'METAR', 'MARINE'.
        """

        obs = ['METAR', 'MARINE']
        return self.get_source() in obs


    def is_model(self):
        """Returns True if the Source is from a model.
        Current model sources: 'GFS', 'GFS13', 'NAM'
        """

        models = ['NAM', 'GFS', 'GFS13']
        return self.get_source() in models


    def is_vector(self):
        """Returns if self is is a vector dataset.
        """
        #This isn't really a good check for if something is vector.  We don't
        #always use 'nstations' in dimensions for vector data.  Especially
        #when it is model vector data. We do however use some form of the word
        #"station"
        #if cfg.read_dimensions()['nstations'] in self.dimensions:
        #    return True
        #---------------------------------------------------
        # New code
        #---------------------------------------------------
        sub = 'station'
        res = [x for x in self.dimensions if re.search(sub, x)]
        if len(res) > 0:
            return True

        return False


    def get_fill_value(self):
        """Return fill_value metadata attribute"""

        try:
            fill_value = self.metadata['fill_value']
        except KeyError:
            logging.debug('Using default fill value: ' + str(FILL_VALUE))
            fill_value = FILL_VALUE

        return fill_value


    def get_process_str(self):
        """Returns a string representation of the processes.
        i.e. A comma separated name of the process enclosed in parentheses.
        """

        process_str = "( "
        for proc in self.processes:
            process_str += proc.name + " "
        process_str = process_str[0:-1] + " )"

        return process_str


    def get_preprocess_str(self):
        """Returns a string representation of the preprocesses.
        i.e. A comma separated name of the process enclosed in parentheses.
        """

        process_str = "( "
        for proc in self.preprocesses:
            process_str += proc.name + " "
        process_str = process_str[0:-1] + " )"

        return process_str


    def add(self, other, axis=1):
        """Add the data of other Camps_data object to self."""

        # Correct shape
        while len(other.data.shape) <= axis:
            #other.data = np.array([other.data])
            other.data = np.ma.array([other.data])

        while len(self.data.shape) <= axis:
            #self.data = np.array([self.data])
            self.data = np.ma.array([self.data])

        if len(other.data.shape) != len(self.data.shape):
            raise ValueError("all input arrays must have the same shape")

        #new_data = np.concatenate((self.data, other.data),axis-1)
        new_data = np.ma.concatenate((self.data, other.data),axis-1)
        return new_data


    def __add__(self, other):
        """Defines how one adds two camps data objects using '+' sign."""

        #Types must match.
        if type(other) != type(self):
            raise TypeError("Types do not match")

        #Names of variables must match.
        if self.name != other.name:
            raise Exception("Attempt to combine different variables failed")

        #Add variable data
        if self.data is not None and other.data is not None:
            new_data = self.add(other)
            self.data = new_data

        #Add times
        self.add_times(other)

        #Add metadata
        for i in self.metadata:
            for j in other.metadata:
                pass

        return self


    def add_times(self, other):
        """Add time objects of same type."""

        for i in self.time:
            for j in other.time:
                if type(i) == type(j):
                    i = i + j
        for k in range(len(self.components)):
            self.components[k].add_times(other.components[k])

    def __getattr__(self, name):
        """Returns metadata using '.' operator"""
        if name in self.metadata:
            return self.metadata[name]
        else:
            raise AttributeError

    def __copy__(self):
        """Creates a copy of the object"""
        cls = self.__class__
        result = cls.__new__(cls)
        result.__dict__.update(self.__dict__)
        return result


    # TODO
    #def __eq__(self, other):

    def __str__(self):
        """Format of response to command self.name."""

        obj_str = "\n***** " + self.name + " ******\n*\n"
        obj_str += "* dtype               : " + str(self.data.dtype) + "\n"
        obj_str += "* processes           : " + self.get_process_str() + "\n"
        obj_str += "* dimensions          : " + str(self.dimensions) + "\n"
        if coord_str in self.metadata:
            obj_str += "* level               : "
            try:
                obj_str += str(self.get_coordinate()) + "\n"
            except:
                obj_str += "\n"
        obj_str += "Metadata:\n"
        for k, v in list(self.metadata.items()):
            num_chars = len(k)
            obj_str += "* " + k
            obj_str += " " * (20 - num_chars)
            obj_str += ": " + str(v) + "\n"

        obj_str += "\n"
        obj_str += "Shape: \n" + str(self.data.shape) + "\n"
        obj_str += "Data: \n"
        obj_str += str(self.data)[:20] + '\n'
        obj_str += str(self.data)[-20:] + '\n'

        return obj_str


#Object representation set by __str__ above.
    __repr__ = __str__

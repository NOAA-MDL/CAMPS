import sys
import os
import numpy as np
import pdb
import re
import logging
from netCDF4 import Dataset
file_dir = os.path.dirname(os.path.realpath(__file__))
relative_path = "/.."
path = os.path.abspath(file_dir + relative_path)
sys.path.insert(0, path)
from nc_writable import nc_writable
from Process import Process
import Time
import registry.util as cfg
import registry.db.db as db
import registry.constants as const


FILL_VALUE = 9999
coord_str = 'coordinates'


class Wisps_data(nc_writable):
    """
    WISPS data object for storing metadata and accompanied objects
    that describe the variable. This class will attempt to
    gather information from the database on a given property, but
    any gaps will need to be provided by the user
    """

    def __init__(self, name, autofill=True):
        """
        Initializes object properties and adds metadata from the database
        coresponding to the name.
        """
        self.name = name
        self.data = np.array([])
        self.dimensions = []  # The name of the dimensions
        self.processes = []
        self.metadata = {}
        self.time = []
        self.properties = {}
        if autofill:
            self.add_db_metadata()

    # Coordinates
    def has_plev(self):
        """
        Checks metadata to see if this has plev.
        """
        if const.COORD in self.metadata:
            return const.PLEV in self.metadata[const.COORD]

    def has_elev(self):
        """
        Checks metadata to see if this has elev.
        """
        if const.COORD in self.metadata:
            return const.ELEV in self.metadata[const.COORD]

    def has_bounds(self):
        """
        Checks metadata to see if this variable has a bounds attribute.
        """
        return 'bounds' in self.metadata

    def has_time_bounds(self):
        """
        Checks metadata to see if this variable time bounds.
        """
        return 'hours' in self.properties or db.get_property(self.name, 'hours') is not None
   
    def has_plev_bounds(self):
        """
        Returns True if metadata indicates variable has plev bounds.
        """
        if self.has_bounds():
            return self.metadata['bounds'] == 'plev_bounds'

    def has_elev_bounds(self):
        """Returns True if metadata indicates variable has plev bounds.
        """
        if self.has_bounds():
            return self.metadata['bounds'] == 'elev_bounds'

    def get_coordinate(self):
        """Returns the value of the coordinate data if it has
        one. If this variable is a bounds, return a tuple of the bounds.
        Otherwise return None"""
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
        if self.has_plev() or self.has_elev():
            try:
                coord = self.properties['coord_val']
            except:
                coord = db.get_property(self.name, 'coord_val')
            coord = int(coord)
            return coord
        return None

    def get_time_bounds(self):
        if not self.has_time_bounds():
            return None
        for i in self.time:
            if i.name == 'OM_phenomenonTimePeriod':
                return i
    
    def get_lead_time(self):
        """Returns leadTime if it exists."""
        lead_type = Time.LeadTime
        return get_time(lead_type)

    def get_result_time(self):
        """Returns resultTime if it exists."""
        result_type = Time.ResultTime
        return get_time(result_type)

    def get_phenom_time(self):
        """Returns instant or period phenomenon time if it exists"""
        phenom_type = Time.PhenomenonTime
        time = self.get_time(phenom_type)
        if time:
            return time
        phenom_period_type = Time.PhenomenonTimePeriod
        time = self.get_time(phenom_period_type)
        if time:
            return time
        return None

    
    def get_time(self, time_type):
        """Returns a time of type time_type or None if there's no such instance
        """
        time_arr = filter(lambda time: type(time) is time_type, self.time)
        if len(time_arr) == 0:
            return None
        if len(time_arr) > 1:
            logging.warning("More than one " + time_type +
                    " time describing " + self.name)
        return time_arr[0] 

    def add_process(self, process):
        """
        Adds a Process object to the Processes list or creates one if given a str.
        """
        if process.__class__ is not Process and type(process) is str:
            process = Process(process)
        self.processes.append(process)
        return self

    def add_data(self, data):
        """
        Given a numpy array with the correct dimensions,
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
        return self

    def get_data_type(self):
        """Check if data_type is defined in the properties
        database for this variable name. Return value if available,
        otherwise throw ValueError.
        """
        try:
            return self.properties['data_type']
        except:
            return db.get_property(self.name, 'data_type')

    def get_dimensions(self):
        """Check if dimensions is defined in the properties
        database for this variable name. Return value if available,
        otherwise throw ValueError.
        """
        var = cfg.read_variables()[self.name]
        dimensions = var['dimensions']
        return dimensions

    def get_observedProperty(self):
        """Returns the parsed OM_observedProperty metadata
        element.
        """
        op = self.metadata['OM_observedProperty']
        if op[-1] == '/':
            op = op[0:-1]
        return os.path.basename(op)

    def change_data_type(self, data_type=None):
        """
        Attempts to force the datatype to change for this data
        """
        if data_type is not None:
            self.data = self.data.astype(data_type)
        else:
            self.data = self.data.astype(self.get_data_type())

    def set_dimensions(self, dimensions=None):
        """
        Given a tuple of String dimensions, sets object to the
        dimensions.
        """
        if not dimensions:
            dimensions = self.get_dimensions()
            dimensions = tuple(dimensions)
        if type(dimensions) is not tuple:
            logging.error(type(dimensions), "is not of type tuple")
            raise TypeError
        if len(self.dimensions) > 0:
            logging.warning("overwriting dimensions")
        self.dimensions = dimensions
        return self

    def add_db_metadata(self):
        """
        Reads the metadata database and copies the metadata to
        this object.
        """
        meta_dict = {}
        try:
            meta_dict = db.get_all_metadata(self.name)
        except ValueError:
            logging.warning("'" + self.name + "' not defined in metadata db")
        self.metadata = meta_dict

    def add_metadata(self, key, value):
        """
        Given a key and value, adds it to the metadata
        """
        self.metadata[key] = value
        return self

    def add_source(self, value):
        """
        Sets the LE_Source attribute to 'value'.
        """
        self.metadata['LE_Source'] = value

    def add_leadTime(self, value):
        """
        Sets the LeadTime_hour attribute to 'value'.
        """
        self.metadata['LeadTime_hour'] = value

    def add_fcstTime(self, value):
        """
        Sets the LE_Source attribute to 'value'.
        """
        self.metadata['FcstTime_hour'] = value

    def add_plev_attributes(self, plev_var):
        """
        Adds Common Plev attributes.
        """
        setattr(plev_var, 'long_name', 'pressure')
        setattr(plev_var, 'units', 'hPa')
        setattr(plev_var, 'standard_name', 'air_pressure')
        setattr(plev_var, 'positive', 'down')
        setattr(plev_var, 'axis', 'Z')

    def add_elev_attributes(self, elev_var):
        """
        Adds Common elev attributes.
        """
        setattr(elev_var, 'long_name', 'height above surface')
        setattr(elev_var, 'units', 'm')
        setattr(elev_var, 'standard_name', 'height')
        setattr(elev_var, 'positive', 'up')
        setattr(elev_var, 'axis', 'Z')

    def in_metadata(self, var):
        """Boolean weather var is in metadata dictionary"""
        return var in self.metadata

    def get_variable_name(self):
        """Returns a uniqueish vairable name such that it looks like,
        <dataSource>_<observedProperty>_<duration>_<verticalCoord>_<fcstReferenceTime>_<fcstLeadTime>_<########>
        """
        # Write dataSource
        name = ""
        try:
            name += self.metadata['LE_Source']
        except:
            pass
        name += '_'

        # Write observedProperty
        try:
            name += self.get_observedProperty()
        except:
            pass
        name += '_'

        # Write duration
        if self.has_time_bounds():
            bounds = self.get_time_bounds()
            name += str(bounds.get_duration())
        else:
            name += 'instant'
        name += '_'

        # Write verticalCoordinate
        if self.has_plev() or self.has_elev():
            level = self.get_coordinate()
            if type(level) is tuple:
                level = level[0]
            name += str(level)
        name += '_'

        # Write fcstReferenceTime
        try:
            name += str(self.metadata['FcstTime_hour'])
        except:
            pass
#        name += '_'


        # Write LeadTime
#        try:
#            name += str(self.metadata['LeadTime_hour'])
#        except:
#            pass
        return name

    def get_coord_name(self, nc_handle, coord_name, is_bounds=False):
        """
        Given a 'coord_name' such as plev or elev, finds if
        a variable already fits the coordinate for this object.
        If one is not found, returns a new, unique name.
        """
        coord_data = self.get_coordinate()
        num = 0
        all_vars = nc_handle.variables
        # Find all plev variables already written
        for v in all_vars.keys():
            if re.match(r'^' + coord_name + '\d+$',  v, re.I):
                # Check if coordinate already exists
                if is_bounds:
                    first_num_matches = coord_data[0] == all_vars[v][1]
                    second_num_matches = coord_data[1] == all_vars[v][1]
                    if first_num_matches and second_num_matches:
                        return (already_exists, v)
                else:
                    first_num_matches = coord_data == all_vars[v][0]
                    if coord_data == all_vars[v][0]:
                        already_exists = True
                        return (already_exists, v)
                # Found a coordinate, but it didn't match this object's
                num += 1

        name = coord_name + str(num)
        already_exists = False
        return (already_exists, name)

    def create_dimensions(self, nc_handle):
        """Check if self.dimensions are defined in the netcdf file.
        If they are not create them.
        """
        dims = nc_handle.dimensions
        for d in self.dimensions:
            if d not in dims:
                self.create_dimension(nc_handle, d)

    def write_coordinate(self, nc_handle):
        """
        Determines which coordinate needs to be written to
        it's own variable and calls the assosiated function.
        A bounds function will always supercede the non-bounds function.
        """
        success = False
        if self.has_plev_bounds():
            success = self.write_plev_bounds(nc_handle)
        elif self.has_elev_bounds():
            success = self.write_elev_bounds(nc_handle)
        elif self.has_plev():
            success = self.write_plev(nc_handle)
        elif self.has_elev():
            success = self.write_elev(nc_handle)

        if self.has_time_bounds():
            success = self.write_time_bounds(nc_handle)
            self.add_bounds_process()


        return success
    
    def add_bounds_process(self):
        """Adds a process representing the cell_method"""
        cell_type = self.metadata['cell_methods'].split(':')[1].strip(' ')
        if cell_type == 'minimum':
            self.add_process('BoundsProcMin')
        elif cell_type == 'maximum':
            self.add_process('BoundsProcMax')
        elif cell_type == 'sum':
            self.add_process('BoundsProcSum')
    
    def write_elev_bounds(self, nc_handle):
        """
        Writes the elev_bounds variable.
        """
        elev = 'elev'
        nv = 'nv'
        # Turn the data into a numpy array and
        # Reshape so that it has a shape of 1,2 for elev,nv
        coord_data = self.get_coordinate()
        coord_data = np.array(coord_data).reshape(1, 2)

        exists, name = self.get_coord_name(nc_handle, 'elev_bounds')
        self.metadata[coord_str] = name
        if not exists:
            if elev not in nc_handle.dimensions:
                nc_handle.createDimension(elev, 1)
            if nv not in nc_handle.dimensions:
                nc_handle.createDimension(nv, 2)
            elev_var = nc_handle.createVariable(name, int, (elev, nv))
            # Probably need this defined:
            # self.add_elev_bounds_attributes(elev_var)
            elev_var[:] = coord_data
        return True

    def write_time_bounds(self, nc_handle):
        """
        Writes the Time bounds variable
        """
        try:
            hours = self.properties['hours']
        except:
            hours = db.get_property(self.name, 'hours')
        hours = int(hours)
        #b_time = Time.BoundedTime(start_time=self.time[0].get_start_time(
        #), end_time=self.time[0].get_end_time(), period=hours)
        #self.time.append(b_time)
        b_time = Time.PhenomenonTimePeriod(start_time=self.time[0].get_start_time(
        ), end_time=self.time[0].get_end_time(), period=hours)
        self.time.append(b_time)

        # Remove instant Phenom time if it's there
        phenom_type = Time.PhenomenonTime
        for i,t in enumerate(self.time):
            if type(t) is phenom_type:
                self.time.pop(i)

        t = self.get_phenom_time()

    def write_plev_bounds(self, nc_handle):
        """
        Writes the pressure level variable.
        """
        plev = 'plev'
        nv = 'nv'
        # Turn the data into a numpy array and
        # Reshape so that it has a shape of 1,2 for plev,nv
        coord_data = self.get_coordinate()
        coord_data = np.array(coord_data).reshape(1, 2)

        # Determine if the variable already exists.
        # Return the existing name, or a new one.
        exists, name = self.get_coord_name(nc_handle, 'plev_bounds')
        self.metadata[coord_str] = name
        if not exists:
            if plev not in nc_handle.dimensions:
                nc_handle.createDimension(plev, 1)
            if nv not in nc_handle.dimensions:
                nc_handle.createDimension(nv, 2)
            plev_var = nc_handle.createVariable(name, int, (plev, nv))
            # Probably need this defined:
            # self.add_plev_bounds_attributes(plev_var)
            plev_var[:] = coord_data
        return True

    def write_elev(self, nc_handle):
        """
        Writes the pressure level variable.
        Changes the name to plev[n] where n a number
        when there are multiple plev variables.
        """
        elev = 'elev'
        exists, name = self.get_coord_name(nc_handle, elev)
        self.metadata[coord_str] = name
        if not exists:
            if elev not in nc_handle.dimensions:
                nc_handle.createDimension(elev, 1)
            elev_var = nc_handle.createVariable(name, int, (elev))
            self.add_elev_attributes(elev_var)
            elev_var[:] = self.get_coordinate()
        return True

    def write_plev(self, nc_handle):
        """
        Writes the pressure level variable.
        Changes the name to plev[n] where n a number
        when there are multiple plev variables.
        """
        exists, name = self.get_coord_name(nc_handle, 'plev')
        self.metadata[coord_str] = name
        if not exists:
            if 'plev' not in nc_handle.dimensions:
                nc_handle.createDimension('plev', 1)
            plev_var = nc_handle.createVariable(name, int, ('plev'))
            self.add_plev_attributes(plev_var)
            plev_var[:] = self.get_coordinate()
        return True

    def reshape(self, coord_name):
        """
        Reshapes the data when adding the a coordinate dimension.
        """
        # Don't do anything if it's in coordinates of time
        if 'plev' not in coord_name or 'elev' not in coord_name:
            return
        self.dimensions.append(coord_name)

        # Change to a list to append extra dimension to shape
        shape = self.data.shape
        new_shape = list(shape)
        new_shape.append(1)
        new_shape = tuple(new_shape)

        # This will add a dimension with length 1 at the end
        # e.g. (1200, 25000) becomes (1200, 25000, 1)
        self.data = self.data.reshape(new_shape)

    def create_dimension(self, nc_handle, dimension_name):
        """
        Creates a netCDF dimension for each of the individual
        dimensions in the object.
        """
        index = self.dimensions.index(dimension_name)
        dim_length = self.data.shape[index]
        nc_handle.createDimension(dimension_name, dim_length)

    def write_to_nc(self, nc_handle):
        """
        Adds a netCDF variable to the nc_handle.
        Includes the data and metadata associated with the object.
        """
        logging.info("writing " + self.name)
        # This will include all netcdf variables that in some way help
        # describe this variable.
        ancillary_variables = ""

        # Writes the elev, plev, and bounds variables if they exist
        success = self.write_coordinate(nc_handle)
        if success:  # modify the shape of the data to accommodate coordinate.
            self.reshape(self.metadata[coord_str])

        # Tell the Process objects and Time Objects
        # to write to the file
        for t in self.time:
            time_name = t.write_to_nc(nc_handle)
            ancillary_variables += time_name + " "

        for p in self.processes:
            p.write_to_nc(nc_handle)
            ancillary_variables += p.name + " "

        self.metadata['ancillary_variables'] = ancillary_variables

        self.check_correct_shape()

        # Check if dimensions are defined in the netCDF file.
        # If they are not, create them.
        self.create_dimensions(nc_handle)

        # Check if the dimension sizes are in agreement
        self.check_dimensions(nc_handle)

        fill_value = self.get_fill_value()

        # Get a variable name and make it unique if needed
        variable_name = self.get_variable_name()
        if variable_name in nc_handle.variables:
            counter = 1
            while variable_name + str(counter) in nc_handle.variables:
                counter += 1
            variable_name = variable_name + str(counter)

        # Get the chunksize
        chunksize = self.get_chunk_size()

        # Create the variable
        nc_var = nc_handle.createVariable(
            variable_name,
            self.data.dtype,
            tuple(self.dimensions),
            chunksizes=chunksize,
            zlib=True,
            complevel=4,
            shuffle=False,
            fill_value=fill_value)

        # Add the metadata
        self.add_nc_metadata(nc_var)

        # Write the processes attribute string
        process_str = self.get_process_str()
        setattr(nc_var, "OM_procedure", process_str)

        self.add_nc_data(nc_var)

        return variable_name

    def add_to_database(self, filename):
        """Add variable to the database for searching.
        """
        var_name = self.get_variable_name()
        # There should always be a phenomenonTime
        try:
            ptime = self.get_phenom_time()
        except IndexError:
            raise AttributeError("No PhenomenonTime")
        # Returns date in datetime format
        # Change to YYYYMMDDHHMM
        start=ptime.get_start_time()
        start=Time.epoch_time(start)
        #start = start.strftime("%Y%m%d%H%S")
        end=ptime.get_end_time()
        end=Time.epoch_time(end)
        #end = end.strftime("%Y%m%d%H%S")
        try:
            btime = filter(lambda t: t.name=='OM_phenomenonTimePeriod', self.time)[0]
            duration = btime.get_duration()
            time_dim = cfg.read_dimensions()['time']
            duration_method = self.get_cell_methods()[time_dim]
        except IndexError:
            duration = None
            duration_method = None

        vertical = self.get_coordinate()
        if type(vertical) is tuple: # then is bounds
            vert_coord1, vert_coord2 = vertical
            vert_method = None
            try:
                elev_dim = cfg.read_dimensions()['elev']
                vert_method = self.get_cell_methods()[time_dim]
            except:
                pass
            try:
                plev_dim = cfg.read_dimensions()['plev']
                vert_method = self.get_cell_methods()[time_dim]
            except:
                pass
            assert vert_method is not None
        elif vertical is not None:
            vert_coord1 = vertical
            vert_coord2 = None
            vert_method = None
        else:
            vert_coord1 = None
            vert_coord2 = None
            vert_method = None


        db.insert_variable(property=self.get_observedProperty(),
                           source=self.metadata['LE_Source'],
                           start=start,
                           end=end,
                           duration=duration,
                           duration_method=duration_method,
                           vert_coord1=vert_coord1,
                           vert_coord2=vert_coord2,
                           vert_method=vert_method,
                           filename=filename,
                           name=var_name)
                           

    def get_chunk_size(self):
        shape = list(self.data.shape)
        if len(shape) == 4:
            shape[2] = 1
            shape[3] = 1
            return tuple(shape)
        return None


    def check_correct_shape(self):
        # Check that the dimensions are correct for the shape of the data
        if len(self.data.shape) != len(self.dimensions):
            logging.error(
                "dimensions of data not equal to dimensions attribute")
            logging.error("Will not write " + self.name)
            raise ValueError

    def add_nc_data(self, nc_var):
        """
        Time intensive. See netCDF4.Variable.__setitem__
        """
        try:
            nc_var[:] = self.data
        except IndexError as e:
            print e

    def get_cell_methods(self):
        """Return a dictionary representing cell methods, where the
        key is the coordinate that the cell method modifies, and the 
        value is the method itself.
        """
        if 'cell_methods' not in self.metadata:
            return None
        methods_dict = {}
        cm_str = self.metadata['cell_methods']
        methods = cm_str.split(",")
        for method_str in methods:
            key_val = method_str.split(':')
            dimension = key_val[0].strip(' ')
            cell_method = key_val[1].strip(' ')
            methods_dict[dimension] = cell_method
        return methods_dict


    def check_dimensions(self, nc_handle):
        """Check data dimension shape is equal to the nc handle dimension.
        """
        shape = self.data.shape
        # Loop through dimension
        for index, (dim, size) in enumerate(zip(self.dimensions, shape)):
            nc_dim_size = len(nc_handle.dimensions[dim])
            if size != nc_dim_size:
                # Find if one has already been created
                for nc_dim in nc_handle.dimensions.keys():
                    nc_dim_size = len(nc_handle.dimensions[nc_dim])
                    if dim in nc_dim and nc_dim_size == size:
                        self.dimensions[index] = nc_dim
                        return
                # Or create an new one
                try:
                    count = 1
                    while True:
                        alt_dim_name = dim + "_alt" + str(count)
                        count += 1
                        nc_dim_size = len(nc_handle.dimensions[alt_dim_name])
                        if size == nc_dim_size:
                            self.dimensions[index] = alt_dim_name
                            return
                except KeyError:
                    self.dimensions[index] = alt_dim_name
                    self.create_dimension(nc_handle, alt_dim_name)

    def add_nc_metadata(self, nc_var):
        for name, value in self.metadata.iteritems(): 
            if name != 'name' and name != 'fill_value': # skip name and fill_value
                if type(value) is unicode:  # To prevent 'string' prefix
                    value = str(value)
                if name == 'OM_observedProperty' and \
                        db.get_property(self.name, 'feature_of_interest'):
                    continue
                setattr(nc_var, name, value)

    def get_source(self):
        """Return the source metadata attribute.
        """
        return self.metadata['LE_Source']

    def is_model(self):
        """Returns True if the Source is from a model.
        Currently, 'GFS' and 'NAM'
        """
        models = ['NAM', 'GFS']
        return self.get_source() in models

    def get_fill_value(self):
        """Return fill_value metadata attribute"""
        try:
            fill_value = self.metadata['fill_value']
        except KeyError:
            fill_value = FILL_VALUE
        return fill_value

    def get_process_str(self):
        """
        Returns a string representation of the process.
        i.e. A comma separated name of the process enclosed in parens.
        """
        process_str = "( "
        for proc in self.processes:
            process_str += proc.name + ","
        process_str = process_str[0:-1] + ' )'
        return process_str

    def __add__(self, other):
        if type(other) != type(self):
            raise TypeError("Types do not match")
        if name != other.name:
            raise Exception("Attempt to combine different variables failed")
        # Add data
        self.data = self.data + other.data

        # Add times
        for i in self.time:
            for j in other.time:
                if i == j:
                    i = i + j

        # Add metadata
        return self

    def __str__(self):
        obj_str = "\n***** " + self.name + " ******\n*\n"
        obj_str += "* dtype               : " + str(self.data.dtype) + "\n"
        obj_str += "* processes           : " + self.get_process_str() + "\n"
        obj_str += "* dimensions          : " + str(self.dimensions) + "\n"
        if coord_str in self.metadata:
            obj_str += "* level               : " + \
                str(self.get_coordinate()) + "\n"
        obj_str += "Metadata:\n"
        for k, v in self.metadata.iteritems():
            num_chars = len(k)
            obj_str += "* " + k
            obj_str += " " * (20 - num_chars)
            obj_str += ": " + str(v) + "\n"

        obj_str += "Data: \n"
        obj_str += str(self.data)

        return obj_str

    __repr__ = __str__

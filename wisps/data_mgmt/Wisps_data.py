import sys, os
#sys.path.insert(0,os.path.abspath('..'))
file_dir = os.path.dirname(os.path.realpath(__file__))
relative_path = "/.."
path = os.path.abspath(file_dir + relative_path)
sys.path.insert(0, path)
import numpy as np
import Location
from nc_writable import nc_writable 
from Process import Process
from netCDF4 import Dataset
from Time import Time
import pdb
import re
import registry.util as cfg
import registry.db.db as db


FILL_VALUE = 9999
coord = 'coordinates'

class Wisps_data(nc_writable):

 
    def __init__(self, name):
        """
        Initializes object properties and adds metadata from the database
        coresponding to the name.
        """
        self.name = name
        self.data = np.array([])
        self.dimensions = [] # The name of the dimensions
        self.processes = []
        self.metadata = {}
        self.time = []
        self.add_db_metadata()

        # Coordinates
        #self.plev = get_plev()
        #self.
        
    def has_plev(self):
        """ 
        Checks metadata to see if this has plev.
        """
        if coord in self.metadata:
            return self.metadata[coord] == 'plev'

    def has_elev(self):
        """ 
        Checks metadata to see if this has elev.
        """
        if coord in self.metadata:
            return self.metadata[coord] == 'elev'
    
    def has_bounds(self):
        """ 
        Checks metadata to see if this variable has a bounds attribute.
        """
        return 'bounds' in self.metadata

    def has_time_bounds(self):
        """
        Checks metadata to see if this variable time bounds.
        """
        if coord in self.metadata:
            return self.metadata[coord] == 'time_bounds'

    def has_plev_bounds(self):
        """
        Returns True if metadata indicates variable has plev bounds.
        """
        if coord in self.metadata:
            return self.metadata[coord] == 'plev_bounds'

    def has_elev_bounds(self):
        """Returns True if metadata indicates variable has plev bounds.
        """
        if coord in self.metadata:
            return self.metadata[coord] == 'elev_bounds'

    def get_coordinate(self):
        """Returns the value of the coordinate data if it has 
        one"""
        return db.get_property(self.name, 'coord_val')

    def add_process(self, process):
        """ 
        Adds a Process object to the Processes list.
        """
        if process.__class__ is not Process:
            print process, "is not a Process object"
            raise TypeError
        self.processes.append(process)
        return self

    def add_data(self, data):
        """
        Given a numpy array with the correct dimensions,
        sets it to objects 'data' instance variable.
        """
        if type(data) is not type(np.array([])):
            print type(data), "is not a numpy array"
            raise ValueError
        if len(self.dimensions) == 0:
            try:
                set_dimensions()
            except:
                pass
        if len(data.shape) != len(self.dimensions):
            print "number of dimensions of data is not " \
                    "equal to number of object dimensions"
            raise ValueError

        self.data = data
        return self

    def get_data_type(self):
        """Check if data_type is defined in the properties
        database for this varibale name. Return value if available,
        otherwise throw ValueError.
        """
        return db.get_property(self.name, 'data_type')

    def get_dimensions(self):
        """Check if dimensions is defined in the properties
        database for this varibale name. Return value if available,
        otherwise throw ValueError.
        """
        var = cfg.read_variables()[self.name]
        dimensions = var['dimensions']
        return dimensions

    def change_data_type(self, data_type=None):
        """
        Attempts to force the datatype to change for this data
        """
        if data_type:
            self.data.astype(data_type)
        else:
            self.data.astype(self.get_data_type())

    def set_dimensions(self,dimensions=None):
        """
        Given a tuple of String dimensions, sets object to the 
        dimensions.
        """
        if not dimensions:
            dimensions = self.get_dimensions()
            dimensions = tuple(dimensions)
        if type(dimensions) is not tuple:
            print type(dimensions), "is not of type tuple"
            raise TypeError
        if len(self.dimensions) > 0:
            print "Warning: overwriting dimensions"
        self.dimensions = dimensions
        return self

    def add_db_metadata(self):
        """
        Reads the metadata database and copies the metadata to 
        this object.
        """
        meta_dict = {}
        try :
            meta_dict = db.get_all_metadata(self.name)
        except ValueError :
            print "ERROR:", self.name, "not defined in metadata db"
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
        return self

    def add_plev_attributes(self, plev_var):
        setattr(plev_var, 'long name', 'pressure')
        setattr(plev_var, 'units', 'hPa')
        setattr(plev_var, 'standard name','air_pressure')
        setattr(plev_var, 'positive', 'down')
        setattr(plev_var, 'axis', 'Z')

    def get_plev_name(self, nc_handle):
        coord_data = self.get_coordinate()
        num = 0
        all_vars = nc_handle.variables
        pdb.set_trace()
        # Find all plev variables already written
        for v in all_vars.keys():
            if re.match(r'^plev\d+$',  v, re.I):
                # Check if same plev
                if coord_data == all_vars[v][0]:
                    already_exists = True
                    return (already_exists, v)
                num += 1

        name = 'plev' + str(num)
        already_exists = False
        return (already_exists, name)

    def create_dimensions(self, nc_handle):
        """Check if self.dimensions are defined. if not
        create them
        """
        dims = nc_handle.dimensions
        for d in self.dimensions:
            if d not in dims:
                self.create_dimension(nc_handle, d)

    def write_plev(self, nc_handle):
        """
        Writes the pressure level variable. 
        Changes the name to plev[n] where n a number
        when there are multiple plev variables.
        """
        if not self.has_plev():
            return False
        exists,name = self.get_plev_name(nc_handle)
        self.metadata[coord] = name
        if not exists:
            if 'plev' not in nc_handle.dimensions:
                nc_handle.createDimension('plev', 1)
            plev_var = nc_handle.createVariable(name, int, ('plev'))
            self.add_plev_attributes(plev_var)
        return True

    def reshape(self, coord_name):
        """
        Reshapes the data when adding the plev dimension
        """
        self.dimensions.append(coord_name)
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
        print "writing", self.name
        
        # Writes the plev variable if it exists
        success = self.write_plev(nc_handle)
        if success: # modify the shape of the data to accommodate plev.
            self.reshape('plev')
        
        # Check that the dimensions are correct for the shape of the data
        if len(self.data.shape) != len(self.dimensions):
            print "dimensions of data not equal to dimensions attribute"
            return

        # Check if dimensions are defined. If they aren't, create them
        self.create_dimensions(nc_handle)
        
        
        # If the oject has a plev bounds, create the plev bound netCDF variable
        if self.has_plev_bounds():
            pass

        # Create and write the variable
        nc_var = nc_handle.createVariable( \
                self.name, \
                self.data.dtype, \
                tuple(self.dimensions), \
                zlib=True, \
                complevel=7, \
                shuffle=True, \
                fill_value=FILL_VALUE)

        # Add the metadata
        for name,value in self.metadata.iteritems():
            if name != 'name':
                setattr(nc_var, name, value)

        # Write the processes attribute string
        process_str = self.get_process_str()
        setattr(nc_var, "OM_Procedure", process_str)

        nc_var[:] = self.data

        # Tell the Process objects and Time Objects
        # to write to the file
        for t in self.time:
            t.write_to_nc(nc_handle)

        for p in self.processes:
            p.write_to_nc(nc_handle)

        return nc_handle


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

    def __str__(self):
        obj_str  = "\n***** " + self.name + " ******\n*\n"
        obj_str += "* dtype               : " + str(self.data.dtype) + "\n"
        obj_str += "* processes           : " + self.get_process_str() + "\n"
        obj_str += "* dimensions          : " + str(self.dimensions) + "\n"
        obj_str += "Metadata:\n"
        for k,v in self.metadata.iteritems():
            num_chars = len(k)
            obj_str += "* " + k
            obj_str += " "*(20-num_chars)
            obj_str += ": " +v+"\n"
            
        obj_str += "Data: \n"
        obj_str += str(self.data)
        
        return obj_str

    __repr__ = __str__



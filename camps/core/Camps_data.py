import sys
import os
import numpy as np
import pdb
import re
import logging
from netCDF4 import Dataset

from nc_writable import nc_writable
from Process import Process
from . import Time
from ..registry import util as cfg
from ..registry.db import db as db
from ..registry import constants as const


"""Module containing Camps_data class.
"""

FILL_VALUE = 9999
coord_str = 'coordinates'


class Camps_data(nc_writable):
    """
    CAMPS data object for storing metadata and accompanied objects describing the variable.

    This class will attempt to
    gather information from the metadata database on a given property, but
    any gaps will need to be provided by the user. 

    Attributes:
        name (str): `quick fill` name that can be used to initialize variable from template.
        data (:obj:`np.array`): n-dimensional numpy array holding variable data.
        dimensions (:obj:`list` of str): The names of the dimensions--ordered by dimension.
        processes (:obj:`list` of :obj:`Process`): Process that modify this variable.
        metadata (dict): Metadata with key-value pairs.
        time (:obj:`list` of :obj:`Time`): Time objects describing this variable
        properties (dict): Metadata that will not be written to NetCDF file 
                that may be used internally.
        location (:obj:`Location`) Location object which describes the first
                dimensions.

    Args:
        name (str): `quick-fill` name that can be used to initialize variable from template.
        autofill (bool): If there should be an attempt to autofill metadata based on `name`.

    Note:
        Time objects must have a dimensionality that's compatible with ``data``.
    """

    def __init__(self, name, autofill=True):
        """
        Initializes object properties and adds metadata from the database
        coresponding to the name if available.
        """
        self.name = name
        self.data = np.array([])
        self.dimensions = []  # The name of the dimensions
        self.processes = []
        self.metadata = {}
        self.time = []
        self.properties = {}
        #self.components = [] #This feature on hold for now
        self.location = None
        if autofill:
            self.add_db_metadata()

    # Coordinates
    def add_coord(self,level1, level2=None, vert_type=None):
        """Adds coordinate information.
        """
        if vert_type is not None:
            self.metadata[const.COORD] = vert_type #sets coordinates metadata key
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
        if 'bounds' in self.metadata:
            return True
        if 'coordinates' in self.metadata:
            return 'bounds' in self.metadata['coordinates']

    def has_time_bounds(self):
        """
        Checks metadata to see if this variable time bounds.
        """
        #pdb.set_trace()
        return 'hours' in self.properties or db.get_property(self.name, 'hours') is not None

    def is_feature_of_interest(self):
        """
        Checks metadata to see if this variable is a feature of interest.
        """
        return 'feature_of_interest' in self.properties or db.get_property(self.name, 'feature_of_interest') is not None

   
    def has_plev_bounds(self):
        """
        Returns True if metadata indicates variable has plev bounds.
        """
        if self.has_bounds():
            if 'bounds' in self.metadata:
                return self.metadata['bounds'] == 'plev_bounds'
            if 'coordinates' in self.metadata:
                return 'plev_bounds' in self.metadata['coordinates']
               
    def has_elev_bounds(self):
        """Returns True if metadata indicates variable has plev bounds.
        """
        if self.has_bounds():
            if 'bounds' in self.metadata:
                return self.metadata['bounds'] == 'elev_bounds'
            if 'coordinates' in self.metadata:
                return 'elev_bounds' in self.metadata['coordinates']
               
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
        """Returns phenomenonTimePeriod if exists.
        """
        if not self.has_time_bounds():
            return None
        for i in self.time:
            if 'OM__phenomenonTimePeriod' in i.name:
                return i
    
    def get_lead_time(self):
        """Returns leadTime if it exists."""
        lead_type = Time.LeadTime
        return self.get_time(lead_type)

    def get_result_time(self):
        """Returns resultTime if it exists."""
        result_type = Time.ResultTime
        return self.get_time(result_type)

    def get_forecast_reference_time(self):
        """Returns ForecastReferenceTime if it exists."""
        result_type = Time.ForecastReferenceTime
        return self.get_time(result_type)

    def get_valid_time(self):
        """Returns ForecastReferenceTime if it exists."""
        result_type = Time.ValidTime
        return self.get_time(result_type)

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
            logging.warning("More than one " + str(time_type) +
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

#    def add_component(self, c_obj):
#        """
#        Adds a component object c_obj to the component list.
#        The object c_obj is a component of self.
#        """
#        if not isinstance(c_obj, Camps_data):
#            return None
#
##        sizes = list(c_obj.data.shape)
##        dict_sizes = dict(zip(c_obj.dimensions, sizes))
##        for key,value in dict_sizes.iteritems():
##            c_obj.metadata.update({key : value})
##        c_obj.metadata.update({'sizes' : sizes})
#
##        c_obj.data = None
#
#        self.components.append(c_obj)

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
        database for this variable name and returns it. 
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

    def change_property(self, property_basename):
        """Change the OM__observedProperty. Add full URI if
        possible.
        """
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
        """Returns the parsed OM__observedProperty metadata
        element.
        """
        op = self.metadata['OM__observedProperty']
        if op[-1] == '/':
            op = op[0:-1]
        return os.path.basename(op)

    def change_data_type(self, data_type=None):
        """
        Attempts to force self.data's dtype to change to the argument.
        The templated value for dtype (found in netcdf.yaml) is used if 
        data_type is not given.
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
            logging.error(type(dimensions)+"is not of type tuple")
            raise TypeError
        if len(self.dimensions) > 0:
            logging.debug("overwriting dimensions")
        self.dimensions = list(dimensions)
        return self

    def add_dimensions(self, *dims):
        """Add dimensions to self."""
        for dim in dims:
            if dim not in self.dimensions:
                self.dimensions.append(dim)

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
        Given a key and value, adds it to the metadata.
        """
        self.metadata[key] = value
        return self

    def add_source(self, value):
        """
        Sets the PROV__Used attribute to 'value'.
        """
        self.metadata['PROV__Used'] = value

    def add_fcstTime(self, value):
        """
        Sets the PROV__Used attribute to 'value'.
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

    def add_plev_bounds_attributes(self, plev_var):
        """
        Adds Common Plev layer bounds attributes.
        """
        setattr(plev_var, 'long_name', 'pressure layer bounds')
        setattr(plev_var, 'units', 'hPa')
        setattr(plev_var, 'standard_name', 'air_pressure')
        setattr(plev_var, 'positive', 'down')
        setattr(plev_var, 'axis', 'Z')

    def add_elev_bounds_attributes(self, elev_var):
        """
        Adds Common elev layer bounds attributes.
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

        if self.is_feature_of_interest():
            return self.name
        # Do not write dataSource
        name = ""
        
        # Write observedProperty
        try:
            name += self.get_observedProperty()
        except:
            pass

        # Write duration
        #pdb.set_trace()
        if self.has_time_bounds():
            bounds = self.get_time_bounds() #get bounds object
            cell_method = self.get_cell_methods() #get cell method
            method = str(cell_method.values()[0]) #grab value from dictionary 
            name += '_'+method+'_'+str(bounds.get_duration())+'hr' #will add the duration and type (ex: avg, max, min) to name
        else:
            name += '_instant'

        # Write verticalCoordinate
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

        # Write fcstReferenceTime (model cycle hour)
        try:
            name += '_'+str(self.metadata['FcstTime_hour']).zfill(2)+'Z'
            #name += '_'+str(self.metadata['FcstTime_hour'])
        except:
            pass

        # Write leadtime if exists
        try:
            leadtime = self.metadata['leadtime']
            name += '_%shr'%(str(leadtime))
        except:
            pass

        # Write smoothing, if metadata indicates smoothing was performed
        try:
            smooth = self.metadata['smooth']
            name += '_%spt_smooth'%(str(smooth))
        except:
            pass

        # For MOS forecast output, add either "MOS" or "CmpChk" to variable name
        if 'TmpDewCmpChk' in self.get_process_str():
            name = 'CmpChk_'+name
        elif 'MOS_Method' in self.get_process_str():
            name = 'MOS_'+name

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

    def _write_coordinate(self, nc_handle):
        """
        Determines which coordinate needs to be written to
        it's own variable and calls the associated function.
        A bounds function will always supercede the non-bounds function.
        """
        success = False
        if self.has_plev_bounds():
            success = self._write_plev_bounds(nc_handle)
        elif self.has_elev_bounds():
            success = self._write_elev_bounds(nc_handle)
        elif self.has_plev():
            success = self._write_plev(nc_handle)
        elif self.has_elev():
            success = self._write_elev(nc_handle)

        if self.has_time_bounds():
            success = self._write_time_bounds(nc_handle)
            self.add_bounds_process()

        if 'coordinates' in self.metadata:
            coord_str = self.metadata['coordinates']
            coords_to_add = [coord_str]
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
        """Adds a process representing the cell_method
        """
        cell_type = self.metadata['cell_methods'].split(':')[1].strip(' ')
        if cell_type == 'minimum':
            # If process has already been added to the list then we skip it
            # Otherwise add it to the process list
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
        """
        Writes the elev_bounds variable.
        """
        elev = 'elev'
        nv = 'nv'
        # Turn the data into a numpy array and
        # Reshape so that it has a shape of 1,2 for elev,nv
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
            # Probably need this defined:
            # self.add_elev_bounds_attributes(elev_var)
            elev_var[:] = coord_data
        return True

    def _write_time_bounds(self, nc_handle):
        """
        Writes the Time bounds variable

        """
        # NOTE: this function doesn't really do what it says it does anymore
        # now that we have changed how we write bounded time variables all 
        # this does is add hours to self.properties if it isn't already there
        # rename this function??
        try:
            hours = self.properties['hours']
        except:
            hours = db.get_property(self.name, 'hours')
            self.properties['hours'] = hours
        hours = int(hours)
        
        t = self.get_phenom_time()


    def _write_plev_bounds(self, nc_handle):
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
        """
        Writes the pressure level variable.
        Changes the name to plev[n] where n a number
        when there are multiple plev variables.
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
        """
        Writes the pressure level variable.
        Changes the name to plev[n] where n a number
        when there are multiple plev variables.
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

    def reshape(self, nc_handle):
        """
        Reshapes the data when adding the a coordinate dimension.
        """
        # 
        if 'level' in self.dimensions:
             return

        try:
            coord_name = self.metadata[coord_str]
        except KeyError:
            logging.warning("no " + coord_str + "metadata")
            return

        if 'plev' not in coord_name and 'elev' not in coord_name:
#        if 'plev' in coord_name or 'elev' in coord_name:
            return

        vertical_coordinate_name = "level"

        self.dimensions = list(self.dimensions)
        self.dimensions.append(vertical_coordinate_name)


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
        #dim_length = 0
        #if self.data is not None:
        #    dim_length = self.data.shape[index]
        #elif self.metadata[dimension_name]:
        #    dim_length = self.metadata[dimension_name]
        nc_handle.createDimension(dimension_name, dim_length)

    def write_to_nc(self, nc_handle):
        """
        Adds a netCDF variable to the nc_handle.
        Includes the data and metadata associated with the object.
        """
        logging.info("Writing " + self.name)
   
        # This will include all netcdf variables that in some way help
        # describe this variable.
        ancillary_variables = ""

        # Writes the elev, plev, and bounds variables if they exist
        success = self._write_coordinate(nc_handle)
        # Modify the shape of the data to accommodate coordinate, unless it's a metadata variable
        if success and self.data is not None:  
            self.reshape(self.metadata[coord_str])

        # Tell the Time objects, Process objects, and Component objects
        # to write to the file
        for t in self.time:
            time_name = t.write_to_nc(nc_handle)
            ancillary_variables += time_name + " "

        for p in self.processes:
            p.write_to_nc(nc_handle)
            ancillary_variables += p.name + " "
        
        #feature on hold temporarily 
#        for c in self.components:
#            comp_name = c.write_to_nc(nc_handle)
#            ancillary_variables += comp_name + " "
#
#        self.metadata['ancillary_variables'] = ancillary_variables

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

        if self.data is None:
            dtype = int
        else:
            dtype = self.data.dtype

        # Create the variaible
        nc_var = nc_handle.createVariable(
            variable_name,
            dtype,
            tuple(self.dimensions),
            chunksizes=chunksize,
            zlib=True,
            complevel=4,
            shuffle=False,
            fill_value=fill_value)

        # Add the metadata
        self._add_nc_metadata(nc_var)

        # Write the processes attribute string if it's not a FOI
        if not self.is_feature_of_interest():
            process_str = self.get_process_str()
            setattr(nc_var, "SOSA__usedProcedure", process_str)
        
        # Add self.data to the nc_var
        self.add_nc_data(nc_var)

        return variable_name

    def add_to_database(self, filename, file_id=None):
        """Add variable to the database for searching.
        """
        var_name = self.get_variable_name()
        # There should always be a phenomenonTime unless it's a feature of interest
        if self.is_feature_of_interest():
            return
        try:
            ptime = self.get_phenom_time()
        except IndexError:
            raise AttributeError("No PhenomenonTime")

        # Try to use forecast reference time as the start if it exists
        ftime = self.get_forecast_reference_time()
        if ftime is not None:
            start = ftime.get_start_time()
        else:
            start=ptime.get_start_time()

        # Returns date in datetime format, so convert to epoch
        start=Time.epoch_time(start)
        end=ptime.get_end_time()
        end=Time.epoch_time(end)
        try:
            btime = filter(lambda t: t.name=='OM__phenomenonTimePeriod', self.time)[0]
            duration = btime.get_duration()
            time_dim = cfg.read_dimensions()['time']
            duration_method = self.get_cell_methods()[time_dim]
        except IndexError:
            duration = 0  # So we can differentiate between instant and period variables in the database search
            duration_method = None

        vertical = self.get_coordinate()
        # If it has an upper and lower bounds, then there should be
        #       a 'cell_methods' component describing the the relationship
        #       between the two methods, e.g. diff, avg, etc.
        if type(vertical) is tuple: # then is bounds
            vert_coord1, vert_coord2 = vertical
            vert_method = None
            try:
                elev_dim = cfg.read_dimensions()['elev']
                vert_method = self.get_cell_methods()[elev_dim]
                vert_units = 'm'
            except:
                pass
            try:
                plev_dim = cfg.read_dimensions()['plev']
                vert_method = self.get_cell_methods()[plev_dim]
                vert_units = 'mb'
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
        reserved1 = None
        if self.is_vector():
            reserved1 = "vector"
        else:
            reserved1 = "grid"
        
        reserved2 = None
        if 'reserved2' in self.properties:
            reserved2 = (self.properties['reserved2'])
        # Add smooth information to database if present in metadata 
        if 'smooth' in self.metadata:
            smooth = int(self.metadata['smooth'])
        else:
            smooth = None

        db.insert_variable(property=self.get_observedProperty(),
                           source=self.get_source(),
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
        """Return an appropriate chunk size tuple given internal data.
        """
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
        """Check that the dimensions are correct for the shape of the data.
        """
        if self.data is not None and self.data.size > 0 \
                and len(self.data.shape) != len(self.dimensions):
            logging.error(
                "dimensions of data not equal to dimensions attribute")
            logging.error('len of shape is: ' + str(len(self.data.shape)))
            logging.error('len of dims  is: ' + str(len(self.dimensions)))
            logging.error("Will not write " + self.name)
            raise ValueError

    def add_nc_data(self, nc_var):
        """
        Time intensive. See netCDF4.Variable.__setitem__
        """
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
        if self.data is None:
            return
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

    def _add_nc_metadata(self, nc_var):
        """Adds internal metadata to netCDF file handle.
        """
        for name, value in self.metadata.iteritems(): 
            if name != 'name' and name != 'fill_value': # skip name and fill_value
                if type(value) is unicode:  # To prevent 'string' prefix
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
        """Return the source metadata attribute.
        """
        if 'PROV__Used' in self.metadata:
            return os.path.basename(self.metadata['PROV__Used'])
        else:
            # Look for PROV__Used in processes
            for proc in self.processes:
                if 'PROV__Used' in proc.attributes:
                    return os.path.basename(proc.attributes['PROV__Used'])
        return None

    def is_observation(self):
        """Returns True if the Source is from a model.
        Currently, 'GFS' and 'NAM'
        """
        obs = ['METAR', 'MARINE']
        return self.get_source() in obs

    def is_model(self):
        """Returns True if the Source is from a model.
        Currently, 'GFS' and 'NAM'
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
        """
        Returns a string representation of the process.
        i.e. A comma separated name of the process enclosed in parens.
        """
        process_str = "( "
        for proc in self.processes:
            process_str += proc.name + " "
        process_str = process_str[0:-1] + " )"
        return process_str

    def add(self, other, axis=1):
        """Add the data of other Camps_data object to self.
        """
        # Correct shape
        while len(other.data.shape) <= axis:
            other.data = np.array([other.data])
        while len(self.data.shape) <= axis:
            self.data = np.array([self.data])
        if len(other.data.shape) != len(self.data.shape):
            raise ValueError("all input arrays must have the same shape")
        new_data = np.concatenate((self.data, other.data),axis-1)
        return new_data

    def __add__(self, other):
        """
        """

        if type(other) != type(self):
            raise TypeError("Types do not match")
        if self.name != other.name:
            raise Exception("Attempt to combine different variables failed")

        # Add data
        if self.data is not None and other.data is not None:
            new_data = self.add(other)
            self.data = new_data

        # Add times
        self.add_times(other)

        # Add metadata
        for i in self.metadata:
            for j in other.metadata:
                pass
        return self

    def add_times(self, other):
        for i in self.time:
            for j in other.time:
                if type(i) == type(j):
                    i = i + j
#        for k in range(len(self.components)):
#            self.components[k].add_times(other.components[k])

    def __getattr__(self, name):
        """Returns metadata using '.' operator"""
        if name in self.metadata:
            return self.metadata[name]
        else:
            raise AttributeError

    # TODO
    #def __eq__(self, other):

    def __str__(self):
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
        for k, v in self.metadata.iteritems():
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

    __repr__ = __str__

import os
import sys
from netCDF4 import Dataset
from nc_writable import nc_writable
file_dir = os.path.dirname(os.path.realpath(__file__))
relative_path = "/.."
path = os.path.abspath(file_dir + relative_path)
sys.path.insert(0, path)
import registry.util as cfg
import pdb


class Process(nc_writable):
    """Class that holds process chain information for WISPS data

    Attributes:
        name (str): Name of the variable.
        process_step (str): URL to description of the process.
        attributes (dict): Additional attributes to add to the variable.
        
    """

    def __init__(self, name, process_step=None, **attributes):
        """Initializes the Process.
        Requires process_step, which would be the URI for the Process.
        """
        self.name = name
        self.process_step = process_step
        # Check the config file for the process metadata if process step not provided
        if process_step is None:
            cfg_def = cfg.read_procedures()[name]
            self.process_step = cfg_def['process_step']
            attributes = cfg_def.copy()
        

        #self.source = source
        self.attributes = attributes
        #self.attributes['standard_name'] = 'source'

    def write_to_nc(self, nc_handle):
        """Writes the netCDF variable representation of the Process
        to the nc_handle.

        Args:
            nc_handle (:obj:`Dataset`): NetCDF file handle.

        Returns:
            None
        """
        if self.name in nc_handle.variables:
            return
        process_var = nc_handle.createVariable(self.name, int)
        setattr(process_var, "LE_ProcessStep", self.process_step)
        #setattr(process_var, "Source", self.source)

        self.attributes.pop('process_step')

        # Adds the remainder of the attributes to the variable.
        for name, value in self.attributes.iteritems():
            if name == 'source':
                name = 'LE_Source'
            setattr(process_var, name, value)

    def add_attribute(self, key, value):
        """Add a new attribute, or change an exsisting attribute.
        Args:
            key (str): Metadata key
            value (str): Metadata value
        
        Returns: 
            None
        """
        if key == "process_step":
            self.process_step = value
        elif key == "source":
            self.source = value
        else:
            self.attributes[key] = value

    def get_attribute(self, key):
        """Returns value of attribute key.

        Args:
            key (str): Metadata key.
        
        Returns: 
            Value of attribute given key.
        
        """
        return self.attributes[key]

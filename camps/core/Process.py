import os
import sys
from netCDF4 import Dataset
from nc_writable import nc_writable
import pdb
from ..registry import util as cfg

class Process(nc_writable):
    """Class holding process chain information for CAMPS data

    Attributes:
        name (str): Name of the variable.
        process_step (str): URL to description of the process.
        attributes (dict): Additional attributes to add to the variable.
    """


    def __init__(self, name, process_step=None, **attributes):
        """Initializes the Process object. It requires process_step,
        an URI for the Process.
        """

        self.name = name

        self.process_step = process_step
        # Check the configuratin file for the process metadata if process step not provided
        if process_step is None:
            cfg_def = cfg.read_procedures()[name]
            self.process_step = cfg_def['process_step']
            attributes = cfg_def.copy()
        self.attributes = attributes


    def write_to_nc(self, nc_handle):
        """Writes the netCDF variable representation of the Process
        to the nc_handle.

        Args:
            nc_handle (:obj:`Dataset`): NetCDF file handle.

        Returns:
            None
        """

        #Return if process already written in Dataset.
        if self.name in nc_handle.variables:
            return

        #Create Dataset process variable
        process_var = nc_handle.createVariable(self.name, int)
        setattr(process_var, "PROV__Activity", self.process_step)

        self.attributes.pop('process_step')

        #Add the remainder of the attributes to the Dataset variable.
        for name, value in self.attributes.iteritems():
            if name == 'source':
                name = 'PROV__Used'
            setattr(process_var, name, value)


    def add_attribute(self, key, value):
        """Add a new attribute, or change an existing attribute.

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

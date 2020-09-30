import os
import sys
import re
from netCDF4 import Dataset
from .nc_writable import nc_writable
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
            pname : process name
        """

        #Return if process already written in Dataset.
        pname, exists = self.get_name(nc_handle)
        if not exists:
            process_var = nc_handle.createVariable(pname, int)
            setattr(process_var, "PROV__Activity", self.process_step)
            #Add the remainder of the attributes to the Dataset variable.
            for name, value in self.attributes.items():
                if name != 'process_step' and name != 'feature_of_interest':
                    if name == 'source':
                        name = 'PROV__Used'
                    setattr(process_var, name, value)

        return pname


    def get_name(self, nc_handle):
        """Returns a tuple containing the
        [0] - name of the netCDF Dataset process variable and
        [1] - a boolean indicating if it already exists as a netCDF Dataset variable.
        Beforehand, if there is no match of
        1) the process variable name or
        2) its attributes and values, 
        then it adjusts the digital suffix of the name
        for the netCDF Dataset process variable.
        """

        all_vars = nc_handle.variables
        varkeys = list(all_vars.keys())

        #Matching pattern consists of Time variable name plus a digital suffix.
        #Case of letters are immaterial.
        def match(var): return re.match(r'^' + self.name + '\d*$', var, re.I)
        proc_vars = list(filter(match, varkeys)) #gleans the matching names from netCDF Dataset
        for name in reversed(proc_vars):
            var = all_vars[name]
            #Return name and True with first match in data array.
            equal = True
            for attr in var.ncattrs():
                try:
                    a = self.get_attribute(attr)
                    if a != var.getncattr(attr):
                        equal = False
                        break
                except:
                    if attr == 'PROV__Activity':
                        try:
                            a = self.get_attribute('process_step')
                            if a != var.getncattr(attr):
                                equal = False
                                break
                        except:
                            equal = False
                            break
                        continue
                    elif attr == 'PROV__Used':
                        try:
                            a = self.get_attribute('source')
                            if a != var.getncattr(attr):
                                equal = False
                                break
                        except:
                            equal = False
                            break
                        continue
                    equal = False
                    break
            if equal:
                return (name, True)

        #No match.  Make name.
        if len(proc_vars) == 0:
            name = self.name
        else:
            name = self.name + str(len(proc_vars))
        return (name, False)


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
        #elif key == "source":
        #    self.source = value
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

from netCDF4 import Dataset
from nc_writable import nc_writable

class Process(nc_writable):
    """ Class that holds process chain information for WISPS data
    """

    def __init__(self, name, process_step, source="", **kwargs):
        """Initializes the Process. 
        Requires process_step, which would be the URI for the Process.
        """
        self.name = name
        self.process_step = process_step
        self.source = source
        self.attributes = kwargs
            
    def write_to_nc(self, nc_handle):
        """Writes the netCDF variable representation of the Process 
        to the nc_handle.
        """
        process_var = nc_handle.createVariable(self.name, int)
        setattr(process_var, "Process_step", self.process_step)
        setattr(process_var, "Source", self.source)

        # Adds the remainder of the attributes to the variable.
        for name,value in self.attributes.iteritems():
            setattr(nc_handle, name, value) 

    def add_attribute(self, key, value):
        """Add a new attribute, or change an exsisting attribute.
        """
        if key == "process_step":
            self.process_step = value
        elif key == "source":
            self.source = value
        else:
            self.attributes[key] = value

    def get_attribute(self, key):
        """Returns value of attribute key"""
        return self.attributes[key]


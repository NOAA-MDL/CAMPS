#!/usr/bin/env python
import sys
from netCDF4 import Dataset
import json


def getVariables(nc):
    p_vars = nc.primary_variables
    p_vars = p_vars.split(" ")
    all_vars = {}
    all_vars['primary'] = p_vars
    all_vars['all'] = get_var_metadata(nc)
    return all_vars

def get_var_metadata(nc):
    out_dict = {}
    variables = nc.variables
    for name, var_obj in variables.iteritems():
        metadata = var_obj.ncattrs()
        var_dict = {}
        var_dict['name'] = name;
        for key in metadata:
            value = var_obj.getncattr(key)
            var_dict[key] = str(value)

        out_dict[name] = var_dict
    return out_dict

if __name__ == '__main__':
    filename = sys.argv[1]
    nc = Dataset(filename, 'r')
    myout = getVariables(nc)
    output = json.dumps(myout)
    print output


    #return [output]


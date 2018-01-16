#!/usr/bin/env python
from netCDF4 import Dataset
import json


def application(environ, start_response):
    status = '200 OK'
    output = b'Hello World'
    #output = str(environ)
    qs = environ['QUERY_STRING']
    output = qs
    nc = Dataset('/var/www/myapp/test3.nc', 'r')
    myout = getVariables(nc)
    output = json.dumps(myout)


    #response_headers = [('Content-type', 'text/plain'),
    response_headers = [('Content-type', 'application/json'),
                        ('Content-Length', str(len(output)))]
    start_response(status, response_headers)

    return [output]


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


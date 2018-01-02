#!/usr/bin/env python
import sys
import os
import logging
file_dir = os.path.dirname(os.path.realpath(__file__))
relative_path = "/.."
path = os.path.abspath(file_dir + relative_path)
sys.path.insert(0, path)
import registry.util as cfg
from netCDF4 import Dataset
import mospred.read_pred as read_pred
import mospred.util as util
import data_mgmt.Time as Time
from datetime import timedelta
import mospred.create as create
from mospred.create import Predictor
import mospred.procedures as procedures
import mospred.interp
import copy
import pdb
from data_mgmt.fetch import *

global control

def main(control_file=None):
    """
    Driver for mospred.
    Will take a
    list of predictors, calculate those that are unavailable,
    apply procedures, and interpolate to stations. 
    """
    if control_file:
        control = cfg.read_mospred_control(control_file)
        print "Reading Control File", control_file
    else:
        control = cfg.read_mospred_control()
        print "Reading Default Control File"
    
    # Pull variables from the config
    date_range_list = control['range'] # Array of date ranges and strides
    fcst_ref_time = control['forecast_reference_time']
    debug_level = control['debug_level']
    input_dirs = control['input_directory']
    output_dir = control['output_directory']
    num_procs = control['num_processors']
    predictor_file = control['predictor_file']
    station_defs_file = control['station_defs']
    selected_stations_file = control['selected_stations']
    log_file = control['log_file']
    if log_file:
        out_log = open(log_file, 'w+')
        sys.stdout = out_log
        sys.stderr = out_log
    try:
        logging.getLogger('').handlers = []
        level = logging.getLevelName(debug_level)
        logging.basicConfig(level=level)
    except:
        print "Logging setup failed"
        raise


    # Read valid station definitions.
    # Is a dictionary where all available station's call name is the key, 
    # and has a dictionary value containing the lat, lon, long_name, and code
    station_defs = util.read_station_definitions(station_defs_file)
    # Read valid stations
    selected_stations = util.read_valid_stations(selected_stations_file)
    
    # Read the predictors
    pred_list = cfg.read_yaml(predictor_file)
    
    # Preprocess the predictor dictionary into full metadata
    formatted_predictors = []
    for entry_dict in pred_list:
        formatted_pred = preprocess_entries(entry_dict, fcst_ref_time)
        formatted_predictors.append(formatted_pred)

    # Now, there's a list of formatted predictors to fetch.
    # Here, We may want to find metadata matches, so that We can fetch full vars
   
    # An array to hold all the computed variables
    computed_vars = []


    # Loop through date ranges specified in the control file.
    for date_range in date_range_list:

        start,end,stride = read_pred.parse_range(date_range)

        # Loop through the dates
        start = Time.str_to_datetime(start)
        end = Time.str_to_datetime(end)
        stride = timedelta(seconds=int(stride))
        # Add fcst_ref_time
        start += timedelta(hours=int(fcst_ref_time))
        end += timedelta(hours=int(fcst_ref_time))
        # Create a date iterator.
        cur = copy.copy(start)
        while cur < end: # Main loop
            logging.info("Processing " + str(cur))
            for pred in formatted_predictors:
                print pred.search_metadata['property']

                # Try to fetch the exact variable asked for
                #variable = fetch(Time.epoch_time(cur), pred.leadTime,**pred.search_metadata)
                variable = fetch(Time.epoch_time(cur),**pred.search_metadata)


                # If the call to fetch doesn't find the variable
                if variable is None:
                   variable = calculate(Time.epoch_time(cur), pred) 
                
                print "Applying procedures for " + variable.name


                # Apply procedures to the variable
                variable = procedures.apply_procedures(variable, pred.procedures)

                # Add to output array
                computed_vars.append(variable)
            pdb.set_trace()
            nc = Dataset('test.nc', 'w')
            computed_vars[3].write_to_nc(nc)

            cur += stride



    

def calculate(time, predictor):
    """
    Given an internal Predictor object, calculate the variable associated with the observed property
    """
    observed_property = os.path.basename(predictor['property'])
    #if 'WSpd' in observed_property:
        #pdb.set_trace()
    if not create.is_valid_property(observed_property):
        err_str = "There is no function associated with the calculation of " 
        err_str += observed_property
        err_str += "\nCheck create.py for function definitions"
        raise RuntimeError(err_str)
    if has_multiple_vertical_layers(predictor):
        ret_obj = calc_with_multiple_vertical_layers(time, predictor)
    else:
        variable_calculation_function = create.get_met_function(observed_property)
        ret_obj = variable_calculation_function(time, predictor) # Pass standard information
    
    
    return ret_obj
    
def calc_with_multiple_vertical_layers(time, predictor):
    """
    """
    # Get the vertical method, e.g. diff, avg, etc.
    vert_method = predictor.search_metadata.pop('vert_method')
    # First, create individual predictors for each layer
    lower_layer_pred = predictor.copy()
    upper_layer_pred = predictor.copy()
    # Change to only have 1 vert_coord
    upper_layer_pred.search_metadata['vert_coord1'] = predictor.search_metadata['vert_coord2'] 
    # Remove second bound
    lower_layer_pred.search_metadata.pop('vert_coord2')
    upper_layer_pred.search_metadata.pop('vert_coord2')
    # Remove method since there's now only 1 vertical layer

    # Check if the (single layer) variables already exist
    variable_layer1 = fetch(time, **lower_layer_pred.search_metadata)
    variable_layer2 = fetch(time, **upper_layer_pred.search_metadata)

    if variable_layer1 is None or variable_layer2 is None:
        observed_property = os.path.basename(predictor['property'])
        variable_calculation_function = create.get_met_function(observed_property)
        variable_layer1 = variable_calculation_function(time, lower_layer_pred)
        variable_layer2 = variable_calculation_function(time, upper_layer_pred)
        assert variable_layer1 is not None
        assert variable_layer2 is not None

    vert_calc_function = create.get_common_function(vert_method)
    new_data = vert_calc_function(variable_layer1.data, variable_layer2.data)
    
    # Create Wisps_data with new data
    variable_layer1.properties['vert_coord1'] = predictor.search_metadata['vert_coord1']
    variable_layer1.properties['vert_coord2'] = predictor.search_metadata['vert_coord2']
    variable_layer1.metadata['coordinates'] = 'plev'
    variable_layer1.data = new_data
    
    return variable_layer1



def has_multiple_vertical_layers(predictor):
    """
    """
    if 'vert_coord2' in predictor.search_metadata:
        return True
    return False
    
def preprocess_entries(entry_dict, fcst_ref_time):
    """Preprocess a dictionary into a convenience Predictor object.
    Return said object.
    """
    variable_metadata = read_pred.get_variable(entry_dict)
    tmp_pred = Predictor(variable_metadata, fcstRef=fcst_ref_time)
    if 'Procedure' in entry_dict:
        tmp_pred.procedures = entry_dict['Procedure']
    #if 'LeadTime' in entry_dict:
        #tmp_pred.leadTime = entry_dict['LeadTime']
    if 'lead_time' in variable_metadata:
        tmp_pred.leadTime = variable_metadata['lead_time']

    return tmp_pred


class Predictor:
    def __init__(self, searchable_dict, procedures=None, leadTime=None, fcstRef=None):
        """
        """
        self.search_metadata = searchable_dict
        self.procedures = procedures
        self.leadTime = leadTime
        self.fcst_ref_time = fcstRef

    def copy(self):
        """
        """
        return copy.deepcopy(self)

    def change_property(self, observed_property):
        """
        """
        self.search_metadata['property'] = observed_property

    def __getitem__(self, item):
        """
        """
        return self.search_metadata[item]

    def __str__(self):
        """
        """
        fstr = str(self.search_metadata) 
        fstr += '\n'
        fstr += str(self.procedures)
        fstr += '\n'
        fstr += str(self.leadTime)
        fstr += '\n'
        fstr += str(self.fcst_ref_time)
        fstr += '\n'
        return fstr

    __repr__ = __str__

if __name__ == '__main__':
    try:
        main(sys.argv[1])
    except IndexError:
        main()

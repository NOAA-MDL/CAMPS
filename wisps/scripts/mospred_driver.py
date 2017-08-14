#!/usr/bin/env python
import sys
import os
import logging
file_dir = os.path.dirname(os.path.realpath(__file__))
relative_path = "/.."
path = os.path.abspath(file_dir + relative_path)
sys.path.insert(0, path)
import registry.util as cfg
import mospred.read_pred as read_pred
import data_mgmt.Time as Time
from datetime import timedelta
import mospred.create as create
import mospred.interp
import pdb
from data_mgmt.fetch import *


def main(control_file=None):
    """
    Driver for mospred.
    Will take a
    list of predictors, calculate those that are unavailable,
    apply procedures, and interpolate to stations. 
    """
    if control_file:
        control = cfg.read_yaml(control_file)
        print "Reading Control File", control_file
    else:
        control = cfg.read_mospred_control()
        print "Reading Default Control File"
    
    #pdb.set_trace()
    # Pull variables from the config
    date_range_list = control['range'] # Array of date ranges and strides
    fcst_ref_time = control['forecast_reference_time']
    debug_level = control['debug_level']
    input_dirs = control['input_directory']
    output_dir = control['output_directory']
    num_procs = control['num_processors']
    predictor_file = control['predictor_file']
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
    
    # Read the predictors
    pred_list = cfg.read_yaml(predictor_file)
    
    # Preprocess the predictor dictionary into full metadata
    formatted_predictors = []
    for entry_dict in pred_list:
        formatted_pred = preprocess_entries(entry_dict, fcst_ref_time)
        formatted_predictors.append(formatted_pred)

    # Now, there's a list of formatted predictors to fetch.
    # Here, We may want to find metadata matches, so that We can fetch full vars
    
    # Loop through date ranges specified in the control file.
    for date_range in date_range_list:

        start,end,stride = read_pred.parse_range(date_range)

        # Loop through the dates
        start = Time.str_to_datetime(start)
        end = Time.str_to_datetime(end)
        stride = timedelta(seconds=int(stride))
        cur = start.copy()
        while cur < end: # Main loop
            logging.info("Processing " + str(cur))
            for pred in pred_list:
                variable = fetch(Time.epoch_time(cur), pred.leadTime,**pred.search_metadata)

                # If the call to fetch doesn't find the variable
                if variable is None:
                   variable = calculate(pred) 

                # Apply procedures to the variable
                variable = apply_procedures(variable, procedures)
            cur += stride
    

def calculate(predictor):
    """
    Given an internal Predictor object, calculate the variable associated with the observed property
    """
    observed_property = predictor['property']
    variable_calculation_function = create.get_function(observed_property)
    if function is None:
        err_str = "There is no function associated with the calculation of" + observed_property
        err_str += "\nCheck create.py for function definitions"
        raise RuntimeError(err_str)
    ret_obj = variable_calculation_function() # Pass standard information
    return ret_obj
    
    
def preprocess_entries(entry_dict, fcst_ref_time):
    """Preprocess a dictionary into a convenience Predictor object.
    Return said object.
    """
    variable_metadata = read_pred.get_variable(entry_dict)
    tmp_pred = Predictor(variable_metadata, fcstRef=fcst_ref_time)
    if 'Procedure' in entry_dict:
        tmp_pred.procedures = entry_dict['Procedure']
    if 'LeadTime' in entry_dict:
        tmp_pred.leadTime = entry_dict['LeadTime']
    return tmp_pred


class Predictor:
    def __init__(self, searchable_dict, procedures=None, leadTime=None, fcstRef=None):
        self.search_metadata = searchable_dict
        self.procedures = procedures
        self.leadTime = leadTime
        self.fcst_ref_time = fcstRef

if __name__ == '__main__':
    try:
        main(sys.argv[1])
    except IndexError:
        main()

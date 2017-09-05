#!/usr/bin/env python
import sys
import os
import logging
relative_path = os.path.abspath(
    os.path.dirname(os.path.realpath(__file__)) + "/..")
sys.path.insert(0, relative_path)
import registry.util as cfg
import parse_pred
import procedures
from data_mgmt.fetch import fetch
import pdb


def read_predictors(yaml_file):
    w_objs = []
    pred_list = cfg.read_yaml(yaml_file)
    #start,end,stride = parse_range(pred_list['range'])
    for entry_dict in pred_list:
        variable_metadata = get_variable(entry_dict)
        Wisps_obj = fetch(variable_metadata)

        # Apply procedures to obj
        if 'Procedure' in entry_dict:
            apply_procedures(Wisps_obj, entry_dict['Procedure'])
        else:
            w_objs.append(Wisps_obj)

def parse_range(range_str):
    """
    Given a string such as '2013100100-2014033100,24h',
    split into a 'start', 'end', and 'stride'. return dict.
    """
    stride = 24 * 60 * 60
    start, end = range_str.split('-')
    if ',' in end:
        end,stride = end.split(',')
        stride = parse_pred.separate_entries(stride)
        # Stride should not have a cell method
        stride = stride['time']
    return (start, end, stride)

def apply_procedures(w_obj, procedures):
    for p in procedures:
        func, args = procedures.get_procedure(p)
        # Apply the function and given args to w_obj
        # This should modify the w_obj
        func(w_obj, args)


def get_variable(entry_dict):
    """
    Given a user-provided dictionary representing a desired variable, 
    format it into a common form.
    """
    parse_pred.check_valid_keys(entry_dict)
    # The dict that will be populated with available metadata
    exit_dict = {} 
    # Check for OM_observedProperty
    if 'Property' not in entry_dict:
        raise LookupError("Property is not defined and is required")
    property = parse_pred.observedProperty(entry_dict['Property'])
    exit_dict['property'] = property

    # Check Source
    try:
        source = entry_dict['Source']
        is_valid = parse_pred.source(source)
        if not is_valid:
            raise LookupError("Not a valid Source")
        exit_dict['source'] = source
    except KeyError:
        logging.warning("'Source' not defined. Defaulting to METAR")
        source = 'METAR'
        exit_dict['source'] = source

    # Check LeadTime
    if 'LeadTime' in entry_dict:
        leadtime = parse_pred.lead_time(entry_dict['LeadTime'])
        if source == "METAR" or source == "MARINE":
            raise Exception(
                "variable cannot have lead time and be an observation")

    # Check Duration
    if 'Duration' in entry_dict:
        dur_dict = parse_pred.duration(entry_dict['Duration'])
        duration = dur_dict['time']
        duration_cell_method = dur_dict['cell_method']
        exit_dict['duration'] = duration
        exit_dict['duration_method'] = duration_cell_method

    # Check Vertical Coordinate
    if 'Vertical_Coordinate' in entry_dict:
        vert_coord_dict = parse_pred.vertical_coordinate(
            entry_dict['Vertical_Coordinate'])
        try:
            layer1 = vert_coord_dict['layer1']
            exit_dict['vert_coord1'] = layer1
        except:
            pass
        try:
            layer2 = vert_coord_dict['layer2']
            vert_cell_method = vert_coord_dict['cell_method']
            exit_dict['vert_coord2'] = layer2
            exit_dict['vert_method'] = vert_cell_method
        except:
            pass
        
    return exit_dict



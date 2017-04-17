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


def read_predictors(yaml_file):
    w_objs = []
    pred_list = cfg.read_yaml(yaml_file)
    for entry_dict in pred_list:
        variable_metadata = parse_variable(entry_dict)
        Wisps_obj = fetch(variable_metadata)

        # Apply procedures to obj
        if 'Procedure' in entry_dict:
            apply_procedures(Wisps_obj, entry_dict['Procedure'])
        else:
            w_objs.append(Wisps_obj)


def apply_procedures(w_obj, procedures):
    for p in procedures:
        func, args = procedures.get_procedure(p)
        # Apply the function and given args to w_obj
        # This should modify the w_obj
        func(w_obj, args)


def parse_variable(entry_dict):
    # Check for OM_observedProperty
    if 'Property' not in entry_dict:
        raise LookupError("Property is not defined, and is required")
    property = parse_pred.observedProperty(entry_dict['Property'])

    # Check Source
    try:
        source = entry_dict['Source']
        is_valid = parse_pred.source(source)
        if not is_valid:
            raise LookupError("Not a valid Source")
    except KeyError:
        logging.warning("'Source' not defined. Defaulting to METAR")
        source = METAR

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
    else:
        duration=0

    # Check Vertical Coordinate
    if 'Vertical_Coordinate' in entry_dict:
        vert_co_dict = parse_pred.vertical_coordinate(
            entry_dict['Vertical_Coordinate'])

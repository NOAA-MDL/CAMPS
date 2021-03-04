#!/usr/bin/env python
import sys
import os
import logging
import pdb

from ..registry import util as cfg
from . import parse_pred
from . import procedures


"""Module: read_pred.py
This module contains methods used to read the predictors yaml file
and produce a list of camps data objects.

Methods:
    read_predictors
    parse_range
    apply_procedures
    get_variable
"""

def parse_range(range_str):
    """Parses the time range into a start date, end date, and a stride (interval)."""

    #Default stride to 24hrs
    stride = 24 * 60 * 60 # In seconds

    out_dates = range_str.split('-')
    #If there's a start and end date
    if len(out_dates) == 2:
        start,end = out_dates
    elif len(out_dates) == 1:
        start = out_dates[0]
        end = out_dates[0]
    else:
        logging.critical("Too many ranges in date_range string")
        raise ValueError

    #Use given stride.
    if ',' in end: #Implies a given stride.
        end,stride = end.split(',')
        stride = parse_pred.separate_entries(stride)
        # Stride should not have a cell method
        stride = (stride['time']*3600)
    return (start, end, stride)


def apply_procedures(w_obj, procedures):
    """Applies specified procedures to camps data object."""

    for p in procedures:
        func, args = procedures.get_procedure(p)

        func(w_obj, args)


def get_variable(entry_dict):
    """Creates a dictionary whose keys and values are gleaned 
    from the predictor yaml file.  This dictionary facilitates access
    to existing predictor data.
    """

    parse_pred.check_valid_keys(entry_dict)

    #The dict that will be populated with key/value pairs.
    exit_dict = {}

    #setting 'property'
    if 'property' not in entry_dict:
        raise LookupError("property is not defined and is required")
    property = parse_pred.observedProperty(entry_dict['property'])
    exit_dict['property'] = property

    #setting 'source'
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

    #'lead_time'
    if 'LeadTime' in entry_dict:
        leadtime = parse_pred.lead_time(entry_dict['LeadTime'])
        if source == "METAR" or source == "MARINE":
            raise Exception(
                "variable cannot have lead time and be an observation")
        exit_dict['lead_time'] = leadtime

    #'duration' and, if not instantaneous, 'duration_method'
    if 'Duration' in entry_dict:
        dur_dict = parse_pred.duration(entry_dict['Duration'])
        duration = dur_dict['time']
        if duration > 0: #duration will now always be a value, > 0 means period variable
            duration_cell_method = dur_dict['cell_method']
            exit_dict['duration'] = duration
            exit_dict['duration_method'] = duration_cell_method
        else: #duration equals zero means instant variable
            exit_dict['duration'] = duration

    #'vert_coord1' and, if multi-layered, 'vert_coord2' and 'vert_method'
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
        try:
            units = vert_coord_dict['units']
            if units=='mb': units='hPa'
            exit_dict['vert_units'] = units
        except:
            pass

    return exit_dict

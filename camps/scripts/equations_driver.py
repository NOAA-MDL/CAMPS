#!/usr/bin/env python
import sys
import os
import logging
import copy
import pdb
import functools
import numpy as np
import re
from pint import UnitRegistry
from netCDF4 import Dataset
from datetime import timedelta
from operator import add

from ..registry import util as cfg
from ..StatPP.regression import plr

from ..mospred import read_pred as read_pred
from ..mospred import create as create
from ..mospred import parse_pred as parse_pred
from ..mospred import procedures as procedures
from ..mospred import interp

from ..core import Time as Time
from ..core.writer import write
from ..core import equations as eq_writer
from ..core import reader as reader
from ..core.Camps_data import Camps_data as Camps_data
from ..core import util as util
from ..registry.constants import international_units


"""Module: forecast_driver.py

Methods:
    main
    get_predictors
    get_predictands
"""


global control


def main():
    """This script performs regression of predictands against predictors,
    resulting in forecast equations for the predictands."""

    #--------------------------------------------------------------------------
    # Read equations_control file
    #--------------------------------------------------------------------------
    # If driver is run with a control file passed as an argument, it will read
    # it, otherwise it will read the default equations_control.yaml file
    import sys
    control_file = None if len(sys.argv) != 2 else sys.argv[1]
    if control_file is not None:
        control = cfg.read_control(control_file)
        logging.info("Control File: " + str(control_file) + " successfully read")
    else:
        raise RuntimeError("A control file must be provided for camps_equations.py.  Exiting program.")

    #--------------------------------------------------------------------------
    # Set up logging
    #--------------------------------------------------------------------------
    if control.log_file:
        out_log = open(control.log_file, 'w+')
        sys.stdout = out_log
        sys.stderr = out_log
    try:
        logging.getLogger('').handlers = []
        level = logging.getLevelName(control.debug_level)
        logging.basicConfig(level=level)
    except:
        logging.error("Logging setup failed")
        raise

    # Read valid station definitions and list of selected stations
    selected_stations = util.read_station_list(control.selected_stations)
    selected_stations, station_defs = util.read_station_table(control.station_defs, selected_stations)

    # Determine Start and end time, and stride.
    i_season = 0 #set index of date range (implicitly consists of a season).
    for i,times in enumerate(control.date_range):

        fcst_ref_time = times.split('-')[0][-2:]
        start,end,stride = read_pred.parse_range(times)
        start_time = Time.epoch_time(start)
        end_time = Time.epoch_time(end)
        times = list(range(start_time,end_time+stride,stride))
        logging.info('start: ' + str(start))
        logging.info('end: ' + str(end))
        logging.info('stride: ' + str(stride))

        # Get predictor/predictand yaml file
        pred_file = control.pred_file

        # Get global lead times if available
        try:
            lead_times = cfg.read_yaml(pred_file).global_config['lead_times']
            for i in range(len(lead_times)):
                lead_times[i] = parse_pred.lead_time(lead_times[i])
        except TypeError:
            lead_times = None
        # Retrieve predictands and station list
        pands,stations = get_predictands(pred_file, times, selected_stations,control, lead_times)

        logging.info("Finished reading predictands")
        # Retrieve predictors
        pors = get_predictors(pred_file, times, fcst_ref_time, control, lead_times, stations)

        logging.info("Finished reading predictors")
        # Append data from current date range.
        if i_season == 0:
            predictands = pands
            predictors = pors
        else:
            for i_pand, pand in enumerate(pands):
                predictands[i_pand] += pand
            for i_por, por in enumerate(pors):
                predictors[i_por] += por
        i_season += 1
    # Run regression
    equations = plr.main_camps(control, predictors, predictands)

    # Write equations to netcdf file
    eq_writer.write_equations(control.filename, control, predictors, predictands, equations)

def get_predictors(pred_file, times, fcst_ref_time, control, lead_times, stations):
    """Get predictors dynamically."""

    # Read list of predictors from control file
    predictor_list = cfg.read_yaml(pred_file).predictors

    # Loop over each predictor and retrieve desired metadata and data
    predictors = []
    for entry_dict in predictor_list:
        # Check for variable specific lead times. If not found, use global lead times.
        # Raise error if neither are found.
        try:
            leads = [parse_pred.lead_time(lead) for lead in entry_dict.pop('lead_times')]
            # Format pred dictionary
            pred_dict = read_pred.get_variable(entry_dict)
        except KeyError:
            if lead_times is None:
                logging.error("Either a global list of lead times or a per variable list of lead times must be provided")
                raise
            leads = copy.copy(lead_times)
            # Format pred dictionary
            pred_dict = read_pred.get_variable(entry_dict)

        # Adjust entry dictionary
        pred_dict['reserved1'] = 'vector'

        # If smoothing, add to pred_dict metadata
        if 'Procedure' in entry_dict:
            indices = [i for i, s in enumerate(entry_dict['Procedure']) if 'smooth' in s]
            if len(indices) == 1:
                smooth, arg = procedures.get_procedure(entry_dict['Procedure'][indices[0]])
                pred_dict['smooth'] = int(arg[0])

        # Loop through lead times and fetch metadata and data for given predictor
        for i,L in enumerate(leads):
            lead = parse_pred.lead_time(L)
            pred_dict['reserved2'] = lead
            logging.info('pred_dict is:'+str(pred_dict))

            # Fetch predictor
            vars_arr = []
            for filepath in control.predictor_data_file:
                var = reader.read_var(filepath=filepath, forecast_time=times,**pred_dict)
                vars_arr.append(var)
            if None in vars_arr:
                logging.warning('Could not fetch all '+pred_dict['property']+'  predictors for lead time '+str(lead))
                logging.warning(str(vars_arr))
                continue

            for i,var in enumerate(vars_arr):
                if i==0:
                    stacked_var = var
                else:
                    stacked_var += var
            if len(stacked_var.data.shape)>1 and stacked_var.dimensions.index('stations') == 0:
                stacked_var.dimensions.insert(0,'phenomenonTime')
            stacked_var.add_metadata('leadtime',lead)
            stacked_var.data = np.ma.masked_greater_equal(stacked_var.data,9999)

            predictors.append(stacked_var)

    return predictors


def get_predictands(pred_file, times, selected_stations,control, lead_times):
    """Puts predictands in fetchable form and fetches."""

    # Read list of predictands from control file
    predictand_list = cfg.read_yaml(pred_file).predictands

    # Loop over all predictands in predictand list and lead times and retrieve metadata and data
    predictands = []
    for entry_dict in predictand_list:
        # Get global lead times if available
        try:
            leads = [parse_pred.lead_time(lead) for lead in entry_dict.pop('lead_times')]
        except:
            if lead_times is None:
                logging.error("Either a global list of lead times or a per variable list of lead times must be provided")
                raise
            leads = copy.copy(lead_times)

        # Adjust entry dictionary
        if isinstance(entry_dict['Source'],list):
            Source = entry_dict.pop('Source')
            entry_dict['Source'] = ' '.join(Source)
        entry_dict['property'] = parse_pred.observedProperty(entry_dict['property'])
        vertical_coordinate = entry_dict.pop('Vertical_Coordinate')
        entry_dict['vert_coord1'],entry_dict['vert_units'] = parse_pred.vertical_coordinate(vertical_coordinate).values()
        logging.info('entry_dict is:'+str(entry_dict))

        # Loop through lead times and fetch metadata and data for given predictand
        for j,L in enumerate(leads):
            # Adjust start and end time based on lead time
            times2 = [t + int(L*3600) for t in times]
            # Fetch predictand
            vars_arr = []
            for filepath in control.predictand_data_file:
                var = reader.read_var(filepath=filepath, forecast_time=times2, **entry_dict)
                vars_arr.append(var)
            if None in vars_arr:
                logging.warning('Could not fetch all '+entry_dict['property']+' predictands for hour '+str(times[0]))
                logging.warning(str(vars_arr))
                continue

            # Stack retrieved data together and append to list of predictand data
            for i,var in enumerate(vars_arr):
                if i==0:
                    stacked_var = var
                else:
                    stacked_var += var

            # Check time variables to be sure it is dimensioned properly. If not, reshape it.
            for t in stacked_var.time:
                if t.get_dimensions().index('phenomenonTime')!=0:
                    t.data = t.data.reshape((-1,stacked_var.data.shape[stacked_var.dimensions.index('phenomenonTime')]))
            stacked_var.add_metadata('leadtime',L)
            if not np.all(stacked_var.data.data==9999):
                predictands.append(stacked_var)
    stations = predictands[0].location.get_stations()
    return (predictands,stations)


if __name__ == '__main__':
    main()

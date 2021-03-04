#!/usr/bin/env python
import sys
import os
import logging
import math
import copy
import pdb
import netCDF4
import functools
import numpy as np
from netCDF4 import Dataset
from netCDF4 import chartostring
from datetime import timedelta

from ..registry import util as cfg

from ..mospred import read_pred as read_pred
from ..mospred import parse_pred as parse_pred
from ..mospred import create as create
from ..mospred import procedures as procedures
from ..mospred import interp

from ..core import Time as Time
from ..core import Camps_data as Camps_data
from ..core.writer import write
from ..core import reader as reader
from ..core import util as util


global control

def main(control_file=None):
    """ """

    import sys

    # Get control file
    control_file = None if len(sys.argv) !=2 else sys.argv[1]
    if control_file is not None:
        control = cfg.read_forecast_control(control_file)
        logging.info("Control File: " + str(control_file) + " successfully read")
    else:
        raise RuntimeError("A control file must be provided for camps_forecast.  Exiting program.")
    # Setup logging
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

    # Read valid station definitions and selected station list.
    selected_stations = util.read_station_list(control.selected_stations)
    selected_stations, station_defs = util.read_station_table(control.station_defs, selected_stations)
    selected_station_defs = {k:v for k,v in station_defs.items() if k in selected_stations}
    # Determine lat and lon from selected stations
    lats = [i['lat'] for i in list(selected_station_defs.values())]
    lons = [i['lon'] for i in list(selected_station_defs.values())]
    # Retrieve list of predictors and predictands
    pred_list = cfg.read_yaml(control.pred_file)
    predictand_list = pred_list.predictands
    predictor_list = pred_list.predictors
    # Retrieve global lead times. Set to None if not found
    try:
        lead_times = pred_list.global_config['lead_times']
    except TypeError:
        lead_times = None
    # Determine start and end dates and stride
    start,end,stride = read_pred.parse_range(control.range[0])
    start_time = Time.epoch_time(start)
    end_time = Time.epoch_time(end)
    print(start_time, end_time, stride)
    times = list(range(start_time,end_time+stride,stride))
    # Read equations from equation file
    eq_dict = read_equations(control.equation_file)
    predictands = []
    predictors = []

    # loop through predictors, predictands, and lead times and fetch.
    sources = []
    for entry_dict in predictor_list:
        if entry_dict['Source'] not in sources:
            sources.append(entry_dict['Source'])
        # Retrieve predictor specific lead times. If empty, retrieve global. Raise error if both are empty.
        try:
            leads = [parse_pred.lead_time(lead) for lead in entry_dict.pop('lead_times')]
            pred_dict = read_pred.get_variable(entry_dict)
        except:
            if lead_times is None:
                logging.error("Either a global list of lead times or a per variable list of lead times must be provided")
                raise
            leads = copy.copy(lead_times)
            # Format pred dictionary
            pred_dict = read_pred.get_variable(entry_dict)

        # Adjust entry_dict for fetch
        pred_dict['reserved1'] = 'vector'

        # loop through lead times and fetch
        for i,L in enumerate(leads):
            lead = parse_pred.lead_time(L)
            pred_dict['reserved2'] = lead
            # Fetch predictors for each date and then stack data
            pred_arr = []
            for filepath in control.predictor_data_path:
                variable = reader.read_var(filepath=filepath, forecast_time=times,**pred_dict)
                pred_arr.append(variable)
            if None in pred_arr:
                logging.warning('Could not fetch all '+pred_dict['property']+' predictors for lead time '+str(lead))
                logging.warning(str(pred_arr))
                continue
            predictor, pred_stations,latitudes,longitudes = process_vars(selected_stations,pred_arr,lats, lons)
            predictor.add_metadata('leadtime',lead)
            predictor.location.set_stations(np.array(util.station_trunc(predictor.location.get_stations())))
            predictors.append(predictor)

    for entry_dict in predictand_list:
        # Retrieve predictor specific lead times if global was empty. Raise error if also empty.
        try:
            leads = [parse_pred.lead_time(lead) for lead in entry_dict.pop('lead_times')]
        except:
            if lead_times is None:
                logging.error("Either a global list of lead times or a per variable list of lead times must be provided")
                raise
            leads = copy.copy(lead_times)
        # Adjust entry_dict for fetch
        if isinstance(entry_dict['Source'],list):
            Source = entry_dict.pop('Source')
        entry_dict = read_pred.get_variable(entry_dict)
        if Source: entry_dict['source'] = ' '.join(Source)
        for i,L in enumerate(leads):
            lead = parse_pred.lead_time(L)
            # Adjust predictand start and end time using lead time
            times2 = [t + int(lead*3600) for t in times]
            vars_arr = []
            for filepath in control.predictand_data_path:
                variable = reader.read_var(filepath=filepath, forecast_time=times2,**entry_dict)
                vars_arr.append(variable)
            if None in vars_arr:
                logging.warning('Could not fetch all '+entry_dict['property']+' predictands for hour '+str(start_time2.hour))
                logging.warning(str(vars_arr))
                continue
            predictand,stations,latitudes,longitudes = process_vars(selected_stations, vars_arr, lats, lons)
            predictand.add_metadata('leadtime',lead)
            if not np.all(predictand.data.data==9999):
                predictands.append(predictand)

    # Reorder predictors to match order of coefficients
    pred_order = [n for pred_name in eq_dict['predictor_list'] for n,pred in enumerate(predictors) if pred.get_variable_name() == pred_name.strip()]
    predictors = [predictors[i] for i in pred_order]
    # Loop Predictand
    outputs = []
    valid_min = None
    valid_max = None
    eq_dict['stations'] = np.array(util.station_trunc(eq_dict['stations']))
    for p in range(len(predictands)):
        # Loop through stations
        output_name = predictands[p].name
        output_data = np.ma.zeros(predictands[p].data.shape)
        # Attempt to get a valid min and max for predictand. If no valid min, set to 0. If no valid max, pass.
        try:
            valid_min = predictands[p].valid_min
        except:
            valid_min = 0
        try:
            valid_max = predictands[p].valid_max
        except:
            pass
        for ns,s in enumerate(stations):
            st_index = np.where(eq_dict['stations'] == s)[0]
            try:
                st_index = st_index[0]
            except:
                continue
            const = eq_dict['equations'][st_index,-1,p]
            coefs = eq_dict['equations'][st_index,0:-1,p]

            assert len(coefs)==len(predictors),"number of coefficients and number of predictors must be equal"
            tot = np.ma.zeros(predictands[p].data[:,st_index].size)
            # Loop through coefs
            for nf,coef in enumerate(coefs):
                # Use coef, const, and predictor data to calculate new forecast
                pred_index = np.where(predictors[nf].location.get_stations() == s)[0][0]
                if len(predictors[nf].data.shape) > 2:
                    datapoint = predictors[nf].data[:,pred_index,0]
                else:
                    datapoint = predictors[nf].data[:,pred_index]
                tot+= datapoint * coef
            tot += const
            logging.info(str(predictands[p].data[:,st_index])+' at '+str(s))
            logging.info(str(tot)+' at '+str(s))
            output_data[:,st_index] = tot[:]
        if valid_min:
            output_data[output_data<valid_min] = np.ma.masked
        if valid_max:
            output_data[output_data>valid_max] = np.ma.masked
        # Create forecast output object
        forecast_obj = create_forecast_obj(output_name,predictands[p],start_time,end_time,stride,sources)
        # Set forecast data to object
        while len(output_data.shape)<len(forecast_obj.dimensions):
            output_data = output_data[...,None]
        forecast_obj.add_data(output_data)
        outputs.append(forecast_obj)
    outputs = consistency_check(outputs)
    # Create station object
    station_dim = cfg.read_dimensions()['nstations']
    station_obj = Camps_data('stations')
    station_obj.dimensions.append(station_dim)
    station_obj.add_metadata("fill_value", '_')
    station_name_arr = np.array(stations)
    station_obj.add_data(station_name_arr)

    # Create lat/lon objects
    lat_obj = Camps_data('latitude')
    lon_obj = Camps_data('longitude')
    lat_obj.dimensions = [station_dim]
    lon_obj.dimensions = [station_dim]
    lat_obj.data = np.array(latitudes)
    lon_obj.data = np.array(longitudes)


    outputs.append(station_obj)
    outputs.append(lat_obj)
    outputs.append(lon_obj)
    # Write forecasts to output file
    logging.info('Writing to '+control.output_file)
    write(outputs, control.output_file)


def read_equations(filename):
    """Reads equations file and returns dict"""

    logging.info('Reading equations')
    nc = Dataset(filename, 'r')
    stations = nc.variables['stations'][:]
    equations = nc.variables['MOS_Equations'][:]
    preds = chartostring(nc.variables['Equations_List'][0:-1])
    tands = chartostring(nc.variables['Predictand_List'][:])
    return {'stations':stations, 'equations':equations, 'predictor_list':preds,'predictand_list':tands}


def process_vars(selected_stations, vars_arr, lats, lons):
    """Stacks read variables into proper dimensions"""

    all_stations = [st.location.get_stations() for st in vars_arr]
    # Get only the stations and lats/lons we want
    if len(selected_stations[0])==4:
        intersected_stations = functools.reduce(np.intersect1d, all_stations).astype('<U4')
        indices = np.in1d(intersected_stations.astype('<U4'),list(selected_stations))
        indices2 = np.in1d(list(selected_stations),intersected_stations.astype('<U4'))
    elif len(selected_stations[0])==5:
        intersected_stations = functools.reduce(np.intersect1d, all_stations)
        intersected_stations = np.array(util.station_trunc(intersected_stations))
        indices = np.in1d(intersected_stations,list(selected_stations))
        indices2 = np.in1d(list(selected_stations),intersected_stations)
    stations = intersected_stations[indices]
    if len(lats)!=len(intersected_stations):
        lats = np.array(lats)[indices2]
        lons = np.array(lons)[indices2]
    for i,var in enumerate(vars_arr):
        var.data = var.data[:,indices]
        if i==0:
            stacked_var = copy.copy(var)
        else:
            stacked_var += var
 
    return (stacked_var,stations, lats, lons)


def create_forecast_obj(output_name,predictand,start,end,stride,sources):
    """ Create forecast object for write out """

    logging.info("Creating "+output_name+" forecast object")
    forecast_obj = Camps_data(output_name)
    # Use predictand metadata to create a forecast object.
    forecast_obj.dimensions = copy.deepcopy(predictand.dimensions)
    forecast_obj.time = copy.deepcopy(predictand.time)
    # Create needed time objects
    FcstRef_Times = Time.ForecastReferenceTime(**{'start_time':start,'end_time':end,'stride':stride})
    forecast_obj.time.append(FcstRef_Times)
    FcstTime_hour = Time.epoch_to_datetime(FcstRef_Times.data[0]).hour
    forecast_obj.metadata.update(predictand.metadata)
    LeadTime = Time.LeadTime(data=np.ma.array([forecast_obj.metadata['leadtime']]))
    forecast_obj.time.append(LeadTime)
    forecast_obj.metadata['FcstTime_hour'] = FcstTime_hour
    if 'PROV__hadPrimarySource' in list(forecast_obj.metadata.keys()):
        forecast_obj.metadata['PROV__hadPrimarySource'] = sources
    forecast_obj.add_process('MOS_Method')
    forecast_obj.location = predictand.location
    forecast_obj.add_vert_coord(predictand.get_coordinate())
    try:
        fp = forecast_obj.metadata.pop('filepath')
    except:
        pass

    return forecast_obj

def consistency_check(outputs):
    """ Check related output variables for logical consistency """

    # Loop through output variables. If temp is found, extract rest of variable name.
    # Loop through again. If dew point is found, compare rest of variable name (lead
    # time, level, etc). If match is found, find any place in data where dew point is
    # greater than temp and average the two, replacing old values with new averaged values.
    new_outputs = []
    for Var in outputs:
        Var_name = Var.name.split('/')[-1]
        if Var_name == 'Temp':
            long_name = Var.get_variable_name()
            name_desc = long_name.replace(Var_name,'')
            for V in outputs:
                if V.name.split('/')[-1]=='DewPt' and V.get_variable_name().replace(V.name.split('/')[-1],'')==name_desc:
                    # Create copies of Temp and DewPt objects for CmpChk output
                    T_Var = copy.copy(Var)
                    T_Var.time = copy.copy(Var.time)
                    T_Var.processes = copy.copy(Var.processes)
                    D_Var = copy.copy(V)
                    D_Var.time = copy.copy(V.time)
                    D_Var.processes = copy.copy(V.processes)
                    T_data = T_Var.data
                    D_data = D_Var.data
                    bad_data = np.where((D_data>T_data) & (D_data!=9999) & (T_data!=9999))
                    avgs = (T_data[bad_data]+D_data[bad_data])/2
                    T_data[bad_data] = avgs
                    D_data[bad_data] = avgs
                    T_Var.add_process('TmpDewCmpChk')
                    new_outputs.append(T_Var)
                    D_Var.add_process('TmpDewCmpChk')
                    new_outputs.append(D_Var)
    outputs += new_outputs
    return outputs


if __name__ == '__main__':
    try:
        main(sys.argv[1])
    except IndexError:
        main()

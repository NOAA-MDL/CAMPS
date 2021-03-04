#!/usr/bin/env python
import sys
import os
import logging
import copy
import pdb
import functools
import numpy as np
from datetime import timedelta
import argparse
from pint import UnitRegistry

from ..registry import util as cfg

from ..mospred import read_pred as read_pred
from ..mospred import create as create
from ..mospred import procedures as procedures
from ..mospred import parse_pred as parse_pred
from ..mospred import interp as interp

from ..core import Time as Time
from ..core import Camps_data as Camps_data
from ..core.writer import write
from ..core.reader import read_var
from ..core import util as util
from ..registry.constants import international_units



"""Module: mospred_driver.py

Methods:
    main
    get_predictors
    get_predictands
    process_vars
    combine_source
    check_units
    convert_units
"""


global control


def main():
    """Driver for mospred.
    Processes predictors and predictands.
    Will take a list of predictors, calculate those that are unavailable,
    apply procedures, and interpolate to stations.
    Will take a list of predictands, calculate those that are unavailable.
    Output saved to CAMPS netcdf file.
    """

    #--------------------------------------------------------------------------
    # Read mospred_control file
    #--------------------------------------------------------------------------
    # If driver is run with a control file passed as an argument, it will read
    # it, otherwise it will fail.
    import sys
    control_file = None if len(sys.argv) != 2 else sys.argv[1]
    if control_file is not None:
        control = cfg.read_control(control_file)
        logging.info("Control File: " + str(control_file) + " successfully read")
    else:
        raise RuntimeError("A control file must be provided for camps_mospred.  Exiting program.")

    # Pull variables from the mospred control file
    date_range_list = control.date_range # Array of date ranges and strides
    fcst_ref_time = control.date_range[0].split('-')[0][-2:]
    debug_level = control.debug_level
    num_procs = control.num_processors
    pred_file = control.pred_file
    selected_stations = util.read_station_list(control.selected_stations)
    selected_stations, station_defs = util.read_station_table(control.station_defs, selected_stations)
    try:
        lead_times = cfg.read_yaml(pred_file).global_config['lead_times']
        for i in range(len(lead_times)):
            lead_times[i] = parse_pred.lead_time(lead_times[i])
    except TypeError:
        lead_times = None

    #--------------------------------------------------------------------------
    # Set up logging
    #--------------------------------------------------------------------------
    log_file = control.log_file
    if log_file:
        out_log = open(log_file, 'w+')
        sys.stdout = out_log
        sys.stderr = out_log
    try:
        logging.getLogger('').handlers = []
        level = logging.getLevelName(debug_level)
        logging.basicConfig(level=level)
    except:
        logging.error("Logging setup failed")
        raise

    #---------------------------------------------------------------------------
    # Get station information and lat/lon info and create camps objects for each
    #---------------------------------------------------------------------------
    selected_station_defs = {k:v for k,v in station_defs.items() if k in selected_stations}
    # Get lat and lon values for selected stations
    sta_ind = [list(selected_station_defs.keys()).index(s) for s in selected_stations if s in list(selected_station_defs.keys())]
    lats = [i['lat'] for i in list(selected_station_defs.values())]
    lats = [lats[i] for i in sta_ind]
    lons = [i['lon'] for i in list(selected_station_defs.values())]
    lons = [lons[i] for i in sta_ind]
    # Get station abbreviations
    station_names = list(np.array(list(selected_station_defs.keys()))[sta_ind])
    # Get station dimension
    station_dim = cfg.read_dimensions()['nstations']

    # Create lat/lon objects
    lat_obj = Camps_data('latitude')
    lon_obj = Camps_data('longitude')
    lat_obj.dimensions = [station_dim]
    lon_obj.dimensions = [station_dim]
    lat_obj.data = np.array(lats)
    lon_obj.data = np.array(lons)

    # Create station object
    station_obj = Camps_data('stations')
    station_obj.dimensions.append(station_dim)
    station_obj.add_data(np.array(station_names))


    #--------------------------------------------------------------------------
    # Check control file for predictor and/or predictand tag
    # run get_predictors and/or get_predictands if set to True
    #--------------------------------------------------------------------------
    if control.predictors is True:

        # Get reprojection information for future interpolation
        projparams, LL_lat, LL_lon, dx, dy = interp.get_projparams(control.predictor_data_path[0])

        # Reproject grid
        xi_x,xi_y = interp.reproject(projparams,LL_lat,LL_lon,dx,dy,lons,lats)

        # Retrieve predictors and write to file
        get_predictors(control, pred_file, fcst_ref_time, date_range_list, selected_stations, selected_station_defs, xi_x, xi_y, lead_times, lat_obj, lon_obj, station_obj)

    if control.predictands is True:
        # Retrieve predictands and write to file
        get_predictands(pred_file, date_range_list, selected_stations, selected_station_defs, control,lons,lats, lead_times, fcst_ref_time)



def get_predictors(control, predictor_file, fcst_ref_time, date_range_list, selected_stations, selected_station_defs, xi_x, xi_y, lead_times, lat_obj, lon_obj, station_obj):


    #--------------------------------------------------------------------------
    # Get and process information from the pred.yaml file
    #--------------------------------------------------------------------------
    # Read the predictors; stored as a list of dictionaries
    pred_list = cfg.read_yaml(predictor_file).predictors

    # Preprocess the predictor dictionary into fetchable metadata
    formatted_predictors = []
    leads_list = []
    for entry_dict in pred_list:
        #NOTE: it is possible that pred_list has lead_time set in it.
        #If that is the case, then it makes sure to add it into the formatted_pred
        #object.  However it is overwritten by the next loop where we use the
        #lead time given in the global_config section of the predictors.yaml file
        #as the lead time we operate on.  Can we take the lead time functionality
        #out of the preprocess_entries function?  Unless it is used elsewhere...
        try:
            leads = entry_dict.pop('lead_times')
            formatted_pred = create.preprocess_entries(entry_dict, fcst_ref_time)
            for i,lead in enumerate(leads):
                leads[i] = parse_pred.lead_time(lead)
                pred = copy.deepcopy(formatted_pred)
                pred['leadTime'] = leads[i]
                pred['search_metadata']['lead_time'] = leads[i]
                formatted_predictors.append(pred)
                leads_list.append(leads[i])
        except KeyError:
            if lead_times is None:
                logging.error("Either a global list of lead times or a per variable list of lead times must be provided")
                raise
            else:
                formatted_pred = create.preprocess_entries(entry_dict, fcst_ref_time)
                for i,j in enumerate(lead_times):
                    pred = copy.deepcopy(formatted_pred)
                    pred['leadTime'] = lead_times[i]
                    pred['search_metadata']['lead_time'] = lead_times[i]
                    formatted_predictors.append(pred)
                    leads_list.append(j)


    #-------------------------------------------------------------------------
    # Multi-Input File check
    #-------------------------------------------------------------------------
    # Check length of input file list and begin loop over If length is 1, loop over all date
    # ranges with the single file. If length > 1, loop over a date range for
    # each input range based on list index.
    #-------------------------------------------------------------------------
    # An array to hold all the computed variables for date range
    computed_vars = [[] for _ in range(len(control.predictor_data_path))]
    input_len = len(control.predictor_data_path)
    time_dim_name = cfg.read_dimensions()['time']
    for file_ind, input_file in enumerate(control.predictor_data_path):

        #--------------------------------------------------------------------------
        # Main loop to fetch/create, apply procedures, and interpolate predictors
        # onto stations
        #--------------------------------------------------------------------------

        # Check number of input files.
        # If only 1 file, Loop through date ranges specified in the control file.
        # If more than 1, be sure number of date ranges and number of input files are
        # equal. Then, go through 1 date range per input file
        if input_len==1:
            date_range_loop = date_range_list
        elif input_len>1:
            if input_len==len(date_range_list):
                date_range_loop = [date_range_list[file_ind]]
            else:
                raise ValueError
        for date_range in date_range_loop:

            # create list of times using start, end, and stride times
            start,end,stride = read_pred.parse_range(date_range)
            start = Time.epoch_time(start)
            end = Time.epoch_time(end)

            if start == end: #Then we only have 1 day of data, stacking won't work later
                date_range_len = 1
            else:
                date_range_len = 2

            times = list(range(start,end+stride,stride))
            logging.info("Processing date range beginning on date: "+str(Time.epoch_to_datetime(times[0]))[:10])


            # Loop through predictors
            for n,pred in enumerate(formatted_predictors):
                logging.info("Property: "+ str(pred['search_metadata']['property']))
                pred['search_metadata']['reserved1'] = 'grid'
                # Try to fetch the exact variable asked for
                variable = read_var(filepath=input_file, forecast_time=times,**pred['search_metadata'])

                # If the call to fetch doesn't find the variable,
                # then see if it can be calculated.
                if variable is None:
                    variable = create.calculate(input_file, times, pred, station_list=selected_stations, station_defs=selected_station_defs)

                if isinstance(variable, Camps_data):
                    # Apply procedures set in the predictor.yaml file to the variable.
                    variable = procedures.apply_procedures(variable, pred['procedures'], xi_x, xi_y)
                    # Add leadtime to the camps object.
                    variable.add_metadata('leadtime', pred['leadTime'])
                    computed_vars[file_ind].append(variable)


        # Check if outfile in control is a list. If yes, determine that length of list
        # is same as length of input files and greater than 1. Then write to each outfile per input file.
        if isinstance(control.predictor_outfile,list) and len(control.predictor_outfile)>1:
            if len(control.predictor_outfile)==input_len:
                # Set current output file
                outfile = control.predictor_outfile[file_ind]
                finalize_predictors(outfile, computed_vars[file_ind], lat_obj, lon_obj, station_obj, leads_list, time_dim_name, control.components)
            elif len(control.predictor_outfile)>1 and len(control.predictor_outfile)!=input_len:
                # If length of output file list greater than 1 but not equal to length of input file list:
                # raise error
                raise ValueError("Number of predictor output files must either be singular or equal to number of predictor input files")


    # Check if outfile is a list of length 1 or a string.
    if ((isinstance(control.predictor_outfile,list) and len(control.predictor_outfile)==1) or (isinstance(control.predictor_outfile,str))):
        if isinstance(control.predictor_outfile,list):
            outfile = control.predictor_outfile[0]
        else:
            outfile = control.predictor_outfile
        combined_predictors = []
        for n,preds in enumerate(computed_vars):
             if n==0:
                 combined_predictors.extend(copy.copy(preds))
                 continue
             for m,pred in enumerate(preds):
                 combined_predictors[m] += pred
             
        finalize_predictors(outfile, combined_predictors, lat_obj, lon_obj, station_obj, leads_list, time_dim_name, control.components)



def finalize_predictors(outfile,combined_predictors,lat_obj,lon_obj,station_obj,leads_list,time_dim_name,components):

    for n,pred in enumerate(combined_predictors):
        pred.properties['reserved2'] = leads_list[n%len(leads_list)]
        if 'filepath' in list(pred.metadata.keys()):
            fp = pred.metadata.pop('filepath')
        pred.dimensions.insert(0, time_dim_name)
    combined_predictors = check_units(combined_predictors)

    combined_predictors.append(lat_obj)
    combined_predictors.append(lon_obj)
    combined_predictors.append(station_obj)
    write(combined_predictors, outfile, components)



def get_predictands(predictand_file, date_range_list, selected_stations, selected_station_defs, control, lons, lats, lead_times, fcst_ref_time):
    """Puts predictands in fetchable form and fetches."""

    # Get list of desired predictands from predictand_file
    predictand_list = cfg.read_yaml(predictand_file)

    # Loop over date_ranges from control file
    # creating lists of desired times from start, end, and stride times
    times_lists = []
    for date_range in date_range_list:

        # Set up time Loop
        start,end,stride = read_pred.parse_range(date_range)
        start_time = Time.epoch_time(start)
        end_time = Time.epoch_time(end)
        times = list(range(start_time,end_time+stride,stride))
        times_lists.append(times)

    # Loop over desired predictands and lead times and fetch for each desired time
    predictands = []
    for tands in predictand_list.predictands:
        entry_dict = copy.copy(tands)
        try:
            leads = [parse_pred.lead_time(lead) for lead in entry_dict.pop('lead_times')]
        except KeyError:
            if lead_times is None:
                logging.error("Either a global list of lead times or a per variable list of lead times must be provided")
                raise
            leads = copy.copy(lead_times)
        pred = {}
        pred.update({'search_metadata' : entry_dict})
        pred.update({'fcst_ref_time' : fcst_ref_time})
        pred['search_metadata'].update({'property' : parse_pred.observedProperty(pred['search_metadata'].get('property'))})
        if 'Vertical_Coordinate' in list(pred['search_metadata'].keys()):
            vertical_coordinate = pred['search_metadata'].pop('Vertical_Coordinate')
        if 'Duration' in pred['search_metadata'].keys():
            duration = pred['search_metadata'].pop('Duration')
            pred['search_metadata'].update({'duration' : parse_pred.duration(duration)['time']})
        if 'duration_method' not in pred['search_metadata'].keys():
            pred['search_metadata'].update({'duration_method' : None})
        pred['search_metadata']['vert_coord1'],pred['search_metadata']['vert_units'] = parse_pred.vertical_coordinate(vertical_coordinate).values()
        logging.info('entry_dict is:'+str(pred['search_metadata']))
        Source = list(pred['search_metadata'].pop('Source'))
        # Loop over file_ids associated with predictand input files
        source_vars = []
        for n,filepath in enumerate(control.predictand_data_path):
            variables = []
            pred['search_metadata'].update({'source' : Source[n]}) #needed for fetching
            for j,L in enumerate(leads):
                pred.update({'leadTime' : L})
                # Adjust start and end time based on desired forecast lead time
                for Ti,T in enumerate(times_lists):
                    times2 = [t + int(L*3600) for t in T]
                    # Fetch variable for each desired time
                    vars_arr = read_var(filepath=filepath, forecast_time=times2,**pred['search_metadata'])
                    if vars_arr is None:
                        vars_arr = create.calculate(filepath, times2, pred, station_list=selected_stations, station_defs=selected_station_defs)

                    variables.append(vars_arr)

            # Combine vars from different lead times into single list
            vars_arr = [sub_var for sub_var in variables if sub_var is not None]
            if len(vars_arr)==0:
                logging.error('\nCould not create any data for predictand %02dZ %s from source  %s!',\
                    int(pred.get('fcst_ref_time'),entry_dict.get('property'),Source[n]))
            # Combine vars from different sources into a single list
            source_vars.append(vars_arr)

        if all(np.all(v.data.data==9999) for var in source_vars for v in var):
            logging.warning("No valid returns for predictand: "+pred.search_metadata['property']+". Not writing out.")
            continue
        else:
            # Process_vars checks pulled station data against station list and then stack each by time
            predictand,stations, latitudes, longitudes = process_vars(selected_stations, source_vars, lats, lons)
        # Set prov_hadPrimarySource based on all sources used
        prov_hPS = predictand.metadata.pop('PROV__hadPrimarySource')
        predictand.metadata['PROV__hadPrimarySource'] = ' '.join(Source)
        # Remove filepath from metadata and append object to predictands list
        if 'filepath' in predictand.metadata.keys():
            filepath = predictand.metadata.pop('filepath')
        predictands.append(predictand)

    # Check to be sure at least 1 predictand object was created. If not, raise error
    if len(predictands) > 0:

        # Check units of predictands against international_units dictionary
        predictands = check_units(predictands)

        # Add lat, lon and station objects to combined predictand object list
        # Station object
        station_names = stations
        station_dim = cfg.read_dimensions()['nstations']
        station_obj = Camps_data('stations')
        station_obj.dimensions.append(station_dim)
        station_obj.add_metadata("fill_value", '_')
        station_obj.add_data(station_names)

        # latitude object
        lat_obj = Camps_data('latitude')
        lat_obj.dimensions.append(station_dim)
        lat_obj.add_data(np.array(latitudes))

        # longitude object
        lon_obj = Camps_data('longitude')
        lon_obj.dimensions.append(station_dim)
        lon_obj.add_data(np.array(longitudes))
        predictands.append(station_obj)
        predictands.append(lat_obj)
        predictands.append(lon_obj)

        #write list of predictands to netcdf file
        write(predictands, control.predictand_outfile, control.components)
    else:
        logging.error('\n\n\nNO predictand data fetched or created for given date ranges and strides!!\n\n')


def process_vars(selected_stations, var_list, lats, lons):
    """Limit variable arrays to selected stations and
    combine together by time coordinate.
    """

    out_vars = []
    latlon_indices = np.array([False])
    for vars_arr in var_list:
        all_stations = [st.location.get_stations() for st in vars_arr if st.location is not None]
        # Get only the stations and lats/lons we want
        # Check whether length of station names is 4 or 5 characters
        # and adjust accordingly
        if len(selected_stations[0])==4:
            intersected_stations = np.array(functools.reduce(np.intersect1d, all_stations))
            indices = np.in1d(intersected_stations,list(selected_stations))
            indices2 = np.in1d(list(selected_stations),intersected_stations)
        elif len(selected_stations[0])==5:
            intersected_stations = functools.reduce(np.intersect1d, all_stations)
            intersected_stations = np.array(util.station_trunc(intersected_stations))
            indices = np.in1d(intersected_stations,list(selected_stations))
            indices2 = np.in1d(list(selected_stations),intersected_stations)
        latlon_indices = latlon_indices+indices2
        # There may be some repetition of station names, finding all unique names
        # and creating a new index for the data index.
        stations,uniq_ind = np.unique(intersected_stations[indices], return_index=True)
        # Sort vars by phenomenon time
        inds = np.argsort([v.time[0].data[0] for v in vars_arr])
        vars_arr = np.array(vars_arr)[inds]

        # Loop over array of times and then stack the variables together
        phenom_times = []
        for i,var in enumerate(vars_arr):
            if var.data.shape[1]==len(indices2):
                var.data = var.data[:,indices2][:,uniq_ind]
            elif var.data.shape[1]==len(indices):
                var.data = var.data[:,indices][:,uniq_ind]
            if var.location is not None:
                var.location.set_stations(stations)

            if i==0:
                stacked_data = var
                phenom_times.extend(var.get_phenom_time().data)
            else:
                phenom_inds = np.where(~np.isin(var.get_phenom_time().data,phenom_times))[0]
                if len(phenom_inds)==0: continue
                else:
                    var.data = var.data[phenom_inds,:]
                    var.get_phenom_time().data = var.get_phenom_time().data[phenom_inds]
                    stacked_data += var
                    phenom_times.extend(var.get_phenom_time().data)
                    # Compare metadata of var with stacked_data.
                    if stacked_data.location is None:
                        stacked_data.location = copy.copy(var.location)
                    if len(stacked_data.processes)==0:
                        stacked_data.processes = copy.deepcopy(var.processes)
                    if len(stacked_data.metadata)<len(var.metadata):
                        stacked_data.metadata = copy.copy(var.metadata)
                    if len(stacked_data.properties)<len(var.properties):
                        stacked_data.properties = copy.copy(var.properties)

        # Reshape the stacked data for dimensionality
        if len(var.dimensions)>len(stacked_data.data.shape):
            stacked_data.data = np.reshape(stacked_data.data, (len(phenom_times),var.data.shape[0]))
        if len(var.dimensions)!=len(stacked_data.data.shape):
            stacked_data.data = np.expand_dims(stacked_data.data,-1)
        try: 
            if stacked_data.data.fill_value > 9999: 
                stacked_data.data.fill_value = 9999
        except:
            stacked_data.data = np.ma.masked_equal(stacked_data.data, 9999)
        out_vars.append(stacked_data)

    if len(out_vars) == 1:
        out_var = out_vars[0]
    elif len(out_vars) > 1:
        out_var = combine_source(out_vars)

    out_t_inds = np.argsort(out_var.time[0].data)
    out_var.time[0].data = out_var.time[0].data[out_t_inds]
    out_var.data = out_var.data[out_t_inds,...]
    stations = np.array(selected_stations)[latlon_indices]
    lats = np.array(lats)[latlon_indices]
    lons = np.array(lons)[latlon_indices]
    return (out_var, stations, lats, lons)


def combine_source(in_vars):
    """For a variable with multiple sources:
    combine data objects into single object.
    """

    out_var = in_vars[0]
    sta = out_var.location.get_stations()
    for n in range(1,len(in_vars)):
        out_var.data = np.concatenate((out_var.data,in_vars[n].data),axis=1)
        [out_var.add_process(proc.name) for proc in in_vars[n].processes if proc.name not in out_var.get_process_str()]
        # Join station information together
        sta = np.concatenate((sta,in_vars[n].location.get_stations()),axis=0)
    # Sort compiled stations and the data
    sta_ind = np.argsort(sta)
    sta = sta[sta_ind]
    out_var.data = out_var.data[...,sta_ind]
    out_var.location.set_stations(sta)


    return out_var


def check_units(pred):
    """check units of predictors or predictands against
    dictionary of international unit standards.
    If they do not match, convert pred units to match
    standard units
    """

    # Get unit registy for conversions
    ureg = UnitRegistry()
    Q = ureg.Quantity

    # Loop through all predictands or predictors, comparing the units
    # for a given variable to the units in the international units dictionary.
    # If the units do not match, convert to the international units.
    for p in pred:
        p_name = p.get_observedProperty()
        p_data = np.ma.getdata(p.data)
        p_mask = np.ma.getmaskarray(p.data)
        try:
            p_units = p.units
        except:
           logging.error("pred, "+p_name+", does not contain units")
           raise
        if p_units == 'dimensionless': #skip conversion if units are dimensionless
            continue

        try:
            name = [n for n in international_units if n in p_name][0]
            int_units = international_units[name]
        except:
            logging.warning("pred, "+p_name+", not found in unit standards. Leaving units as is.")
            continue

        if p_units != int_units:
            logging.info("pred units, "+p_units+", do not match unit standards, "+int_units+". Converting.")
            p_data = np.ma.array(p_data).astype(np.float)
            p_data[:] = convert_units(p_data,p_name,p_units,int_units,Q)
            p.units = int_units
            p.metadata['units'] = int_units
            if hasattr(p,'valid_max'):
                p.valid_max = float(convert_units(p.valid_max,p_name,p_units,int_units,Q))
                p.metadata['valid_max'] = p.valid_max
            if hasattr(p,'valid_min'):
                p.valid_min = float(convert_units(p.valid_min,p_name,p_units,int_units,Q))
                p.metadata['valid_min'] = p.valid_min
        p.data = np.ma.array(p_data, mask=p_mask)

    return pred


def convert_units(data, name, in_unit, out_unit, Q):
    """Do unit converstion"""

    if "Precip" in name and 'in' in in_unit:
        # For precip, a direct conversion from 'in' to 'kg m**-2' is not possible.
        # Converts from inch to meter then multiples by 'kg m**-3' to complete
        # desired conversion.
        q_data = Q(data,in_unit)
        q_data.ito('meter')
        q_data *= Q(1000.0,'kg m**-3')
        p_data = np.array(q_data)
    else:
        p_data = np.array(Q(data,in_unit).to(out_unit))

    p_data[data==9999] = 9999
    p_data[data==-9999] = -9999

    return p_data


if __name__ == '__main__':
    main()

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
from ..registry.db.update_db import update

from ..mospred import read_pred as read_pred
#from ..mospred import util as util
from ..mospred import create as create
from ..mospred.create import Predictor
from ..mospred import procedures as procedures
from ..mospred import parse_pred as parse_pred
from ..mospred import interp as interp

from ..core import Time as Time
from ..core import Camps_data as Camps_data
from ..core.fetch import *
from ..core.writer import write
from ..core.reader import read_var
from ..core import util as util
from ..registry.constants import international_units


global control

def main():
    """
    Driver for mospred.
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
    log_file = control.log_file

    #--------------------------------------------------------------------------
    # Set up logging
    #--------------------------------------------------------------------------
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
    selected_station_defs = {k:v for k,v in station_defs.iteritems() if k in selected_stations}
    # Get lat and lon values for selected stations
    lats = [i['lat'] for i in selected_station_defs.values()]
    lons = [i['lon'] for i in selected_station_defs.values()]
    # Get station abbreviations
    station_names = selected_station_defs.keys()
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
    station_obj = Camps_data('station')
    station_obj.dimensions.append(station_dim)
    dim_name = cfg.read_dimensions()['chars']
    station_obj.dimensions.append(dim_name)
    station_obj.add_metadata("fill_value", '_')
    max_char = np.max([len(s) for s in station_names])
    for n,s in enumerate(station_names):
        if len(s)< max_char:
            s = s+' '*(max_char-len(s))
        char_arr = np.array(list(s), 'c')
        if n == 0:
            station_name_arr = char_arr
        else:
            station_name_arr = np.vstack((station_name_arr, char_arr))
    station_obj.add_data(station_name_arr)


    #--------------------------------------------------------------------------
    # Check control file for predictor and/or predictand tag 
    # run get_predictors and/or get_predictands if set to True
    #--------------------------------------------------------------------------
    if control.predictors is True:

        # Get reprojection information for future interpolation
        #pdb.set_trace()
        projparams, LL_lat, LL_lon = interp.get_projparams(control.predictor_data_path[0])
        # Reproject grid
        xi_x,xi_y = interp.reproject(projparams,LL_lat,LL_lon,lons,lats)

        # Retrieve predictors and write to file
        get_predictors(control, pred_file, fcst_ref_time, date_range_list, selected_stations, selected_station_defs, xi_x, xi_y, lead_times, lat_obj, lon_obj, station_obj)

    if control.predictands is True:
        # Retrieve predictands and write to file
        get_predictands(pred_file, date_range_list, selected_stations, selected_station_defs, control,lons,lats, lead_times, fcst_ref_time)



def get_predictors(control, predictor_file, fcst_ref_time, date_range_list, selected_stations, selected_station_defs,xi_x,xi_y,lead_times, lat_obj, lon_obj, station_obj):

    #--------------------------------------------------------------------------
    # Update the database
    #--------------------------------------------------------------------------
    # Check to see if the variable table is empty or missing files from the
    # input path provided in the control file. If it is then the function will
    # populate the variable table in the database with the input data provided.
    file_id = update(control.predictor_data_path[0])
    #--------------------------------------------------------------------------

    #--------------------------------------------------------------------------
    # Get and process information from the predictors.yaml file
    #--------------------------------------------------------------------------
    # Read the predictors; stored as a list of dictionaries
    pred_list = cfg.read_yaml(predictor_file).predictors

    # Preprocess the predictor dictionary into fetchable metadata
    formatted_predictors = []
    leads_list = []
    for entry_dict in pred_list:
        #NOTE: it is possible that pred_list has lead_time set in it...
        #if that is set then it makes sure to add it into the formatted_pred
        #object...however it is overwritten by the next loop where we use the
        #lead time given in the global_config section of the predictors.yaml file
        #as the lead time we operate on.  Can we take the lead time functionality
        #out of the preprocess_entries function?  Unless it is used elsewhere...
        if lead_times is None:
            try:
                leads = entry_dict.pop('lead_times')
            except KeyError:
                logging.error("Either a global list of lead times or a per variable list of lead times must be provided")
                raise
            formatted_pred = create.preprocess_entries(entry_dict, fcst_ref_time)
            for i,lead in enumerate(leads):
                leads[i] = parse_pred.lead_time(lead)
                pred = formatted_pred.copy()
                pred.leadTime = leads[i]
                pred.search_metadata['lead_time'] = leads[i]
                formatted_predictors.append(pred)
                leads_list.append(leads[i])
        else:
            if 'lead_times' in entry_dict.keys():
                lead_unneeded = entry_dict.pop('lead_times')
            formatted_pred = create.preprocess_entries(entry_dict, fcst_ref_time)
            for i,j in enumerate(lead_times):
                pred = formatted_pred.copy()
                pred.leadTime = lead_times[i]
                pred.search_metadata['lead_time'] = lead_times[i]
                formatted_predictors.append(pred)
                leads_list.append(j)


    #--------------------------------------------------------------------------
    # Main loop to fetch/create, apply procedures, and interpolate predictors
    # onto stations
    #--------------------------------------------------------------------------

    # Loop through date ranges specified in the control file.
    # NOTE: this implies there could be mutilpe date ranges per run...?
    for date_range in date_range_list:

        # An array to hold all the computed variables for date range
        computed_vars = [[] for _ in range(len(formatted_predictors))]

        # set up date range Loop
        start,end,stride = read_pred.parse_range(date_range)
        start = Time.str_to_datetime(start)
        end = Time.str_to_datetime(end)
        stride = timedelta(seconds=int(stride))
        
        if start == end: #Then we only have 1 day of data, stacking won't work later
            date_range_len = 1
        else: 
            date_range_len = 2


        # Create a date iterator.
        cur = copy.copy(start)
        #print start, end

        # Loop through the dates.
        while cur <= end:
            logging.info("Processing " + str(cur))

            # Loop through predictors
            for n,pred in enumerate(formatted_predictors):
                logging.info("Property: "+ str(pred.search_metadata['property']))
                pred.search_metadata['reserved1'] = 'grid'
                pred.search_metadata['file_id'] = file_id
                # Try to fetch the exact variable asked for
                variable = fetch(control.predictor_data_path, Time.epoch_time(cur), **pred.search_metadata)

                # If the call to fetch doesn't find the variable,
                # then see if if it can be calculated.
                if variable is None:
                   variable = create.calculate(control.predictor_data_path, Time.epoch_time(cur), pred, station_list=selected_stations, station_defs=selected_station_defs)
                # Apply procedures set in the predictor.yaml file to the variable.
                # Note: variable is a CAMPS_data object
                #pdb.set_trace()
                variable = procedures.apply_procedures(variable, pred.procedures, xi_x, xi_y)

                # Add leadtime to the camps object
                variable.add_metadata('leadtime', pred.leadTime)

                # Add CAMPS variable object to output array
                # NOTE: computed_vars is a list of predictor lists.  Index of
                # of computed_vars corresponds to one date range iteration. Each
                # containing a list of predictor objects.
                computed_vars[n].append(variable)

            cur += stride
        # Create a list of CAMPS predictor objects
        combined_predictors = []
        logging.info("Adding variables")
        # Stack predictor objects by date range iteration
        for n,i in enumerate(computed_vars):
            temp_pred = i[0] # Initialize temp_pred as first of the predictor ojbects
            for j in range(1,len(i)): # Now loop over computed_vars list (skipping index 0)
                temp_pred += i[j] # Stack objects by date dimension
            # If date range is one day, need to force data shape into 2D
            if date_range_len == 1:
		new_shape = tuple([1, len(temp_pred.data)])
                temp_pred.data = temp_pred.data.reshape(new_shape)

            temp_pred.properties['reserved2'] = leads_list[n%len(leads_list)]
            temp_pred.get_result_time().append_result(None)
            combined_predictors.append(temp_pred)

        # Add time dimension to predictor objects
        time_dim_name = cfg.read_dimensions()['time']
        [x.dimensions.insert(0, time_dim_name) for x in combined_predictors]
        # Check units of predictors against international_units dictionary
        combined_predictors = check_units(combined_predictors)
        # Add lat, lon and station objects to combined predictor object list
        combined_predictors.append(lat_obj)
        combined_predictors.append(lon_obj)
        combined_predictors.append(station_obj)
        # Write list of objects (combined_predictors) to netcdf file
        write(combined_predictors, control.predictor_outfile)


def get_predictands(predictand_file, date_range_list, selected_stations, selected_station_defs, control, lons, lats, lead_times, fcst_ref_time):
    """Puts predictands in fetchable form and fetches.
    """

    #--------------------------------------------------------------------------
    # Update the database
    #--------------------------------------------------------------------------
    # Check to see if the variable table is empty or missing files from the
    # input path provided in the control file. If it is then the function will
    # populate the variable table in the database with the input data provided.
    # Retrieve file ids of each predictand input file.
    file_ids = []
    for FILE in control.predictand_data_path:
        file_ids.append(update(FILE))

    # Get list of desired predictands from predictand_file
    predictand_list = cfg.read_yaml(predictand_file)
    predictands = []
 
    # Loop over date_ranges from control file
    for date_range in date_range_list:

        # Set up time Loop
        start,end,stride = read_pred.parse_range(date_range)
        start_time = Time.str_to_datetime(start)
        end_time = Time.str_to_datetime(end)
        stride_time = timedelta(seconds=int(stride))

            # Loop over desired predictands and lead times and fetch for each desired time
        for entry_dict in predictand_list.predictands:
            if lead_times is None:
                try:
                    leads = [parse_pred.lead_time(lead) for lead in entry_dict.pop('lead_times')]
                except KeyError:
                    logging.error("Either a global list of lead times or a per variable list of lead times must be provided")
                    raise
            else:
                if 'lead_times' in entry_dict.keys():
                    lead_unneeded = entry_dict.pop('lead_times')
                leads = copy.copy(lead_times)
            pred = create.Predictor(entry_dict,fcstRef=fcst_ref_time)
            
            vertical_coordinate = pred.search_metadata.pop('Vertical_Coordinate')
            if 'duration_method' not in pred.search_metadata:
                pred.search_metadata['duration_method'] = None
            pred.search_metadata['vert_coord1'] = parse_pred.vertical_coordinate(vertical_coordinate)['layer1']
            logging.info('entry_dict is:'+str(pred.search_metadata))
            Source = list(pred.search_metadata.pop('Source'))
            source_vars = []
            # Loop over file_ids associated with predictand input files
            for n,file_id in enumerate(file_ids):
                variables = []
                pred.search_metadata['file_id'] = file_id
                pred.search_metadata['Source'] = Source[n]
                for j,L in enumerate(leads):
                    # Adjust start and end time based on desired forecast lead time
                    start_time2 = start_time + timedelta(seconds=int(L*3600))
                    end_time2 = end_time + timedelta(seconds=int(L*3600))
                    times = np.arange(start_time2,end_time2+stride_time,stride_time)
                    pred.leadTime = L
                    # Fetch variable for each desired time
                    vars_arr = fetch_many_dates(control.predictand_data_path, start_time2, end_time2, stride_time, pred.search_metadata)
                    # If vars_arr has any empty values. error out. Will change as predictand creation is added.
                    if None in vars_arr:
                        for i,t in enumerate(times):
                           vars_arr[i] = create.calculate(control.predictand_data_path, Time.epoch_time(t.astype(datetime)), pred, station_list=selected_stations, station_defs=selected_station_defs)
                    
                    variables.append(vars_arr)
                # Combine vars from different lead times into single list
                vars_arr = [var for sub_var in variables for var in sub_var if var is not None]
                if len(vars_arr)==0:
                    logging.error('\nCould not create any data for predictand %02dZ %s from source  %s!',\
                        int(pred.fcst_ref_time),entry_dict['property'],Source[n])
                # Combine vars from different sources into a single list
                source_vars.append(vars_arr)
            if all(all(v.data.data==9999) for var in source_vars for v in var):
                logging.warning("No valid returns for predictand: "+pred.search_metadata['property']+". Not writing out.")
                continue
            else:
                # Process_vars checks pulled station data against station list and then stack each by time
                predictand,stations, latitudes, longitudes = process_vars(selected_stations, source_vars, lats, lons)
            # Set prov_used based on all sources used
            prov_used = predictand.metadata.pop('PROV__Used')
            predictand.metadata['PROV__Used'] = ' '.join(Source)
            filepath = predictand.metadata.pop('filepath')
            predictands.append(predictand)
        if len(predictands) > 0:
            # Check units of predictands against international_units dictionary
            predictands = check_units(predictands)
            # Add lat, lon and station objects to combined predictand object list
            # Station object
            station_names = stations
            station_dim = cfg.read_dimensions()['nstations']
            station_obj = Camps_data('station')
            station_obj.dimensions.append(station_dim)
            dim_name = cfg.read_dimensions()['chars']
            station_obj.dimensions.append(dim_name)
            station_obj.add_metadata("fill_value", '_')
            max_char = np.max([len(s) for s in station_names])
            for n,s in enumerate(station_names):
                if len(s)< max_char:
                     s = s+' '*(max_char-len(s))
                char_arr = np.array(list(s), 'c')
                if n == 0:
                    station_name_arr = char_arr
                else:
                    station_name_arr = np.vstack((station_name_arr, char_arr))
            station_obj.add_data(station_name_arr)
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
        else:
            logging.error('\n\nNO predictand data created for date range and stride: %s!!!!\n',date_range)
        #write list of predictands to netcdf file
    if len(predictands) > 0:
        write(predictands, control.predictand_outfile)
    else:
        logging.error('\n\n\nNO PREDICTANDS CREATED AT ALL!!!!\n\n')


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
            intersected_stations = functools.reduce(np.intersect1d, all_stations)
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
            if len(var.data)==len(indices2):
                var.data = var.data[indices2][uniq_ind]
            elif len(var.data)==len(indices):
                var.data = var.data[indices][uniq_ind]
            if i==0:
                stacked_data = var
                phenom_times.append(var.get_phenom_time().data[0])
            else:
                if var.get_phenom_time().data[0] in phenom_times:
                    continue
                else:
                    stacked_data += var
                    phenom_times.append(var.get_phenom_time().data[0])
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
        out_vars.append(stacked_data)
    if len(out_vars)==1:
        out_var = out_vars[0]
    elif len(out_vars)>1:
        out_var = combine_source(out_vars)
    stations = np.array(selected_stations)[latlon_indices]
    lats = np.array(lats)[latlon_indices]
    lons = np.array(lons)[latlon_indices]
    return (out_var,stations, lats, lons)


def combine_source(in_vars):
    """For a variable with multiple sources:
    combine data objects into single object.
    """
    out_var = in_vars[0]
    for n in range(1,len(in_vars)):
        out_var.data = np.concatenate((out_var.data,in_vars[n].data),axis=1)
        [out_var.add_process(proc.name) for proc in in_vars[n].processes if proc.name not in out_var.get_process_str()]

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
    # Loop through all predictands, comparing the units for a given variable
    # to the units in the international units dictionary. If the units do not
    # match, convert to the international units.
    for p in pred:
        p_name = p.get_observedProperty()
        try:
           p_units = p.units
        except:
           logging.error("pred, "+p_name+", does not contain units")
           raise
        try:
            name = [n for n in international_units if n in p_name][0]
            int_units = international_units[name]
        except:
            logging.warning("pred, "+p_name+", not found in unit standards. Leaving units as is.")
            continue
        if p_units != int_units:
            logging.info("pred units, "+p_units+", do not match unit standards, "+int_units+". Converting.")
            p.data[:] = convert_units(p.data,p_name,p_units,int_units,Q)
            p.units = int_units
            p.metadata['units'] = int_units
            if hasattr(p,'valid_max'):
                p.valid_max = float(convert_units(p.valid_max,p_name,p_units,int_units,Q))
                p.metadata['valid_max'] = p.valid_max
            if hasattr(p,'valid_min'):
                p.valid_min = float(convert_units(p.valid_min,p_name,p_units,int_units,Q))
                p.metadata['valid_min'] = p.valid_min

    return pred

def convert_units(data,name,in_unit,out_unit,Q):
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

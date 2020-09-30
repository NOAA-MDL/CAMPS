import os
import sys
import re
import pdb
import metpy.calc as calc
from metpy.units import units
import math
import numpy as np
import operator
import uuid
import logging

from netCDF4 import Dataset
from ..registry import util as cfg
from ..mospred import read_pred as read_pred
from ..core import util as util
from . import Time as Time
from . import writer as writer
from .fetch import *
from .Camps_data import Camps_data



"""Module: equations.py

Methods:
    write_globals
    create_dimensions
    write_ancillary_variables
    write_data
    write_stations
    get_max_parameters
    write_equations
"""



def write_globals(nc, control, primary_vars, file_id):
    """Write global attributes from the control file and args.
    """
    # Create dictionary of global attributes
    global_dict = {}
    global_dict['PROV__Entity'] = "StatPP__Data/Source/MOSEqnFile"
    global_dict['PROV__wasGeneratedBy'] = "StatPP__Methods/Stat/MOSDev"
    global_dict['file_id'] = file_id
    global_dict['primary_variables'] = primary_vars
    # Get season from control file
    season = control['forecast_season']
    global_dict['season'] = season
    # Determine season start and end dates and forecast cycle
    start,end,stride = read_pred.parse_range(control.date_range[0])
    seasBegin = start[4:8]
    seasEnd = end[4:8]
    fcst_cycle = start[-2:]
    global_dict['StatPPTime__SeasBeginDay'] = seasBegin
    global_dict['StatPPTime__SeasEndDay'] = seasEnd
    global_dict['StatPPTime__SeasDayFmt'] = 'StatPP__Data/Time/SeasDayFmt/MMDD'
    global_dict['StatPPTime__FcstCyc'] = fcst_cycle
    global_dict['StatPPTime__FcstCycFmt'] = 'StatPP__Data/Time/FcstCycFmt/HH'
    # Get status (and role, if needed) from control file
    status = control['status']
    if status.lower() == 'developmental':
        status_uri = 'StatPP__Methods/System/Status/Dev'
    elif status.lower() == 'experimental':
        status_uri = 'StatPP__Methods/System/Status/Exp'
    elif status.lower() == 'operational':
        status_uri = 'StatPP__Methods/System/Status/Opnl'
        role = control['role']
        role_uri = 'StatPP__Methods/System/Role/'+role.title()
    elif status.lower() == 'prototype':
        status_uri = 'StatPP__Methods/System/Status/Proto'
    try:
        global_dict['StatPPSystem__Status'] = status_uri
    except:
        pass
    try:
        global_dict['StatPPSystem__Role'] = role_uri
    except:
        pass
    # Gather additional global attributes
    nc_globals = cfg.read_globals()
    for name,value in nc_globals.items():
        if name == 'organization':
            name = 'PROV__wasAttributedTo'
            value = "StatPP__Data/Source/MDL"
        if value:
            global_dict[name] = value
    for name, value in global_dict.items():
        setattr(nc, name, value)


def create_dimensions(nc, control, num_stations, num_char_predictor, num_char_predictand, n_outputs, max_inputs, max_params):
    """Create Dimensions for dataset."""

    nc.createDimension('number_of_stations',num_stations)
    nc.createDimension('number_of_predictands',n_outputs)
    nc.createDimension('max_eq_terms',max_inputs+1)
    nc.createDimension('num_char_predictors',num_char_predictor)
    nc.createDimension('num_char_predictands',num_char_predictand)


def write_process_variables(nc, proc_vars):
    """Write the process ancillary Variables
    which help describe the dataset.
    """

    for proc in proc_vars:
        proc_var = nc.createVariable(proc,int)
        proc_def = cfg.read_procedures()[proc]
        for name, value in proc_def.items():
            if name == 'process_step':
                name = 'PROV__Activity'
            setattr(proc_var,name,value)


def write_data(nc, control, equations, nparams=5):
    """Writes station forecast equations into the netCDF file."""
    num_stations = len(equations)

    #Write stations/groups
    write_stations(nc, equations)

    #Next three lines unnecessary for now as all predictands and all predictors will be output (unused predictors have value of 0)
    #num_in = nc.createVariable("output_indices", int, ('number_of_stations','lead_time','number_of_oredictands'))
    #num_in = nc.createVariable("input_indices", int, ('number_of_stations','lead_time','number_of_predictands'))
    #inp_in = nc.createVariable("number_of_inputs_used", int, ('number_of_stations', 'lead_time','max_predictors','number_of_outputs'))

    proc_vars = ['PolyLinReg', 'Mean']
    write_process_variables(nc,proc_vars)

    #Format coefficients
    coefs = [np.array(x['coefs']) for x in equations]
    coefs = np.array(coefs)
    # Create variables for MOS equation parameters
    pred_coef = nc.createVariable("MOS_Predictor_Coeffs", int,())
    setattr(pred_coef, 'standard_name', 'source')
    setattr(pred_coef, 'long_name', 'MOS Predictor Coefficients')
    setattr(pred_coef, 'PROV__Entity', 'StatPP__Methods/Stat/MOS/OutptParams/MOSEqnCoef')
    setattr(pred_coef, 'SOSA__usedProcedure', '( PolyLinReg )')

    SEE = nc.createVariable("Standard_Error_Estimate", 'f4', ('number_of_stations','number_of_predictands'))
    setattr(SEE, 'PROV__Entity', 'StatPP__Methods/Stat/MOS/OutptParams/MOSStdErrEst')
    setattr(SEE, 'standard_name', 'source')
    setattr(SEE, 'long_name', 'MOS Standard Error Estimate')
    setattr(SEE, 'coordinates', "station Predictand_List")
    setattr(SEE, 'SOSA__usedProcedure', '( PolyLinReg )')
    setattr(SEE, 'units', 1)

    RoV = nc.createVariable("Reduction_of_Variance", 'f4', ('number_of_stations','number_of_predictands'))
    setattr(RoV, 'PROV__Entity', 'StatPP__Methods/Stat/MOS/OutptParams/MOSRedOfVar')
    setattr(RoV, 'standard_name', 'source')
    setattr(RoV, 'long_name', 'MOS Reduction of Variance')
    setattr(RoV, 'coordinates', "station Predictand_List")
    setattr(RoV, 'SOSA__usedProcedure', '( PolyLinReg )')
    setattr(RoV, 'units', 1)

    EqCo = nc.createVariable("Equation_Constant", int, ())
    setattr(EqCo, 'PROV__Entity', 'StatPP__Methods/Stat/MOS/OutptParams/MOSEqnConst')
    setattr(EqCo, 'standard_name', 'source')
    setattr(EqCo, 'long_name', 'MOS Equation Constant')
    setattr(EqCo, 'SOSA__usedProcedure', '( PolyLinReg )')


    MCC = nc.createVariable("Multiple_Correlation_Coefficient", 'f4', ('number_of_stations','number_of_predictands'))
    setattr(MCC, 'PROV__Entity', 'StatPP__Methods/Stat/MOS/OutptParams/MOSMultiCorCoef')
    setattr(MCC, 'standard_name', 'source')
    setattr(MCC, 'long_name', 'MOS Multiple Correlation Coefficient')
    setattr(MCC, 'coordinates', "station Predictand_List")
    setattr(MCC, 'SOSA__usedProcedure', '( PolyLinReg )')
    setattr(MCC, 'units', 1)

    Pred_avg = nc.createVariable("Predictand_Average", 'f4', ('number_of_stations','number_of_predictands'))
    setattr(Pred_avg, 'PROV__Entity', 'StatPP__Methods/MOS/Arith/Mean')
    setattr(Pred_avg, 'standard_name', 'source')
    setattr(Pred_avg, 'long_name', 'Predictand Average')
    setattr(Pred_avg, 'coordinates', "station Predictand_List")
    setattr(Pred_avg, 'SOSA__usedProcedure', '( Mean )')
    setattr(Pred_avg, 'units', 1)

    MOS_eq = nc.createVariable("MOS_Equations", 'f4', ('number_of_stations','max_eq_terms','number_of_predictands'))
    setattr(MOS_eq, 'PROV__Entity', 'StatPP__Methods/Stat/MOS/MOSEqn')
    setattr(MOS_eq, 'standard_name', 'source')
    setattr(MOS_eq, 'long_name','MOS Equation Coefficients and Constants')
    setattr(MOS_eq, 'coordinates', "station Equations_List Predictand_List")
    setattr(MOS_eq, 'SOSA__usedProcedure', '( PolyLinReg )')
    setattr(MOS_eq, 'ancillary_variables', '( MOS_Predictor_Coeffs Equation_Constant )')
    setattr(MOS_eq, 'units', 1)

    ancils = [np.array(list(x['ancil'].values())) for x in equations]
    shape = (nparams,nc.dimensions['number_of_predictands'].size)
    for n,a in enumerate(ancils):
        if a.shape != shape:
            ancils[n] = np.zeros(shape)
            logging.info("Not enough ancils. Adding")

    ancils = np.dstack(ancils)
    MOS_eq[:,0:-1,:] = coefs
    MOS_eq[:,-1,:] = ancils[0,:,:].T

    SEE[:] = ancils[2,:,:].T
    RoV[:] = ancils[3,:,:].T
    MCC[:] = ancils[1,:,:].T
    Pred_avg[:] = ancils[4,:,:].T

    #Create prefix list
    prefixes =  { "OM__" : "http://opengeospatial.org/standards/om/",
            "PROV__" : "http://www.w3.org/ns/prov/#",
            "StatPP__" : "http://codes.nws.noaa.gov/StatPP/",
            "OM2__" : "http://codes.nws.noaa.gov/StatPP/",
            "StatPPTime__" : "http://codes.nws.noaa.gov/StatPP/Data/Time/",
            "StatPPSystem__" : "http://codes.nws.noaa.gov/StatPP/Methods/System/",
            "SOSA__" : "http://www.w3.org/ns/sosa/"
            }
    group = nc.createGroup('prefix_list')
    for name,value in prefixes.items():
        setattr(group, name, value)

    return ancils, coefs


def write_stations(nc, equations):
    """Write stations."""

    # Determine if stations are groups
    max_stations = 1
    stations = [x['stations'] for x in equations]
    for station in stations:
        if len(station) > 1:
        # Handle writing groups here
            logging.info("writing station groups")

    writer.write_stations(nc,[x[0] for x in stations])


def get_max_parameters(equations):
    """Get the number of output statistics. They should be uniform accross stations."""

    return len(equations[0]['ancil'])


def write_equations(filename, control, predictors, predictands, equations):
    """Write eqation information to a netCDF4 file."""

    #Initializes dataset. Overwrites if filename already exists
    full_filename = control.output_directory+filename
    logging.info("Attempting to write to " + str(full_filename))
    nc = Dataset(full_filename, 'w')
    file_id = str(uuid.uuid4())
    # Write global attributes
    primary_variables = "MOS_Equations Standard_Error_Estimate Reduction_of_Variance Multiple_Correlation_Coefficient Predictand_Average"
    write_globals(nc, control, primary_variables, file_id)

    # Establish dimensions
    max_params = get_max_parameters(equations)
    max_char_predictor = np.max([len(x.get_variable_name()) for x in predictors])
    max_char_predictand = np.max([len(x.get_variable_name()) for x in predictands])
    create_dimensions(nc, control,len(equations), max_char_predictor, max_char_predictand, len(predictands), len(predictors), max_params)

    # Write equations ordered lists and metadata of predictor variables (no data or dimensions).
    predictor_var = nc.createVariable('Equations_List', 'c', ('max_eq_terms','num_char_predictors'))
    for n,predictor in enumerate(predictors):
        name_len = len(predictor.get_variable_name())
        entry_name = predictor.get_variable_name()+' '*(max_char_predictor-name_len)
        counter = 0
        while entry_name in predictor_var[:].data.view('S'+str(max_char_predictor)):
            counter += 1
            entry_name = predictor.get_variable_name()+str(counter)+' '*(max_char_predictor-name_len-len(str(counter)))
        predictor_var[n] = entry_name
        predictor.data = None #remove data
        predictor.dimensions = [] #remove data dimensions
        filepath = predictor.metadata.pop('filepath')
        var = predictor.write_to_nc(nc)
        nc.variables[var].coordinates += ' station'
    predictor_var[-1] = "Equation_Constant"+' '*(max_char_predictor-len("Equation_Constant"))
    pred_list = predictor_var[:-1]
    setattr(predictor_var,'PROV__Entity','StatPP__Methods/Stat/OrdrdInpt')
    setattr(predictor_var,'long_name','Ordered List of Equation Terms')

    # Write ordered predictand list for equations and associated metadata
    predictand_var = nc.createVariable('Predictand_List', 'c', ('number_of_predictands','num_char_predictands'))
    for n,predictand in enumerate(predictands):
        predictand.data = None
        predictand.dimensions = []
        filepath = predictand.metadata.pop('filepath')
        var = predictand.write_to_nc(nc)
        nc.variables[var].coordinates += ' station'
        tand_name = predictand.get_variable_name()
        name_len = len(tand_name)
        entry_name = tand_name+' '*(max_char_predictand-name_len)
        counter = 0
        while entry_name in predictand_var[:].data.view('S'+str(max_char_predictand)):
            counter +=1
            entry_name = tand_name+str(counter)+' '*(max_char_predictand-name_len-len(str(counter)))
        predictand_var[n] = entry_name
    tand_list = predictand_var[:]
    setattr(predictand_var,'PROV__Entity', 'StatPP__Methods/Stat/OrdrdOutpt')
    setattr(predictand_var,'long_name','Ordered List of Predictand Outputs')

    # Writes equation coefficients, constants, and regression parameters and any other ancillary variables
    ancils, coefs = write_data(nc, control, equations)
    T = datetime.now().strftime("%Y-%m-%dT%H:00:00")
    setattr(nc,'PROV__generatedAtTime',T)
    logging.info('Wrote to '+ full_filename)

    nc.close()
    if control.equations_summary is not None:
        logging.info("Writing equations summary to "+control.output_directory+control.equations_summary)
        util.equations_summary(stations=[x['stations'] for x in equations],coefficients=coefs,predictors=pred_list,predictands=tand_list,outname=control.output_directory+control.equations_summary,variance=ancils[3,:,:].T,error=ancils[2,:,:].T, consts=ancils[0,:,:].T, averages=ancils[4,:,:].T)

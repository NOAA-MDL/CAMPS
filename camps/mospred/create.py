import os
import sys
from os.path import basename
import pdb
import copy

from ..core.fetch import fetch
from ..core.Camps_data import Camps_data as Camps_data
from . import computations
#from ..libraries.mathlib import miscellaneous
from ..libraries.mathlib import mass
from ..libraries.mathlib import momentum
from ..libraries.mathlib import stability
from ..libraries.mathlib import temperature
from ..libraries.mathlib import moisture
from . import read_pred


"""Module: create.py
Creates a predictor object, which essentially contains
information necessary for finding or creating its data.

Methods:
    is_valid_property
    get_met_function
    get_common_function
    calculate
    calc_with_multiple_vertical_layers

Classes:
    Predictor
"""


#Dictionary of functions that create predictors whose names
#are encoded in the keys and the corresponding function in
#the value.
creation_functions = {
        'Ozone' : None,
        #'DOY' : miscellaneous.DOY,
        'CilgHght' : None,
        'CilgHghtProb' : None,
        'CldAmt' : None,
        'CldHght' : None,
        'SkyCover' : None,
        'SunDuratn' : None,
        'GeoHght' : None,
        'Pres' : None,
        'PLThick' : mass.thickness,
        'TLapse' : temperature.temp_lapse_setup,
        'Albedo' : None,
        'LandSea' : None,
        'Terrain' : None,
        'Veg' : None,
        'MixR' : moisture.mixing_ratio_setup,
        'MoistDiv' : None,
        'PWat' : None,
        'RelHum' : None,
        'SpecHum' : None,
        'WatEquAccSN' : None,
        'TotSNRate' : None,
        'ThetaEAdv' : None,
        'ThetaEDiff' : None,
        'VolSoilMoist' : None,
#        'AbsVort' : momentum.vorticity_setup,
        'BlkShear' : None,
        'CondGust' : None,
        'GeoRelVort' : None,
        'GeoWsp' : None,
        'Gust' : None,
        'InflWind' : None,
        'WChill' : momentum.WindChill_setup,
        'PBLMixHi' : None,
#        'RelVort' : momentum.RelativeVorticity_setup,
        'ThetaEUwindProd' : None,
        'ThetaEVwindProd' : None,
        'Upslope' : None,
        'Uwind' : None,
        'Vwind' : None,
        'WindDir' : None,
        'WindSpd' : momentum.wind_speed_setup,
        'WSpdRatio' : None,
        'Wwind' : None,
        'CAPE' : stability.cape_setup,
        'CIN' : stability.cin_setup,
        'ConvProb' : None,
        'HtIndex' : moisture.heat_index_setup,
        'KIdxCnvRFProd' : None,
        'KIdxTstmRFProd' : None,
        'KIndex' : stability.KIndex_setup,
        'LtngFlsh' : None,
        'LI' : None,
        'LIBest4Lyr' : None,
        'LtngMRFKIProd' : None,
        'MoistDivVVProd' : None,
        'RHVVProd' : None,
        'Sweat' : None,
        'SweatCondSvrWxRFProd' : None,
        'SweatSvrRFProd' : None,
        'Threat' : None,
        'TstormProb' : None,
        'TotTots' : None,
        'VVKIProd' : None,
        'VVPWatProd' : None,
        'DewPt' : moisture.dewpoint_temperature_setup,
        'EquPotTemp' : moisture.equivalent_potential_temperature_setup,
        'LapRate' : None,
        'PotTemp' : temperature.potential_temperature_setup,
        'SoilTemp' : None,
        'Temp' : None,
        'DayMaxT' : temperature.extreme_temperature_setup,
        'NightMinT' : temperature.extreme_temperature_setup,
        'TempAdv' : temperature.temp_advection_setup,
        'VirPotTemp' : None,
        'WbPotTemp' : None,
        'WbTemp' : None,
        '2-hCnvPrbCnvRFProd' : None,
        '2-hCnvPrbTopoProd' : None,
        'AvgRadRefl' : None,
        'ConvSnow' : None,
        'CPrecip' : None,
        'FZRABin' : None,
        'IFRCond' : None,
        'IPBin' : None,
        'LIFRCond' : None,
        'LMPFrozPred' : None,
        'LMPPtypePred' : None,
        'MaxCompRadRefl' : None,
        'MOSPtypePred' : None,
        'MOSZRPred' : None,
        'MRF.10"PRISMpaTotQPFProd' : None,
        'MRF.10"TotQPFProd' : None,
        'MRF.25"TotQPFProd' : None,
        'MRF.50"CnvQPFProd' : None,
        'MRFSRF.10"TotQPFProd' : None,
        'MRFSRF.50"CnvQPFProd' : None,
        'MVFRCond' : None,
        'NCPrecip' : None,
        'ObsVision' : None,
        'OpqSky' : None,
        'POP' : None,
        'POPOccur' : None,
        'PQPF' : None,
        'PrbFZPOPOccurProd' : None,
        'PrbSNPOPOccurProd' : None,
        'PrbSNPrbFZProd' : None,
        'PrbSNPrbRProd' : None,
        'PrecipChar' : None,
        'PrecipOccur' : None,
        'PredWx' : None,
        'PType' : None,
        'RadRefl' : None,
        'RNBin' : None,
        'SNBin' : None,
        'SRF.10"TotQPFProd' : None,
        'SRF.25"TotQPFProd' : None,
        'SRF.50"TotQPFProd' : None,
        'SRF.75"TotQPFProd' : None,
        'TotalPrecip' : moisture.TotalPrecip,
        'TVVAvgRHProd' : None,
        'TVVTotQPFProd' : None,
        'VFRCond' : None,
        'FlightCats' : None,
        'Hel' : None,
        'SRH' : None,
        'PBL' : None,
        'AltimtrStg' : None,
        'Vsby' : None
        }

#Functions that basically perform common math
#and statistical operations.
common_functions = {
     'mean' : computations.mean,
     'difference' : computations.difference,
     'sum' : computations.sum,
     'point' : None, # What is this?
     'maximum' : computations.max,
     'minimum' : computations.min,
     'mid_range' : None,
     'standard_deviation' : None,
     'variance' : None,
     'mult' : None
    }


def is_valid_property(observedProperty):
    """Determine if property is in the function dictionary"""

    return basename(observedProperty) in creation_functions


def get_met_function(observedProperty):
    """Returns function associated with a particular weather element"""

    if observedProperty in creation_functions:
        return creation_functions[observedProperty]
    error = "Property: " + observedProperty + " not in creation functions."
    raise ValueError(error)
    return None


def get_common_function(method):
    """Returns function name for common math or stat operation
    indicated by method
    """

    return common_functions[method]


def calculate(filepaths, time, predictor, station_list=None, station_defs=None):
    """Given an internal Predictor object, create the camps data object
    associated with the observed property containing its data and metadata.

    Arguments:
        filepaths (list): paths to input data files
        time (int): epoch time of interest in seconds, usually phenomenon time.
        predictor (dictionary): key/value pairs provide information to calculate predictor.
        station_list (list): list of call letters of stations selected for the predictor.
        station_defs (dictionary): information about each station in station_list.

    Returns:
        ret_obj (Camps_data): object containing calculated data and metadata of the
            specified predictor.
    """

    #Exit if observed property is not valid.
    observed_property = os.path.basename(predictor['property'])
    if not is_valid_property(observed_property):
        err_str = "There is no function associated with the calculation of "
        err_str += observed_property
        err_str += "\nCheck create.py for function definitions"
        raise RuntimeError(err_str)
    #Fork the creation process between single vertical layer predictors
    #and multi-level ones.
    if has_multiple_vertical_layers(predictor):
        #Get vertical method
        vert_method = predictor.search_metadata['vert_method']
        #Check if vert_method is in common_functions
        if vert_method in common_functions:
            ret_obj = calc_with_multiple_vertical_layers(filepaths, time, predictor)
        #If no vert_method, then see if observed_property is in creation_functions
        elif observed_property in creation_functions:
            variable_calculation_function = get_met_function(observed_property)
            ret_obj = variable_calculation_function(filepaths, time, predictor)
    else: #single level predictors, some of which require station information
        variable_calculation_function = get_met_function(observed_property)
        if 'station_list' in variable_calculation_function.__code__.co_varnames and \
           'station_defs' in variable_calculation_function.__code__.co_varnames:
            ret_obj = variable_calculation_function(filepaths, time, predictor, station_list=station_list, station_defs=station_defs) #Pass station information
        else:
            ret_obj = variable_calculation_function(filepaths, time, predictor) # Pass standard information

    #Add source to metadata if it is not in there.
    if isinstance(ret_obj,Camps_data):
        processes = []
        for process in ret_obj.processes:
            processes.append(process.name)
            if 'Calc' in process.name:
                process.add_attribute('source', predictor.search_metadata['source'])
        #if 'Calculated' not in processes:
        #    ret_obj.add_process('Calculated')
        #    for index,proc in enumerate(ret_obj.processes):
        #        if 'Calculate' in proc.name:
        #            break
        #    calc = ret_obj.processes[index]
        #    calc.add_attribute('source', predictor.search_metadata['source'])

    return ret_obj


def calc_with_multiple_vertical_layers(filepaths, time, predictor):
    """Calculate predictor that has multiple vert_coords"""
    # Get the vertical method, e.g. diff, avg, etc.
    vert_method = predictor.search_metadata['vert_method']
    # First, create individual predictors for each layer
    lower_layer_pred = predictor.copy()
    upper_layer_pred = predictor.copy()
    # Change to only have 1 vert_coord
    upper_layer_pred.search_metadata['vert_coord1'] = predictor.search_metadata['vert_coord2']
    # Remove second bound and vertical method
    lower_layer_pred.search_metadata.pop('vert_method')
    upper_layer_pred.search_metadata.pop('vert_method')
    lower_layer_pred.search_metadata.pop('vert_coord2')
    upper_layer_pred.search_metadata.pop('vert_coord2')
    # Remove method since there's now only 1 vertical layer

    # Check if the (single layer) variables already exist
    variable_layer1 = fetch(filepaths, time, **lower_layer_pred.search_metadata)
    variable_layer2 = fetch(filepaths, time, **upper_layer_pred.search_metadata)

    if variable_layer1 is None or variable_layer2 is None:
        observed_property = os.path.basename(predictor['property'])
        variable_calculation_function = get_met_function(observed_property)
        variable_layer1 = variable_calculation_function(filepaths, time, lower_layer_pred)
        variable_layer2 = variable_calculation_function(filepaths, time, upper_layer_pred)
        assert variable_layer1 is not None
        assert variable_layer2 is not None

    vert_calc_function = get_common_function(vert_method)
    new_data = vert_calc_function(variable_layer1.data, variable_layer2.data)

    # Create Camps_data with new data
    variable_layer1.properties['vert_coord1'] = predictor.search_metadata['vert_coord1']
    variable_layer1.properties['vert_coord2'] = predictor.search_metadata['vert_coord2']
    variable_layer1.metadata['coordinates'] = 'plev'
    variable_layer1.data = new_data

    return variable_layer1


def has_multiple_vertical_layers(predictor):
    """Returns True if Predictor object has more than one vertical layer."""

    return 'vert_coord2' in predictor.search_metadata


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


"""Class: Predictor
This is a simple class for objects that hold the necessary information
to define a predictor.

Methods:
    __init__
    copy
    change_property
    __getitem__
    __str__
"""


class Predictor:

    def __init__(self, searchable_dict, procedures=None, leadTime=None, fcstRef=None):
        """The attributes of a Predictor object are the dictionary search_metadata that
        is used to get the predictor's data, a list of procedures to perform on the predictor,
        the integer lead time of the predictor in seconds, and the integer model cycle time given
        as the hour of the day in seconds.
        """

        self.search_metadata = searchable_dict
        self.procedures = procedures
        self.leadTime = leadTime
        self.fcst_ref_time = fcstRef


    def copy(self):
        """Deep copy of the Predictor object"""

        return copy.deepcopy(self)


    def change_property(self, observed_property):
        """Changes the value of the search_metadata key 'property'"""

        self.search_metadata['property'] = observed_property


    def __getitem__(self, item):
        """Get the value of the key 'item' in the search_metadata dictionary"""

        return self.search_metadata[item]


    def __str__(self):
        """Format for printing out a predictor object"""

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

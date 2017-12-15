import os
import sys
from os.path import basename
file_dir = os.path.dirname(os.path.realpath(__file__))
relative_path = "/.."
path = os.path.abspath(file_dir + relative_path)
sys.path.insert(0, path)
import thickness
import computations
import wind_speed


creation_functions = {
        'Ozone' : None,
        'CilgHght' : None,
        'CilgHghtProb' : None,
        'CldAmt' : None,
        'CldHght' : None,
        'SkyCover' : None,
        'SunDuratn' : None,
        'GeoHght' : None, 
        'Pres' : None,
        'Albedo' : None,
        'DOY' : None,
        'LandSea' : None,
        'Terrain' : None,
        'Veg' : None,
        'MixR' : None,
        'MoistDiv' : None,
        'PWat' : None,
        'RelHum' : None,
        'SpecHum' : None,
        'WatEquAccSN' : None,
        'TotSNRate' : None,
        'ThetaEAdv' : None,
        'ThetaEDiff' : None,
        'VolSoilMoist' : None,
        'AbsVort' : None,
        'BlkShear' : None,
        'CondGust' : None,
        'GeoRelVort' : None,
        'GeoWsp' : None,
        'Gust' : None,
        'InflWind' : None,
        'PBLMixHi' : None,
        'RelVort' : None,
        'ThetaEUwindProd' : None,
        'ThetaEVwindProd' : None,
        'Upslope' : None,
        'Uwind' : None,
        'Vwind' : None,
        'WindDir' : None,
        'WSpd' : wind_speed.WSpd_setup,
        'WSpdRatio' : None,
        'Wwind' : None,
        'CAPE' : None,
        'CIN' : None,
        'ConvProb' : None,
        'KIdxCnvRFProd' : None,
        'KIdxTstmRFProd' : None,
        'KIndex' : None,
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
        'DewPt' : None,
        'EquPotTemp' : None,
        'LapRate' : None,
        'PotTemp' : None,
        'SoilTemp' : None,
        'Temp' : None,
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
        'TotalPrecip' : None,
        'TVVAvgRHProd' : None,
        'TVVTotQPFProd' : None,
        'VFRCond' : None,
        'WxGroup' : None,
        'M2KCodedWxGroup1' : None,
        'M2KCodedWxGroup2' : None,
        'M2KCodedWxGroup3' : None,
        'FlightCats' : None,
        'Hel' : None,
        'SRH' : None,
        'PBL' : None,
        'AltimtrStg' : None,
        'WvPd' : None,
        'DomWvPd' : None,
        'WvHght' : None,
        'WvDir' : None,
        'Vsby' : None
        }

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
    """
    """
    return basename(observedProperty) in creation_functions

def get_met_function(observedProperty):
    """Returns function associated with a particular weather element
    """
    # First, check if it's a arithmetic function on 2 layers
    if observedProperty in creation_functions:
        return creation_functions[observedProperty]
    return None

def get_common_function(method):
    return common_functions[method]




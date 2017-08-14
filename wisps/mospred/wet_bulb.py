import os
import sys
import re
import pdb
relative_path = os.path.abspath(
    os.path.dirname(os.path.realpath(__file__)) + "/..")
sys.path.insert(0, relative_path)
from data_mgmt.fetch import *

#import metpy.constants as const
import data_mgmt.constants as const
import metpy.calc as calc
from metpy.units import units

def wet_bulb_setup(mixrat_obj):
    """Compute gridded mixing ratio using 
    pressure, temperature, and relative humidity (%) 
    on an isobaric, a constant height, or a sigma surface.
    """
    level = mixrat_obj.get_coordinate()
    if level != 2 or level is not None:
        raise ValueError("level is not surface or 2m")
    # Get temperature, relative humidity, and pressure
    temp = fetch(property='Temp', source='GFS', vert_coord1=level)
    pres = fetch(property='Pres', source='GFS', vert_coord1=None)
    rel_hum = fetch(property='RelHum', source='GFS', vert_coord1=level)
    
    # Package into quantity
    q_temp = units('K') * temp.data
    q_pres = units('Pa') * pres.data
    q_rel_hum = units(None) * rel_hum.data # Dimensionless

    data = mixing_ratio(q_temp, q_pres, q_relum)
    mixrat_obj.data = data
    return mixrat_obj



    # # # mixrat.f interpretted # # # 
    #
    # Initialize variables 
    # 
    # Determine if isobaric, constant height, or sigma surface
    # 
    # if isobaric. 
    #   Looks at mosid, and gets the upper level pressure.
    #   fills pressure 1-d array with that pressure. 
    # else 
    #   if sigma or 2 m height
    #      divides upper level by 1000 
    #      fetches pressure
    # 
     

def wet_bulb(pressure_arr, temperature_arr, rel_hum_arr):
    """Compute the mixing ratio
    """
    #epsilon = const.ratio_of_dry_and_saturated_gas_constant
    #psat = const.saturated_pressure_at_triple_point
    #saturation_vapor_pressure = calc.saturation_vapor_pressure

    sat_mix_ratio = calc.saturation_mixing_ratio(pressure_arr, temperature_arr)
    mixing_ratio = sat_mix_ratio * rel_hum_arr
    return mixing_ratio
    


    
       DO 500 I=1,NX*NY
 C
          IF(FD1(I).NE.9999..AND.FD2(I).NE.9999..AND.FD3(I).NE.9999.)THEN
 C
 C              USE TETEN-STACKPOLE APPROXIMATION (JAM, VOL 6, P. 465) TO
 C              COMPUTE SATURATION VAPOR PRESSURE FROM TEMPERATURE
 C
             FDTC=FD2(I)+ABSZRO
             FDSVP=PSAT*EXP(17.269*FDTC/(237.3+FDTC))
 C
 C              COMPUTE SATURATION MIXING RATIO FROM THE SATURATION VAPOR
 C              PRESSURE BY AN ALGEBRAIC EXPRESSION (BEYERS EQN 8-11).
 C              CONVERT PRESSURE TO HECTOPASCAL IF NECESSARY
 C
             IF(ISO.EQ.1.OR.IDPARS(4).EQ.6)THEN
 C                 PRESSURE IS ALREADY IN HPA BECAUSE (1) THIS IS AN
 C                 ISOBARIC SURFACE OR (2) THIS IS PRESSURE DATA FROM THE
 C                 NGM MODEL
                FDAPH=FD1(I)
             ELSE
 C                 PRESSURE MUST BE CONVERTED FROM PA TO HPA
                FDAPH=FD1(I)/100.
             END IF
 C
             FDSMR=EPSILN*FDSVP/(FDAPH-FDSVP)
 C
 C              COMPUTE MIXING RATIO FROM THE RELATIVE HUMIDITY AND THE
 C              SATURATION MIXING RATIO (BEYERS EQN 8-13)
 C
             FDMR(I)=FDSMR*FD3(I)/100.
          ELSE
 C              FILL IN THE MIXING RATIO ARRAY WITH MISSING VALUES.
             FDMR(I)=9999.
          END IF
 C
  500  CONTINUE


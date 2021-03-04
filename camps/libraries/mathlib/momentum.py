r"""Module momentum creates and manipulates predictors involving
the movement of atmosphereic gases.

"""
import logging
import os
import sys
import re
import pdb
import copy
import metpy.calc as calc
from metpy.units import units
import math
import numpy as np
import operator

from ...mospred import create as create
from ...mospred import parse_pred as parse_pred
from ...core.Time import epoch_to_datetime
from ...core import Time as Time
from ...core.Camps_data import Camps_data
from ...core.reader import read_var
from ...registry import constants as const



def wind_speed_setup(filepaths, time, predictor):
    """This method prepares relevant parameters for the calculation of
        horizontal wind speed at a specified vertical level.

    Args:
        control(instance): contains mospred_control.yaml file variables.
        time (int): The number of seconds since January 1, 1970 00Z.
        predictor (Predictor): a container that holds key/value pairs
            used for retrieving variables.  A hard copy is modified within this method to
            fetch components of the wind speed.

    Returns:
        wspd (Camps_data): A Camps data object containing the wind speed.

    """

#   Instantiate the camps data object for wind speed
    wspd = Camps_data('wind_speed_instant')
    international_units = { 'speed' : 'm/s' } #A future global dictionary

#   Get the international units for speed, which is the unit for wind speed.
#   It is also the standard for the u- and v-components of horizontal wind.
#   Construct a metpy object carrying the international unit to be used
#   for dimensionality tests below.
    iu_unit = international_units.get('speed')
    iu_pint = units.Quantity(1., iu_unit)

#   Obtain the wind speed unit specified in netcdf.yaml, determine if it
#   exists, and, if so, test its dimensionality.
    unit = None
    try:
        unit = wspd.metadata['units']
        q_pint = units.Quantity(1., unit)
        assert(q_pint.dimensionality == iu_pint.dimensionality),"Wind speed units given in the metadata have the wrong dimensionality."
    except KeyError:
        logging.info("metadata key \'units\' does not exist or has no value within netcdf metadata.")
        logging.info("Adopt the units of the fetched wind components.")

#   Now set up for fetching the u- and v-components of the horizontal wind
#   from which we calculate the wind speed.
#   Make a hard copy of the predictor and use it in fetching the u- and v-
#   components of wind.  Using the hard copy prevents any changes we make
#   here from leaking outside this method.
    pred = copy.deepcopy(predictor)

#   Fetch the u-component of the horizontal wind.
#   The result is a camps data object.
    pred['search_metadata'].update({'property' : parse_pred.observedProperty('Uwind')})
    u_wind = read_var(filepath=filepaths, forecast_time=time, **pred['search_metadata'])
    assert(isinstance(u_wind,Camps_data)), "u_wind is expected to be a camps data object."
    mask = np.ma.getmaskarray(u_wind.data)
    try:
        u_unit = u_wind.metadata['units']
        u_pint = units.Quantity(1., u_unit)
        assert(u_pint.dimensionality == iu_pint.dimensionality),"Units of u_wind has wrong dimensionality."
    except KeyError:
        logging.info("Fetched u-wind has no specified units.")
        raise

#   Adopt unit from fetched u-wind if not set yet.
    if unit is None:
        unit = u_unit
        wspd.metadata.update({'units' : unit})
#   Construct metpy object of fetched u-wind.
#   To be used in calculating wind speed, taking advantage of metpy's coding that
#   accounts for differences in units.
    u_pint = units.Quantity(u_wind.data, u_unit)
#   Add u-wind to the list of components of wind speed.
    wspd.dimensions = copy.deepcopy(u_wind.dimensions)
    wspd.add_component(u_wind)
    wspd.preprocesses = u_wind.preprocesses

#   Fetch the v-component of the horizontal wind.
#   The result is a camps data object.
    pred['search_metadata'].update({'property' : parse_pred.observedProperty('Vwind')})
    v_wind = read_var(filepath=filepaths, forecast_time=time, **pred['search_metadata'])
    assert(isinstance(v_wind,Camps_data)), "v_wind is expected to be a camps data object."
    mask += np.ma.getmaskarray(v_wind.data)
    try:
        v_unit = v_wind.metadata['units']
        v_pint = units.Quantity(1., v_unit)
        assert(v_pint.dimensionality == iu_pint.dimensionality),"Units of v_wind has wrong dimensionality."
    except KeyError:
        logging.info("Fetched v-wind has no specified units.")
        raise
#   Construct metpy object of fetched v-wind.
#   To be used in calculating wind speed, taking advantage of metpy's coding that
#   accounts for differences in units.
    v_pint = units.Quantity(v_wind.data, v_unit)
#   Add v-wind to the list of components of wind speed.
    wspd.add_component(v_wind)
    for proc in v_wind.preprocesses:
        wspd.add_preprocess(proc)


#   Call the function calculating and returning the horizonatl wind speed given
#   it u- and v-components.  Metpy accounts for potential differences in units
#   between the u- and v-components.  Convert the returned data to the units
#   we established above.
    w_pint = wind_speed(u_pint, v_pint).to(unit)
#   Insert the data as numpy array into the data object of the wind speed.
#   But first it is necessary to set the dimensions object within the camps
#   data object for the wind speed.
    wspd.add_data(np.ma.array(np.array(w_pint), mask=mask))

#   Construct the rest of the Camps data object wspd.
    wspd.time = copy.deepcopy(u_wind.time)
    wspd.location = u_wind.location
    wspd.add_vert_coord(u_wind.get_coordinate())
    wspd.metadata[const.VERT_COORD] = u_wind.metadata[const.VERT_COORD]
    wspd.metadata.update({'coordinates' : u_wind.metadata.get('coordinates')})
    wspd.metadata.update({'FcstTime_hour' : u_wind.metadata.get('FcstTime_hour')})
    wspd.metadata.update({'PROV__hadPrimarySource' : u_wind.metadata.get('PROV__hadPrimarySource')})
    wspd.add_process('WindSpeedCalc')

    return wspd



def wind_speed(u_wind, v_wind):
    r"""Calculates the horizontal wind speeds from its two components.

    Args:
        u_wind (pint.Quantity): u (+ easterly) component of the horizontal wind.
        v_wind (pint.Quantity): v (+ northerly) component of the horizontal wind.

    Returns:
        wspd (pint.Quantity): wind speed.

    """

    wspd = np.sqrt(u_wind**2 + v_wind**2)

    return wspd



def WindChill_setup(filepaths, time, predictor):
    r"""Sets up the call to the wind_chill function
    which calculates the wind chill temperature as
    given by metpy.calc.wind_chill.

    Args:
        control(instance): contains mospred_control.yaml file variables.
        time(int): The valid time of the predictor given as the
            number of seconds since January 1, 1970 00Z.
        predictor(Predictor): a Predictor object instantiated prior
            to the call to this function with the metadata fields
            pre-filled.

    Returns:
        windchill(Camps_data): The calculated wind chill in units of
            degrees Fahrenheit.

    """

    #Instantiate the wind chill camps data object.
    windchill = Camps_data('wind_chill_instant')
    wc_unit = 'degF' #default units
    if windchill.units:
        wc_unit = windchill.units
    elif windchill.metadata['units']:
        wc_unit = windchill.metadata['units']
    windchill.metadata.update({ 'units' : wc_unit })

# Create a copy of the predictor object that you can
# alter without affecting the original.  That's a deep copy.
    pred = copy.deepcopy(predictor)

# Fetch the air temperature at 2 meters and the wind speed at 10 meters.
# These are needed to calculate the wind chill where it is valid to do so.

# Note that we assume that the temperature is available from model output.
# It is critical that the fetched temperature camps data object specify
# units.  Abandon calculating wind chill if no units found.
    pred['search_metadata'].update({'property' : parse_pred.observedProperty('Temp')})
    pred['search_metadata']['vert_coord1'] = 2
    temp = read_var(filepath=filepaths, forecast_time=time, **pred['search_metadata'])
    assert(isinstance(temp, Camps_data)), "temp is expected to be a camps data object."
    mask = np.ma.getmaskarray(temp.data)
    if temp.units:
        temp_unit = temp.units
    elif temp.metadata['units']:
        temp_unit = temp.metadata['units']
    else:
        logging.info("WindChill: Input temperature must have units.")
        return None
    q_temp = units.Quantity(temp.data, temp_unit)
    windchill.dimensions = temp.dimensions
    windchill.add_component(temp)
    windchill.preprocesses = temp.preprocesses

# Wind speed is not available from model output, but it could have been
# calculated and stored in a netcdf file.  So a fetch may succeeed.  If
# not, calculate it.  Like for temperature, it is critical that the
# wind speed camps data object specify units.
    pred['search_metadata'].update({'property' : parse_pred.observedProperty('WindSpd')})
    pred['search_metadata']['vert_coord1'] = 10
    wspd = read_var(filepath=filepaths, forecast_time=time, **pred['search_metadata'])
    if wspd is None:
        wspd = create.calculate(filepaths, time, pred)
    assert(isinstance(wspd, Camps_data)), "wspd is expected to be a camps data object."
    mask += np.ma.getmaskarray(wspd.data)
    if wspd.units:
        wspd_unit = wspd.units
    elif wspd.metadata['units']:
        wspd_unit = wspd.metadata['units']
    else:
        return None
    q_wspd = units.Quantity(wspd.data, wspd_unit)
    windchill.add_component(wspd)
    for proc in wspd.preprocesses:
        windchill.add_preprocess(proc)

# Since the actual calculation is done by MetPy, the input arguments
# must be of class pint.Quantity.  These objects are essentially numpy
# arrays with an associated unit and methods that can change units.
    q_data = wind_chill(q_temp, q_wspd).to(wc_unit)

# The Metpy quantity has an attribute that is an array of boolean values
# that serves as a mask indicating where in the wind chill array the wind
# chill formula is invalid.  Here we just fill in the air temperature
# in the units we specified for the wind chill.
    q_tf = q_temp.to(wc_unit) # air temp in same units as wind chill.
    mask_invalid = q_data.mask.astype(np.int)
    mask_valid = 1 - mask_invalid
    data = mask_valid*np.array(q_data) + mask_invalid*np.array(q_tf)
    windchill.add_data(np.ma.array(data, mask=mask))

# Create the Camps data object windchill using the temperature
# camps data object as a guide.  The data attribute will be filled
# in from output by Metpy.calc's windchill method
    windchill.time = copy.deepcopy(temp.time)
    windchill.location = temp.location
    windchill.properties = temp.properties
    windchill.add_vert_coord(temp.get_coordinate())
    windchill.metadata[const.VERT_COORD] = temp.metadata[const.VERT_COORD]
    windchill.metadata.update({'coordinates' : temp.metadata.get('coordinates')})
    windchill.metadata.update({'FcstTime_hour' : temp.metadata.get('FcstTime_hour')})
    windchill.metadata.update({'PROV__hadPrimarySource' : temp.metadata.get('PROV__hadPrimarySource')})
    windchill.add_process('WindChillCalc')

    return windchill



def wind_chill(temperature, wind_speed):
    r"""This function calls the metpy method that calculates
    the wind chill.  The arguments are pint Quantities that
    carry their units.  The metpy method returns a wind chill
    with the units of degrees Fahrenheit.

    Args:
        temperature(pint.Quantity): atmospheric temperature.
        wind_speed(pint.Quantity): horizontal wind speed.

    Returns:
        wchill(pint.Quantity): wind chill in units of degree Fahrenheit.

    """

    wchill = calc.windchill(temperature, wind_speed)

    return wchill

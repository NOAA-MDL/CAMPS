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

from ...core.fetch import *
from ...core.Time import epoch_to_datetime
from ...core import Time as Time
from ...core.Camps_data import Camps_data



def wind_speed_setup(filepaths, time, predictor):
    """This method prepares relevant parameters for the calculation of
        horizontal wind speed at a specified vertical level.

    Args:
        control(instance): contains mospred_control.yaml file variables.
        time (int): The number of seconds since January 1, 1970 00Z.
        predictor (Predictor): a container that holds key/value pairs 
            used to enquire the database for information about the 
            specified predictor.  A hard copy is modified within this method to
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

#   Obtain the wind speed unit specified in the database, determine if it
#   exists, and, if so, test its dimensionality.
    unit = None
    try:
        unit = wspd.metadata['units']
        q_pint = units.Quantity(1., unit)       
        assert(q_pint.dimensionality == iu_pint.dimensionality),"Wind speed units given in the database have the wrong dimensionality."
    except KeyError:
        logging.info("metadata key \'units\' does not exist or has no value within the database.")
        logging.info("Adopt the units of the fetched wind components.")

#   Now set up for fetching the u- and v-components of the horizontal wind
#   from which we calculate the wind speed.
#   Make a hard copy of the predictor and use it in fetching the u- and v-
#   components of wind.  Using the hard copy prevents any changes we make
#   here from leaking outside this method.
    pred = predictor.copy()

#   Fetch the u-component of the horizontal wind.
#   The result is a camps data object.
    pred.change_property('Uwind')
    u_wind = fetch(filepaths, time, **pred.search_metadata)
    assert(isinstance(u_wind,Camps_data)), "u_wind is expected to be a camps data object."
    try:
        u_unit = u_wind.metadata['units']
        u_pint = units.Quantity(1., u_unit)
        assert(u_pint.dimensionality == iu_pint.dimensionality),"Units of u_wind has wrong dimensionality."
    except KeyError:
        logging.info("Fetched u-wind has no specified units.")
        raise

#   Copy the processes from u_wind
    wspd.processes = copy.deepcopy(u_wind.processes)

#   Adopt unit from fetched u-wind if not set yet.
    if unit is None:
        unit = u_unit
        wspd.metadata.update({'units' : unit})
#   Construct metpy object of fetched u-wind.
#   To be used in calculating wind speed, taking advantage of metpy's coding that
#   accounts for differences in units.
    u_pint = units.Quantity(u_wind.data, u_unit)
##   Add u-wind to the list of components of wind speed.
#    wspd.add_component(u_wind)

#   Fetch the v-component of the horizontal wind.
#   The result is a camps data object.
    pred.change_property('Vwind')
    v_wind = fetch(filepaths, time, **pred.search_metadata)
    assert(isinstance(v_wind,Camps_data)), "v_wind is expected to be a camps data object."
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
##   Add v-wind to the list of components of wind speed.
#    wspd.add_component(v_wind)


#   Call the function calculating and returning the horizonatl wind speed given
#   it u- and v-components.  Metpy accounts for potential differences in units 
#   between the u- and v-components.  Convert the returned data to the units 
#   we established above.
    w_pint = wind_speed(u_pint, v_pint).to(unit)
#   Insert the data as numpy array into the data object of the wind speed.
#   But first it is necessary to set the dimensions object within the camps
#   data object for the wind speed.
    wspd.dimensions = copy.deepcopy(u_wind.dimensions)
    wspd.add_data(np.array(w_pint))

#   Construct the rest of the Camps data object wspd.
    wspd.time = copy.deepcopy(u_wind.time)
    wspd.location = u_wind.location
    wspd.add_coord(u_wind.get_coordinate())
    wspd.metadata.update({'coordinates' : u_wind.metadata.get('coordinates')})
    wspd.metadata.update({'FcstTime_hour' : u_wind.metadata.get('FcstTime_hour')})

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

# Create a copy of the predictor object that you can
# alter without affecting the original.  That's a deep copy.
    pred = predictor.copy()

# Fetch the air temperature at 2 meters and the wind speed at 10 meters.
# These are needed to calculate the wind chill where it is valid to do so.

# Note that we assume that the temperature is available from model output.
# It is critical that the fetched temperature camps data object specify 
# units.  Abandon calculating wind chill if no units found.
    pred.change_property('Temp')
    pred.search_metadata['vert_coord1'] = 2
    temp = fetch(filepaths, time, **pred.search_metadata)
    if temp.units:
        temp_unit = temp.units
    elif temp.metadata['units']:
        temp_unit = temp.metadata['units']
    else:
        logging.info("WindChill: Input temperature must have units.")
        return None

# Wind speed is not available from model output, but it could have been
# calculated and stored in a netcdf file.  So a fetch may succeeed.  If
# not, calculate it.  Like for temperature, it is critical that the
# wind speed camps data object specify units.
    pred.change_property('WindSpd')
    pred.search_metadata['vert_coord1'] = 10
    wspd = fetch(filepaths, time, **pred.search_metadata)
    if wspd is None:
        wspd = wind_speed_setup(filepaths, time, pred)
    if wspd.units:
        wspd_unit = wspd.units
    elif wspd.metadata['units']:
        wspd_unit = wspd.metadata['units']
    else:
        return None

# Create the Camps data object windchill using the temperature
# camps data object as a guide.  The data attribute will be filled
# in from output by Metpy.calc's windchill method 
    windchill = Camps_data('wind_chill_instant')
    wc_unit = 'degF' #default units
    if windchill.units:
        wc_unit = windchill.units
    elif windchill.metadata['units']:
        wc_unit = windchill.metadata['units']
    windchill.time = temp.time
    windchill.location = temp.location
    windchill.dimensions = temp.dimensions
    windchill.processes = temp.processes
    windchill.properties = temp.properties
    windchill.add_coord(temp.get_coordinate())
    for k,v in temp.metadata.iteritems():
        if not 'name' in k \
        and not 'Property' in k \
        and not 'units' in k:
            windchill.metadata[k] = v

# Since the actual calculation is done by MetPy, the input arguments
# must be of class pint.Quantity.  These objects are essentially numpy
# arrays with an associated unit and methods that can change units.
    q_temp = units.Quantity(temp.data, temp_unit)
    q_tf = q_temp.to(wc_unit) # air temp in same units as wind chill.
    q_wspd = units.Quantity(wspd.data, wspd_unit)
    q_data = wind_chill(q_temp, q_wspd).to(wc_unit)

# The Metpy quantity has an attribute that is an array of boolean values
# that serves as a mask indicating where in the wind chill array the wind 
# chill formula is invalid.  Here we just fill in the air temperature
# in the units we specified for the wind chill.
    mask_invalid = q_data.mask.astype(np.int)
    mask_valid = 1-mask_invalid
    windchill.data = mask_valid*np.array(q_data) + mask_invalid*np.array(q_tf)

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



#def vorticity_setup():
#    r"""
#    """
#
#    predictor.change_property('AbsVort')
#    absv = fetch(time, **predictor.search_metadata)
#
#    return absv
#
#
#
#def RelativeVorticity_setup(time, grid, rv_obj):
#    r"""
#    """
#
#    predictor.change_property('Uwind')
#    u_wind = fetch(time, **predictor.search_metadata)
#    predictor.change_property('Vwind')
#    v_wind = fetch(time, **predictor.search_metadata)
#    udelta = None
#    vdelta = None
#
#    relvort = u_wind
#    relvort.data = relative_vorticity(u_wind.data, v_wind.data, udelta, vdelta)
#    relvort.metadata['property'] = 'RelVort'
#
#    return relvort
#
#
#
#def relative_vorticity(uwind, vwind, udelta, vdelta):
#    relvort() = (u(:,2:)-u(:,0:nv-2))/(vdelta(:,1:nv-1)) \
#               - (v(2:,:)-v(0:nv-2,:))/(2.*udelta()))
#    Linearly interpolate for the edge values
#    relvort()
#    return relvort
#    return None

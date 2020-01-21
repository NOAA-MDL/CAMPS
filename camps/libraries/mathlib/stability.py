"""Atmospheric stability indices.

This module's methods fetch or calculate predictors related to
the stability of the atmosphere against air parcel convection.

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
from ...core import Camps_data
from . import moisture



def KIndex_setup(filepaths, time, predictor):
    r"""The K stability index is a linear function of several weather
        parameters: air temperatures at pressure levels of 850 hPa,
        700 hPa, and 500 hPa, and dewpoint temperatures at pressure
        levels of 850 hPa and 700 hPa.  It normally has units of
        degrees Centigrade.

    Args:
        control(instance): contains mospred_control.yaml file variables.
        time (int): The time in seconds since January 1, 1970 00Z
        predictor (Predictor): a generic predictor object carrying
            information necessary to fetch Camps data objects from 
            netCDF4 files via a database.

    Returns:
        kindex (Camps_data): a camps data object containing metadata
            and data of the K index.

    """
    
#   Instantiate the camps data object for the K index.
#   Certain attributes are set in this instantiation.
    kindex = Camps_data("k_index_instant")
    international_units = { 'Temperature' : 'kelvin' } #Future global dictionary

#   The K index has units of temperature, particularly degrees Celsius.
#   Get the international standard unit for temperature
#   and construct a MetPy object containing that unit.  It will be used
#   below to test the dimensionality of the units in objects of temperature.
    iu_unit = international_units.get('Temperature')
    iu_pint = units.Quantity(1., iu_unit)

#   The unit for K-index must be degrees Celsius.
    try:
        unit = kindex.metadata['units']
        if unit != 'degC':
            logging.info("Reset units of stability K index from %s to degC" % unit)
    except KeyError:
        logging.info("metadata key \'units\' does not exist or has no value.")
        logging.info("Inserted into metadata, set to \'degC\'.")
    unit = 'degC'
    kindex.metadata.update({'units' : unit})

#   Make a hard copy of the Predictor object predictor to
#   use in fetching the components of the K index.  It is
#   necessary to do this in order to prevent inadvertently
#   changing the key/value pairs for 
    pred = predictor.copy()

#   Fetch the weather parameters that make up K index.
#   Check that they are camps data objects
#   and that they have units of temperature.
    pred.change_property('Temp')

#   Fetch temperature at isobar 850 mbar
    pred.search_metadata.update({'vert_coord1' : 850})
    t850 = fetch(filepaths, time, **pred.search_metadata)
    assert(isinstance(t850,Camps_data)),"t850 expected to be camps data object"
    try:
        t850_unit = t850.metadata['units']
        t_pint = units.Quantity(1., t850_unit)
        assert(t_pint.dimensionality == iu_pint.dimensionality),"t850 does not have dimensions of temperature"
    except KeyError:
        logging.info("Fetched temperature at 850hPa has no units!")
        raise
#   Construct MetPy object to be used in calculating the K index.
##   And add the camps data object of the 850 mb air temperature to
##   the list of components of the K index.
    q_t850 = units.Quantity(t850.data, t850_unit)
#    kindex.add_component(t850)

#   Fetch temperature at isobar 700 mbar
    pred.search_metadata.update({'vert_coord1' : 700})
    t700 = fetch(filepaths, time, **pred.search_metadata)
    assert(isinstance(t700,Camps_data)),"t700 expected to be camps data object"
    try:
        t_unit = t700.metadata['units']
        t_pint = units.Quantity(1., t_unit)
        assert(t_pint.dimensionality == iu_pint.dimensionality),"t700 does not have dimensions of temperature"
    except KeyError:
        logging.info("Fetched temperature at 700hPa has no units")
        raise
#   Construct MetPy object to be used in calculating the K index.
##   And add the camps data object of the 700 mb air temperature to
##   the list of components of the K index.
    q_t700 = units.Quantity(t700.data, t_unit)
    q_t700.ito(t850_unit)
#    kindex.add_component(t700)

#   Fetch temperature at isobar 500 mbar
    pred.search_metadata.update({'vert_coord1' : 500})
    t500 = fetch(filepaths, time, **pred.search_metadata)
    assert(isinstance(t500,Camps_data)),"t500 expected to be camps data object"
    try:
        t_unit = t500.metadata['units']
        t_pint = units.Quantity(1., t_unit)
        assert(t_pint.dimensionality == iu_pint.dimensionality),"t500 does not have dimensions of temperature"
    except KeyError:
        logging.info("Fetched temperature at 500hPa has no units")
        raise
#   Construct MetPy object to be used in calculating the K index.
##   And add the camps data object of the 500 mb air temperature to
##   the list of components of the K index.
    q_t500 = units.Quantity(t500.data, t_unit)
    q_t500.ito(t850_unit)
#    kindex.add_component(t500)

#   Dewpoint temperature components of K index.
#   These parameters may not be available from netCDF files.
#   But if relative humidity is, then we calculate it from
#   the dewpoint temperature function within the module moisture.
    pred.change_property('DewPt')

#   Fetch dewpoint temperature at isobar 850 mbar.
#   If fetch fails, try the dewpoint temperature function.
    pred.search_metadata.update({'vert_coord1' : 850})
    td850 = fetch(filepaths, time, **pred.search_metadata)
    if td850 is None:
        td850 = moisture.dewpoint_temperature_setup(filepaths, time, pred)
    assert(isinstance(td850,Camps_data)),"td850 expected to be camps data object"
    try:
        t_unit = td850.metadata['units']
        t_pint = units.Quantity(1., t_unit)
        assert(t_pint.dimensionality == iu_pint.dimensionality),"td850 does not have dimensions of temperature"
    except KeyError:
        logging.info("Fetched dewpoint temperature at 850hPa has no units")
        raise
#   Construct MetPy object to be used in calculating the K index.
##   And add the camps data object of the 850 mb dewpoint temperature to
##   the list of components of the K index.
    q_td850 = units.Quantity(td850.data, t_unit)
    q_td850.ito(t850_unit)
#    kindex.add_component(td850)

#   Fetch dewpoint temperature at isobar 700 mbar.
#   If fetch fails, try the dewpoint temperature function.
    pred.search_metadata.update({'vert_coord1' : 700})
    td700 = fetch(filepaths, time, **pred.search_metadata)
    if td700 is None:
        td700 = moisture.dewpoint_temperature_setup(filepaths, time, pred)
    assert(isinstance(td700,Camps_data)),"td700 expected to be camps data object"
    try:
        t_unit = td700.metadata['units']
        t_pint = units.Quantity(1., t_unit)
        assert(t_pint.dimensionality == iu_pint.dimensionality),"td700 does not have dimensions of temperature"
    except KeyError:
        logging.info("Fetched dewpoint temperature at 700hPa has no units")
        raise
#   Construct MetPy object to be used in calculating the K index.
##   And add the camps data object of the 700 mb dewpoint temperature to
##   the list of components of the K index.
    q_td700 = units.Quantity(td700.data, t_unit)
    q_td700.ito(t850_unit)
#    kindex.add_component(td700)

#   Call the function that constructs the K index as a pint.Quantity object.
#   The key advantage of using pint.Quantity objects is that their
#   mathematical operators account for differences in units of the operands.
#   Add the dimensions to the camps data object before inserting the data
#   into it.
    q_kindex = KIndex(q_t850, q_t700, q_t500, q_td850, q_td700).to(unit)
    kindex.add_dimensions(u'y')
    kindex.add_dimensions(u'x')
    kindex.add_dimensions(u'elev')
    kindex.add_data(np.array(q_kindex))
    kindex.processes = copy.deepcopy(td700.processes)

#   Create the rest of the camps data object for K index
    kindex.add_coord(0,vert_type='elev')
    kindex.time = copy.deepcopy(t850.time)
    kindex.location = t850.location
    kindex.metadata.update({'FcstTime_hour' : t850.metadata.get('FcstTime_hour')})

    return kindex



def KIndex(t850, t700, t500, td850, td700):
    r"""The K index formula.

    Args:
        t850 (pint.Quantity): Atmospheric temperature (K) at isobar 850mb.
        t700 (pint.Quantity): Atmospheric temperature (K) at isobar 700mb.
        t500 (pint.Quantity): Atmospheric temperature (K) at isobar 500mb.
        td850 (pint.Quantity): Atmospheric dewpoint temperature (K) at isobar 850mb.
        td700 (pint.Quantity): Atmospheric dewpoint temperature (K) at isobar 700mb.

    Returns:
        kindex (pint.Quantity): A stability index of the atmosphere (deg C)

    K-index = (t850 - t500) + td850 - (t700 - td700).
    It is useful for predicting non-severe warm season
    convective activity.  Its unit is commonly degrees
    Centigrade.

    """

    kindex = (t850 - t500) + td850 - (t700 - td700)

    return kindex



def cape_setup(filepaths, time, predictor):
    r"""The method fetching atmospheric stability index CAPE.

    CAPE is the Convective Available Potential Energy.

    args:
        time (int): Time in seconds since January 1, 1970 00Z.
        predictor (predictor): a generic predictor object consisting of a
            numpy.ndarray data object plus some metadata.

    Returns:
        cape, a predictor object containing data of the stability index CAPE.

    """

    predictor.change_property('CAPE')
    cape = fetch(filepaths, time, **predictor.search_metadata)

    return cape



def cin_setup(filepaths, time, predictor):
    r"""The method fetching atmospheric stability index CIN.

    CIN stands for the Convective INhibition.  It has units of energy.

    args:
        time (int): Time in seconds since January 1, 1970 00Z.
        predictor (predictor): a generic predictor object consisting of a
            numpy.ndarray data object plus some metadata.

    Returns:
        cin, a predictor object containing data of the stability index CIN.

    """

    predictor.change_property('CIN')
    cin = fetch(filepaths, time, **predictor.search_metadata)

    return cin

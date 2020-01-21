import logging
import os
import sys
import re
import pdb
import string
import copy
import metpy
from metpy.units import units
import math
import numpy as np
from operator import itemgetter

from ...registry.db import db as db
from ...core.fetch import *
from ...core.Time import epoch_to_datetime
from ...core import Time as Time
from ...core import Camps_data


def dewpoint_temperature_setup(filepaths, time, predictor):
    r"""This method prepares relevant parameters for the calculation of
        the dewpoint temperature at a specified vertical level.

    Args:
        control(instance): contains mospred_control.yaml file variables.
        time (int): The number of seconds since January 1, 1970 00Z.
        predictor (Predictor): a generic object of type Predictor holding
            an appropriately sized data array and metadata or properties
            pertaining to air temperature and atmospheric relative
            humidity.

    Returns:
        dewpt (Camps_data): A Camps data object containing the dewpoint
        temperature in the units of the fetched air temperature.

    """

#   Instatiate the camps data object for the dewpoint temperature.  
#   The camps data base is read for specific attribute values, initially
#   set in the camps registry netcdf.yaml file.
    dewpt = Camps_data("dew_point_temperature")
    international_units = { 'temperature' : 'kelvin' } #this will be a global dictionary.

#   Obtain the standard international units for this predictor.
#   The unit dimensionality of other objects will be checked against this international standard 
#   for correct dimensionality.
    intl_unit = international_units['temperature']
    iu_pint = units.Quantity(1., intl_unit)

#   Determine the unit for the constructed predictor.
#   First try to obtain the unit from the instantiation process.
#   If set here, then test its dimensionality.
    unit = None
    try:
        unit = dewpt.metadata['units']
        u_pint = units.Quantity(1.,unit)
        assert(u_pint.dimensionality == iu_pint.dimensionality),"Wrong unit dimensionality for dew_point_temperature in netcdf.yaml"
    except KeyError:
        logging.info("dewpt: ")
        logging.info("    Metadata key \'units\' does not exist or has no value.")
        logging.info("    Adopt the units of the fetched temperature.")

#   Create a deep copy of the inputted predictor object to use in
#   fetching various predictor components.
    pred = predictor.copy()

#   Fetch air temperature and adopt its units if one has not
#   been set so far.  The fetched object is tested for type
#   and, if its unit is adopted adopted, its unit dimensionality.
    pred.change_property('Temp')
    temp = fetch(filepaths, time, **pred.search_metadata)
    assert(isinstance(temp, Camps_data)),"temp expected to be camps data object"

#   Copy any processes from temp object to dewpt object
    dewpt.processes = copy.deepcopy(temp.processes)

#   Create the met.py version of the air temperature
#   to be used in calculating the dewpoint temperature.
##   Declare the camps data object for temperature a component
##   of dewpoint temperature.
    try:
        t_unit = temp.metadata['units']
        t_pint = units.Quantity(1.,t_unit)
        assert(t_pint.dimensionality == iu_pint.dimensionality),"Wrong unit dimensionality for fetched temperature."
    except KeyError:
        logging.info("temp: ")
        logging.info("    Fetched temperature does not have defined units!")
        raise
    q_temp = units.Quantity(temp.data, t_unit)
#    dewpt.add_component(temp)
    if unit is None:
        unit = t_unit
        dewpt.metadata.update({'units' : unit})

#   Fetch atmospheric relative humidity and test if its
#   a camps data object.  Its unit is dimensionless, either
#   ranging from 0 to 100 as a percentage or 0 to 1 as a
#   proportion.
    pred.change_property('RelHum')
    rel_hum = fetch(filepaths, time, **pred.search_metadata)
    assert(isinstance(rel_hum, Camps_data)),"rel_hum expected to be camps data object"
#   Create the met.py version of the relative humidity, casting
#   it as a proportion with range [0,1].
##   Declare the camps data object for relative humidity a
##   component of dewpoint temperature.
    q_relhum = units(None) * rel_hum.data
    if np.amax(rel_hum.data) > 2:
        q_relhum = q_relhum/100
#    dewpt.add_component(rel_hum)
    
#   Call the function dewpoint that calls the metpy.calc function
#   calculating dewpoint temperature.  Convert values to units of 'unit'.
    q_data = dewpoint(q_temp, q_relhum).to(unit)
#   Before loading the data attribute, declare the its dimensions.
    dewpt.dimensions = copy.deepcopy(temp.dimensions)
    dewpt.add_data(np.array(q_data))

#   Finish constructing the dewpoint temperature Camps data object
#   and return it.
    dewpt.time = copy.deepcopy(temp.time)
    dewpt.location = temp.location
    dewpt.add_coord(temp.get_coordinate())
    dewpt.metadata.update({'coordinates' : temp.metadata.get('coordinates')})
    dewpt.metadata.update({'FcstTime_hour' : temp.metadata.get('FcstTime_hour')})

    return dewpt


def dewpoint(temp, rel_hum):
    r"""This method calls the metpy.calc function dewpoint_rh
        which takes the pint.Quantity objects containing the
        atmospheric temperature and atmospheric relative
        humidity and produces the dewpoint temperature in units
        of degrees Centigrade.

    """

    q_dewpt = metpy.calc.dewpoint_rh(temp, rel_hum)

    return q_dewpt



def mixing_ratio_setup(filepaths, time, predictor):
    r"""This method prepares relevant parameters for the calculation of
        the mixing ratio at a specified pressure level.

    Args:
        control(instance): contains mospred_control.yaml file variables.
        time (int): The number of seconds since January 1, 1970 00Z.
        predictor (Predictor): a generic object of type Predictor holding
            an appropriately sized data array and metadata or properties
            pertaining to air temperature and atmospheric relative
            humidity.

    Returns:
        mixr (Camps_data): A Camps data object containing the mixing
        ratio in units of grams of water vapor in a kilogram of atmosphere.

    """

#   Instatiate the camps data object for the mixing ratio.  
#   The camps data base is read for specific attribute values, initially
#   set in the camps registry netcdf.yaml file.
    mixr = Camps_data("mixing_ratio_instant")
    international_units = { 'mixing_ratio' : 'g/kg'} #this will be a global dictionary.
    international_units.update({ 'temperature' : 'kelvin'})

#   Obtain the standard international units for this predictor.
#   The unit dimensionality of other objects will be checked against this international standard 
#   for correct dimensionality.
    intl_unit = international_units.get('mixing_ratio')
    iu_pint = units.Quantity(1., intl_unit)

#   Determine the unit for the constructed predictor.
#   First try to obtain the unit from the instantiation process.
#   If set here, then test its dimensionality.
#   Else just adopt the international unit.
    unit = None
    try:
        unit = mixr.metadata['units']
        u_pint = units.Quantity(1.,unit)
        assert(u_pint.dimensionality == iu_pint.dimensionality),"Wrong unit dimensionality for mixing_ratio_instant in netcdf.yaml"
    except KeyError:
        logging.info("mixr: ")
        logging.info("    Metadata key \'units\' does not exist or has no value.")
        logging.info("    Adopt the international units.")
        unit = intl_unit
        mixr.metadata.update({ 'units' : intl_unit })

#   Deep copy the inputted predictor object to use in
#   fetching various predictor components without having these
#   changes leaking outside of the method.
    pred = predictor.copy()

#   The air pressure is a factor in calculating the mixing ratio.
#   Get its value and create a metpy object of it.
    p_level = pred.search_metadata.get('vert_coord1')
    q_plev = units.Quantity(p_level, units.mbar).to('millibars') #millibars assumed.
#   Note: the above line will change when the vertical coordinate units are read in
#         and not assumed.
    mixr.add_coord(p_level, vert_type='plev')

#   Fetch air temperature.  The fetched object is tested for type
#   and unit dimensionality.
    pred.change_property('Temp')
    iu_unit = international_units.get('temperature')
    iu_pint = units.Quantity(1., iu_unit)
    temp = fetch(filepaths, time, **pred.search_metadata)
    assert(isinstance(temp, Camps_data)),"temp expected to be camps data object"
    try:
        u_temp = temp.metadata['units']
        t_pint = units.Quantity(1., u_temp)
        assert(t_pint.dimensionality == iu_pint.dimensionality),"Fetched temperature units have wrong dimensionality."
    except KeyError:
        logging.info("temp: ")
        logging.info("    Fetched temperature does not have defined units!")
        raise

#   Copy processes from temp object
    mixr.processes = copy.deepcopy(temp.processes)
    
#   Create the met.py version of the air temperature
#   to be used in calculating the dewpoint temperature.
#   Declare the camps data object for temperature a component
#   of dewpoint temperature.
    q_temp = units.Quantity(temp.data, u_temp)
#    mixr.add_component(temp)

#   Fetch atmospheric relative humidity and test if its
#   a camps data object.  Its unit is dimensionless, either
#   ranging from 0 to 100 as a percentage or 0 to 1 as a
#   proportion.
    pred.change_property('RelHum')
    rh = fetch(filepaths, time, **pred.search_metadata)
    assert(isinstance(rh, Camps_data)),"rh expected to be camps data object"
#   Create the met.py version of the relative humidity, casting
#   it as a proportion with range [0,1].
##   Declare the camps data object for relative humidity a
##   component of dewpoint temperature.
    q_rh = units(None) * rh.data
    if np.amax(rh.data) > 2:
        q_rh = q_rh/100
#    mixr.add_component(rh)

#   Call the mixing ratio function, which uses metpy quantities
#   and calls metpy functions to create the mixing ratio.
#   A metpy object is returned and inserted as a numpy array
#   into the mixing ratio camps data object.
    q_data = mixing_ratio(q_plev, q_temp, q_rh).to(unit)
#   Before inserting data, declare its dimensions.
    mixr.dimensions = copy.deepcopy(rh.dimensions)
    mixr.add_data(np.array(q_data))

#   Construct the rest of the mixing ratio data camps object.
    mixr.time = copy.deepcopy(rh.time)
    mixr.location = rh.location
    mixr.metadata.update({'coordinates' : rh.metadata.get('coordinates')}) #needed for reshape to work.
    mixr.metadata.update({'FcstTime_hour' : rh.metadata.get('FcstTime_hour')})

    return mixr


def mixing_ratio(pressure_arr, temperature_arr, rel_hum_arr):
    """
    Compute the mixing ratio, 
    using the metpy module to obtain the saturation mixing ratio.
    Mixing ratio is the product of saturation mixing ratio and
    the relative humidity times the number of grams in a kilogram.  
    It's value is the mass of water vapor in grams in each 1000 grams 
    (1 kg) of atmosphere.
    """

    sat_mix_ratio = metpy.calc.saturation_mixing_ratio(pressure_arr, temperature_arr)
    mixing_ratio = sat_mix_ratio * rel_hum_arr

    return mixing_ratio
#
#    
#
def equivalent_potential_temperature_setup(filepaths, time, predictor):
    r"""This method prepares relevant parameters for the calculation of
        the equivalent potential temperature at a specified pressure level.
        The equivalent potential temperature is the temperature achieved 
        by adiabatically moving a parcel of air at a given temperature and 
        isobaric level to the reference pressure level of 1000 millibars,
        while accounting for phase transitions of water.

    Args:
        control(instance): contains mospred_control.yaml file variables.
        time (int): The number of seconds since January 1, 1970 00Z.
        predictor (Predictor): a generic object of type Predictor holding
            an appropriately sized data array and metadata or properties
            pertaining to air temperature and atmospheric relative
            humidity.

    Returns:
        eqpotemp (Camps_data): A Camps data object containing the equivalent
        potential temperature in units of the fetched temperature.

    """

#   Instantiate the camps data object for equivalent potential temperature.
    eqpotemp = Camps_data('equivalent_potential_temperature_instant')
    international_units = { 'temperature' : 'kelvin' }

#   Get the international standard units for temperature and
#   create a metpy object to use for testing unit dimensionality.
    iu_unit = international_units.get('temperature')
    iu_pint = units.Quantity(1., iu_unit)

#   Get the units that the database has for the equivalent potential temperature.
#   Test dimensionality.
#   If no unit is specified, pick it up from the fetched temperature below.
    unit = None
    try:
        unit = eqpotemp.metadata['units']
        u_pint = units.Quantity(1., unit)
        assert(u_pint.dimensionality == iu_pint.dimensionality),"The units from the database has the wrong dimensionality."
    except KeyError:
        logging.info("The database does not have units for equivalent potential temperature.")
        logging.info("Obtain these units from the fetched temperature.")

#   Fetch the components needed for the equivalent potential temperature.
#   Make a hard copy of the search keys to keep them from contaminating
#   other searches outside of this method.
    pred = predictor.copy()

#   Air pressure is a component of equivalent potential temperature.
#   Get the isobaric value, add its value to the camps data object,
#   and create a metpy object of it to be used in calculating the
#   equivalent potential temperature.
    isobar = pred.search_metadata.get('vert_coord1')
    eqpotemp.add_coord(isobar, vert_type='plev')
    q_isobar = units.Quantity(isobar, units.mbar)

#   Fetch the air temperature
#   Adopt its unit for equivalent potential temperature if
#   that unit has not been set yet.
    pred.change_property('Temp')
    temp = fetch(filepaths, time, **pred.search_metadata)
    assert(isinstance(temp, Camps_data)),"Fetched temperature is not a Camps data object."
    try:
        u_temp = temp.metadata['units']
        u_pint = units.Quantity(1., u_temp)
        iu_pint = units.Quantity(1., international_units.get('temperature'))
        assert(u_pint.dimensionality == iu_pint.dimensionality),"Fetched temperature units has wrong dimensionality."
    except KeyError:
        logging.info("Fetched temperature has no units.")
        raise
    if unit is None:
        unit = u_temp
        eqpotemp.metadata.update({ 'units' : unit })

#   Copy the processes from the temp object
    eqpotemp.processes = copy.deepcopy(temp.processes)
 

#   Create the metpy object for temperature and then
#   add the camps data object for temperature to the list
#   of components of equivalent potential temperature.
    q_temp = units.Quantity(temp.data, u_temp)
#    eqpotemp.add_component(temp)

#   Fetch the dewpoint temperature.
#   If that fails, then calculate it.
    pred.change_property('DewPt')
    dewpt = fetch(filepaths, time, **pred.search_metadata)
    if dewpt is None:
        dewpt = dewpoint_temperature_setup(filepaths, time, pred)
    assert(isinstance(dewpt, Camps_data)),"Fetched dewpoint temperature is not a Camps data object."
    try:
        u_dewpt = dewpt.metadata['units']
        d_pint = units.Quantity(1.,u_dewpt)
        iu_pint = units.Quantity(1., international_units.get('temperature'))
        assert(d_pint.dimensionality == iu_pint.dimensionality),"Fetched dewpoint temperature has wrong dimensionality."
    except KeyError:
        logging.info("Fetched dewpoint temperature has no units.")
        raise
#   Create the metpy object for dewpoint temperature, and then
##   add the camps data object of it to the list of components
##   of equivalent potential temperature.
    q_dewpt = units.Quantity(dewpt.data, u_dewpt)
#    eqpotemp.add_component(dewpt)

#   Call the function returning the equivalent potential temperature
#   as a Metpy object, convert that returning object to a numpy array, and
#   after declaring its dimensions, insert it into the camps data object.
    q_data = equivalent_potential_temperature(q_isobar, q_temp, q_dewpt).to(unit)
    eqpotemp.dimensions = copy.deepcopy(temp.dimensions)
    eqpotemp.add_data(np.array(q_data))

#   Construct the rest of the Camps data object of the
#   equivalent potential temperature.
    eqpotemp.time = copy.deepcopy(temp.time)
    eqpotemp.location = temp.location
    eqpotemp.metadata.update({ 'coordinates' : temp.metadata.get('coordinates') }) #needed for reshape to work.
    eqpotemp.metadata.update({ 'FcstTime_hour' : temp.metadata.get('FcstTime_hour') })

    return eqpotemp


def equivalent_potential_temperature(pressure, temperature, dewpoint):
    r"""This method calls the metpy.calc function equivalent_potential_temperature
        which takes the pint.Quantity objects containing the isobaric level value 
        and the temperature at that level and, assuming saturated water vapor,
        produces the corresponding equivalent potential temperature with the reference 
        pressure being 1000 millibars.

    """

    eqpotemp = metpy.calc.equivalent_potential_temperature(pressure, temperature, dewpoint)

    return eqpotemp



def heat_index_setup(filepaths, time, predictor):
    """
    Calculate the heat index.
    We use the method provided by MetPy, which is based on
    work presented in Steadman (1979) and Rothfusz(1990).
    """

# Produce a copy of the predictor object that is independent
# of the original object.  This avoids inadvertent changes to
# one object when effecting it on the other.
    pred = predictor.copy()

# Obtain the parameters that are assumed to be available
# either directly from the weather model output or created 
# earlier by this software package.  The formula for heat
# index requires temperature and relative humidity.
    pred.search_metadata['vert_coord1'] = 2
    pred.change_property('Temp')
    temp = fetch(filepaths, time, **pred.search_metadata)
    if temp.units:
        u_temp = temp.units
    elif temp.metadata['units']:
        u_temp = temp.metadata['units']
    else:
        logging.info("heat_index: the air temperature must have units.")
        return None

    pred.change_property('RelHum')
    rh = fetch(filepaths, time, **pred.search_metadata)
    if rh.units:
        u_rh = rh.units
    elif rh.metadata['units']:
        u_rh = rh.metadata['units']
    else:
        logging.info("heat_index: the relative humidity must have units.")
        return None
    if u_rh == u"%":
        u_rh = u"percent"

# Create camps data object for the heat index.
# The temperature camps data object is the key guide in
# constructing the heat index camps data object.
    ht_index = Camps_data('heat_index_instant')
    hi_unit = 'degF' # degrees Fahrenheit is the default unit
    if ht_index.units:
        hi_unit = ht_index.units
    elif ht_index.metadata['units']:
        hi_unit = ht_index.metadata['units']
    ht_index.time = temp.time
    ht_index.location = temp.location
    ht_index.dimensions = temp.dimensions
    ht_index.processes = temp.processes
    ht_index.properties = temp.properties
    ht_index.add_coord(temp.get_coordinate())
    for k,v in temp.metadata.iteritems():
        if not 'name' in k \
        and not 'Property' in k \
        and not 'units' in k:
            ht_index.metadata[k] = v

# Calculate the heat index using a method in MetPy.
# To do so, we have to contain the temperature and relative
# humidity data into pint.Quantity objects, which require
# that the units be specified.
    q_temp = units.Quantity(temp.data, u_temp).to('kelvin')
    q_rh = units.Quantity(rh.data, u_rh).to('dimensionless')
    q_data = heat_index(q_temp, q_rh).to(hi_unit)

# The MetPy method returns heat index values where it was valid
# to use the heat index formula.  There are no values where this
# formula was not valid to apply.  A mask array is an attribute
# of the pint.Quantity heat index, which is True if the heat index
# is invalid.  Where the heat index valus is invalid, we insert
# the temperature in appropriate units.
    q_tf = q_temp.to(hi_unit)
    mask_invalid = q_data.mask.astype(np.int)
    mask_valid = 1-mask_invalid
    ht_index.data = mask_valid*np.array(q_data) + mask_invalid*np.array(q_tf)

    return ht_index
#
#
#
def heat_index(temperature, relative_humidity):
    r"""
    Calls the MetPy module to calculate the heat index array.
    The array returned contains heat index values where valid.
    An array mask of boolean values is an attribute of the returned
    heat index array, where False corresponds to where a heat index
    is defined.
    """

    hi = metpy.calc.heat_index(temperature,relative_humidity,mask_undefined=True)

    return hi



def TotalPrecip(filepaths, time, predictor):
    """This function constructs the camps data object for total precipitation
    over a specified duration (3hr, 6hr, ...).  It fetches all available model
    output of this quantity and knits these inputs together on the specified
    timeline.

    Args:
        control(instance): a container possessing information from mospred_control.yaml.
        time(int): the forecast reference time in seconds since 1970 Jan 1, 00:00:00.
        predictor(Predictor): chiefly contains the key/value pairs used to enquire the
            database for locating the desired data.

    Returns:
        totpcp(Camps_data): a container of the data and metadata for total precipitation
            over a specified duration.

    """
    #pdb.set_trace()
#   total precipitation over a specified time period can have two
#   different unit dimensionalities: mass per unit area or length.
#   Mass per unit area is a superior unit in that it's value is
#   independent of the precipitation type.
    international_units = { 'precipitation_amount' : 'kg m**-2' }
    ipa_unit = international_units.get('precipitation_amount')
    ipa_pint = units.Quantity(1, ipa_unit)
    international_units.update({ 'lwe_thickness' : 'm' })
    ilt_unit = international_units.get('lwe_thickness')
    ilt_pint = units.Quantity(1, ilt_unit)

#   Make a hard copy of the predictor object and use that copy
#   in enquiring the database.  Changes in the copy will not
#   leak outside of this method.
    pred = predictor.copy()
    duration_method = pred.search_metadata['duration_method']
#   vertical coordinate is not relevant.  Precipitation is measured at ground level.
    vert_coord1 = pred.search_metadata['vert_coord1']
    duration = pred.search_metadata['duration']
    model = pred.search_metadata['source']
    cycle = int(pred.fcst_ref_time)
    leadTime = pred.leadTime
    file_id = pred.search_metadata['file_id']
    if leadTime < duration:
        return None
#
#   Instantiate a camps data object for total precipitation.
#   We assume that the duration specified in predictors.yaml is
#   given in hours.
    name = 'precipitation_amount_' + str(duration) + '_hour'
    totpcp = Camps_data(name)
    totpcp_dtype = totpcp.get_data_type()
    totpcp.change_data_type(totpcp_dtype)
    unit = None
    try:
        unit = totpcp.metadata['units']
        tp_pint = units.Quantity(1, unit)
        assert(tp_pint.dimensionality == ipa_pint.dimensionality \
            or tp_pint.dimensionality == ilt_pint.dimensionality), \
            "Unit from database has wrong dimensionality."
    except KeyError:
        logging.info("Database has no information about units.")
        logging.info("Adopt the unit from fetched total precipitations.")

#   Fetch total precipitation of all available positive durations.

#   First see if we can get the precipitation amount for the specified
#   duration from predictors in direct model output whose metadata is
#   contained in the Camps database.

#   Construct lookup dictionary
    info_dict = {'duration_method': duration_method, 'source': model, 'property': 'TotalPrecip', 
                 'vert_coord1': vert_coord1, 'reserved1': 'grid', 'file_id': file_id}
#   Fetch variables from netcdf file, allow for multiple objects returned via list
    info = fetch(filepaths, time, repeat=True, **info_dict)

#   If zero objects returned, exit function
    if info == None:
        return None

    durations_hrs_nosort = []
#   Info must be of type list to proceed
#   Record each duration time available from input file
#   Exclude TotalPrecip that correspond to a differnet daily model cycle
    if not isinstance(info, list):
        info = [info]
    for tup in info:
        if tup.FcstTime_hour == cycle:
            durations_hrs_nosort.append(tup.properties['hours'])
    durations_hrs = sorted(durations_hrs_nosort)

#   Stop if the specified duration of this method's product
#   is less than the smallest fetched duration.
#   NOTE: A better test is that duration must be a multiple of least one of the fetched durations.
    assert(duration >= min(durations_hrs)),"Specified duration must be greater than the smallest fetched duration."

#   Fianlly, fetch the available total precip data objects and collect them into a list
#   These will be used to construct the total precip of a specified duration at a specified
#   time that is not available in the fetched set.
    data = []
    ndata = len(info)
    for inc in range(ndata):
        dict = {'duration_method': duration_method, 'source': model, 'duration': durations_hrs[inc], 
                'property': 'TotalPrecip', 'vert_coord1': vert_coord1, 'reserved1': 'grid', 'file_id': file_id}
        data.append(fetch(filepaths, time, **dict))

#   Lets make the data objects in the list consistent with
#   one another.  First, they must correspond to the same grid.
#   Second, the data in these objects should have the same units.

#   Grids must match.
#   Right now it is a weak match in that we match only
#   the number of grid points along each axis.
    iy = data[0].dimensions.index('y')
    ix = data[0].dimensions.index('x')
    location = data[0].location
    ny_grid = data[0].data.shape[iy]
    nx_grid = data[0].data.shape[ix]
    data_grid = []
    for dt in data:
        if dt.data.shape[iy] == ny_grid and dt.data.shape[ix] == nx_grid:
            data_grid.append(dt)
    if data_grid == []:
        return None
    data = data_grid

#   Remove data objects that have the wrong dimensionality.
    data_dim = []
    for dt in data:
        try:
            dt_unit = dt.metadata['units']
            dt_pint = units.Quantity(1., dt_unit)
            if dt_pint.dimensionality == ipa_pint.dimensionality \
                or dt_pint.dimensionality == ilt_pint.dimensionality:
                data_dim.append(dt)
        except KeyError:
            pass
    if data_dim == []:
        return None
    data = data_dim

#   If the product data unit has not been specified yet,
#   set it to that of the first fetched data object.
    if unit is None:
        unit = data[0].metadata.get('units')

#   Force data of fetched objects to have the specified units.
#   No Metpy magic in this function.
    q_totpcp = units.Quantity(1., unit)
    q_h2oDensity = units.Quantity(1000.0, 'kg m**-3')
    if q_totpcp.dimensionality == ipa_pint.dimensionality:
        for i in range(len(data)):
            dt = data[i]
            dt.data.mask = np.ma.nomask
            q_data = units.Quantity(dt.data, dt.metadata.get('units'))
            if q_data.dimensionality == ilt_pint.dimensionality:
                q_data *= q_h2oDensity
                q_data.ito(unit)
            dt.data = np.ma.array(q_data)
            dt.metadata.update({ 'units' : unit })
    else:
        for i in range(len(data)):
            dt = data[i]
            dt.data.mask = np.ma.nomask
            q_data = units.Quantity(dt.data, dt.metadata.get('units'))
            if q_data.dimensionality == ipa_pint.dimensionality:
                q_data /= q_h2oDensity
                q_data.ito(unit)
            dt.data = np.ma.array(q_data)
            dt.metadata.update({ 'units' : unit })

#   Force the dimensions of the data arrays in the camps data objects
#   to be ('y', 'x', 'lead_time').  This code was written back when
#   this was the order of dimensions for the fetched total precip.
    ilt = data[0].dimensions.index('lead_times')
    for i in data:
        dt = np.moveaxis(i.data,[iy,ix,ilt],[-3,-2,-1])
        dims = [i.dimensions[j] for j in [iy,ix,ilt]]
        i.data=dt
        i.dimensions=dims

#   Is the data stored as a running sum or discrete units of
#   precipitation amount.  A running sum where the precip is 
#   accumulated along lead time, increasing from zero at the 
#   lead time of zero.
#
#   The algorithm to determine how total precip is stored is
#   to find the maximum value in each data object, note its location
#   by index (j,i), and follow its value along increasing lead time.
#   If the value never decreases, then the data is stored as a running
#   sum.  Otherwise, its in discrete units.
    cumulative = 1
    for dt in data:
        amts = dt.data
#        amts.mask = np.ma.nomask
        j,i,k = np.unravel_index(amts.argmax(), amts.shape)
        for ilt in range(1,amts[0,0,:].size):
            cumulative *= (amts[j,i,ilt] >= amts[j,i,ilt-1])

#   NOTE: The functions called below are not yet available.
#   The code below this conditional statement block (FORTRAN!)
#   assumes discrete buckets.  An error is raised if the fetched
#   data is cumulative.
    if cumulative:
        raise
#        totpcp = sum_amts_cumulative(pred, data)
    else:
        pass
#        totpcp = sum_amts_discrete(pred, data)

    
#   Here starts the essential construction of the total precipitation
#   from the addition/subtraction of the fetched set.
    durations = [dur*3600 for dur in durations_hrs] #duration_hrs used be in units of hours, but now is in seconds.
    totpcp.data = np.ma.zeros((ny_grid,nx_grid))
    t0 = time + (leadTime*3600)
    t1 = t0 - (duration*3600)

#   intervals will contain a list of times denoting the front and back times of
#   selected intervals from the set of fetched total precips used to construct
#   the desired toal precip.
#   Select or deselect time intervals.
    intervals = []
    for i in range(ndata):
        frntimes = [x+time for x in data[i].get_lead_time().data]
        bcktimes = [x-durations[i] for x in frntimes]
        intervals.append(list(zip(bcktimes, frntimes)))
    intvls = []
    for i in range(len(intervals[:])):
        intvls.append([intvl for intvl in intervals[i] if intvl[0] <= t0 and intvl[1] >= t1])
    fronts = [intvl[1] for sublist in intvls[:] for intvl in sublist]
    backs = [intvl[0] for sublist in intvls[:] for intvl in sublist]
    if t0 in fronts:
        path = [t0]
        intervals_selected = interval_selection(path,t1,intvls)
    elif t1 in backs:
        intvls_negrev = []
        for i in range(len(intvls[:])):
            intvls_negrev.append([(-intvl[1],-intvl[0]) for intvl in intvls[i]])
        path = [-t1]
        intervals_selected = interval_selection(path,-t0,intvls_negrev)

#   Go through the selected intervals adding/subtracting the 
#   the fetched total precip within that interval.
    if intervals_selected:
        front = intervals_selected.pop()
    while intervals_selected:
        back = intervals_selected.pop()

        sign = math.copysign(1., front - back)
        aback = abs(back)
        afront = abs(front)
        if afront > aback:
            intvl = (aback, afront)
        else:
            intvl = (afront, aback)
        for i in range(len(intervals[:])):
            if intvl in intervals[i]:
                idata = i
                ilt = intervals[i].index(intvl)
                break
        totpcp.data[:,:] += sign*data[idata].data[:,:,ilt]
        front = back
#   The data matrix of the CAMPS data object has been filled.
#   Construct the rest of this data object, starting with the
#   various times.
    phenomTpd = Time.PhenomenonTimePeriod(data=np.array([[[time+(leadTime*3600)-(duration*3600),time+(leadTime*3600)]]]))
    phenomTpd.duration = duration
    totpcp.time.append(phenomTpd)
    fcstRefTime = Time.ForecastReferenceTime(data=np.array([time]))
    totpcp.time.append(fcstRefTime)
    leadT = Time.LeadTime(data=np.array([(leadTime*3600)]))
    totpcp.time.append(leadT)
    resultT = Time.ResultTime(data=np.array([time]))
    totpcp.time.append(resultT)
    validT = Time.ValidTime(data=np.array([[[time,t0]]]))
    totpcp.time.append(validT)

#   Inherit from the fetched object with the shortest duration 
#   the non-time objects.
    totpcp.location = data[0].location
    totpcp.dimensions = copy.deepcopy(data[0].dimensions[0:2])
    totpcp.properties = copy.deepcopy(data[0].properties)
    totpcp.processes = copy.deepcopy(data[0].processes)
#   Insert the necessary metadata.
    totpcp.properties.update({ 'hours' : duration })
    totpcp.metadata.update({ 'coordinates' : data[0].metadata.get('coordinates') })
    totpcp.metadata.update({ 'FcstTime_hour' : data[0].metadata.get('FcstTime_hour') })
    totpcp.metadata['hours'] = duration
    return totpcp
            

def interval_selection(path,ll,i):
    """
    This function is called by TotalPrecip to search for intervals
    that can construct the desired total precip.
    """
    while path != []:
        if path[0] > ll:
            intvl = interval_retrieval_and_removal(i,path[0],1)
            if intvl == []:
                path.pop(0)
            else:
                path = [intvl[0]] + path
                if intvl[0] == ll:
                    return path
        else:
            intvl = interval_retrieval_and_removal(i,path[0],0)
            if intvl == []:
                path.pop(0)
            else:
                if intvl[1] > ll:
                    path.pop(0)
                else:
                    path = [intvl[1]] + path
                    if intvl[1] == ll:
                        return path
    return path


def interval_retrieval_and_removal(array, time, index):
    """
    This function is called by interval_selection to present
    time intervals that may work in calculating the total
    precipitation.
    """

    nlists = len(array[:])
    b = []
    for i in range(nlists):
        b = [x for x in array[i] if x[index] == time]
        if b != []:
            j = array[i].index(b[0])
            return array[i].pop(j)
    return b

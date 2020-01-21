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


def thickness(filepaths, time, predictor):
    r"""
    The thickness method calculates the difference in geopotential
    height between two specified pressure levels.  It should be
    positive, so the difference will be the geoheight of the smaller
    pressure minus the geoheight of the greater pressure.

    Args:
        control(instance): contains mospred_control.yaml file variables.
        time (int): the number of seconds since January 1, 1970.
        predictor (Predictor): an object of the class Predictor that
            essentially contains information necessary to search for
            written predictor data and metadata or to construct a Camps
            data object.

    Returns:
        thickness (Camps_data): contains the data/metadata for pressure
            layer thickness.
    """

    thickness = Camps_data('PLThick')
    international_units = { 'length' : 'm' }

    iu_unit = international_units.get('length')
    iu_pint = units.Quantity(1., iu_unit)

    unit = None
    try:
        unit = thickness.metadata['units']
        u_pint = units.Quantity(1., unit)
        assert(u_pint.dimensionality == iu_pint.dimensionality),"Unit for pressure layer thickness in database has wrong dimensionality."
    except KeyError:
        logging.info("Metadata key \'units\' does not exist or has no value.")
        logging.info("Adopt the unit of the fetched geopotential heights.")
        pass

        thickness.metadata.update({'units' : unit})

    #Make a deep copy of the predictor object.
    pred = predictor.copy()

    #Sort the isobar values with pl haviing the lesser value.
    plevel1 = pred.__getitem__('vert_coord1')
    plevel2 = pred.__getitem__('vert_coord2')
    pl = plevel1
    pg = plevel2
    if pl > pg:
        pl = plevel2
        pg = plevel1
    thickness.add_coord(pl,level2=pg,vert_type='plev')

    #Fetch the geopotential heights.
    pred.change_property('GeoHght')
    #The keys 'vert_coord2' and 'vert_method' cannot be in
    #the database queries for the two geopotential heights,
    #if the fetches are to succeed.
    pred.search_metadata.pop('vert_coord2')
    pred.search_metadata.pop('vert_method')
    #------------------------------------------------------

    q_ght = units.Quantity(1., unit)
    #Fetch the geopotential height corresponding to the lesser isobar.
    pred.search_metadata.update({'vert_coord1' : pl})
    ght_pl = fetch(filepaths, time, **pred.search_metadata)
    assert(isinstance(ght_pl,Camps_data)),"ght_pl expected to be camps data object"
    try:
        hpl_unit = ght_pl.metadata['units']
        hpl_pint = units.Quantity(1., hpl_unit)
        assert(hpl_pint.dimensionality == iu_pint.dimensionality),"Unit of fetched geopotential height has wrong dimensionality."
    except KeyError:
        logging.info("Fetched geopotential height has no units!")
        raise
    q_ghtPL = units.Quantity(ght_pl.data, hpl_unit)
    if unit is None:
        unit = hpl_unit
        thickness.metadata.update({ 'units' : unit })
#    thickness.add_component(ght_pl)

    #Fetch the geopotential height corresponding to the greater isobar.
    pred.search_metadata.update({'vert_coord1' : pg}) 
    ght_pg = fetch(filepaths, time, **pred.search_metadata)
    assert(isinstance(ght_pg,Camps_data)),"ght_pg expected to be camps data object"
    try:
        hpg_unit = ght_pg.metadata['units']
        hpg_pint = units.Quantity(1., hpg_unit)
        assert(hpg_pint.dimensionality == iu_pint.dimensionality),"Unit of fetched geopotential height has wrong dimensionality."
    except KeyError:
        logging.info("Fetched geopotential height has no units!")
        raise
    q_ghtPG = units.Quantity(ght_pg.data, hpg_unit)
#    thickness.add_component(ght_pg)

#   Copy the processes from ght_pg 
    thickness.processes = copy.deepcopy(ght_pg.processes)


    q_thick = (q_ghtPL - q_ghtPG).to(unit)
    thickness.add_dimensions(u'y')
    thickness.add_dimensions(u'x')
    thickness.add_dimensions(u'plev_bounds')
    thickness.add_data(np.array(q_thick))

    #Construct the pressure layer thickness camps data object.
    #The object is built by instantiating an object with empty substructures
    #and filling one substructure (metadata) with information in the
    #database table 'metadata'.  We further fill in the substructures with
    #references to the fetched object ght_pl, and edit portions to be
    #relevant for the constructed predictor.
    thickness.add_process('PressThickness')
    thickness.location = ght_pl.location
    thickness.time = copy.deepcopy(ght_pl.time)
    thickness.metadata.update({'FcstTime_hour' : ght_pl.metadata.get('FcstTime_hour')})
 
    return thickness

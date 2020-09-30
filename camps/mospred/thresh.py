import os
import sys
import re
import logging
import pdb
import operator
import numpy as np
from metpy.units import units
from math import *

from . import smooth
from . import interp
from .. import core



"""Module: thresh.py
Changes to a specified value data in a camps data object that satisfy a
simple specified threshold condition.

Methods:
    grid_binary
    apply_condition
    thresh_setup -- placeholder
"""


operator_to_func = {
    '>' : operator.gt,
    '<' : operator.lt,
    '>=' : operator.ge,
    '<=' : operator.le,
    '==' : operator.eq,
    '!=' : operator.ne
    }



def grid_binary(c_obj, operator_str, threshold, unit):
    """Converts the variable's data on a grid into binary values
    where values are mapped to the value one if they satisfy the condition
    'operator_str threshold', zero otherwise.  As presently constructed,
    the original data is lost.
    """

    # Check if camps object
    assert(isinstance(c_obj, core.Camps_data))

    # Check if camps object contains a grid
    assert('x' in c_obj.dimensions and 'y' in c_obj.dimensions)

    if len(unit) == 0:
        threshu = threshold
    elif len(unit) > 0:
        # Get units of data and convert threshold to those units
        # only if they have the same dimensionality.
        q_obj = units.Quantity(np.float(1.), c_obj.units) #NOTE: confirm that c_obj.units/c_obj.metadata['units'] exists
        q_thr = units.Quantity(np.float(threshold), unit)
        if q_obj.dimensionality != q_thr.dimensionality:
            if 'precip' in c_obj.name.lower():
                rh2o = units.Quantity(np.float(1000.), "kg m**-3")
                length = units.Quantity(np.float(1.), "meter")
                kgm2 = units.Quantity(np.float(1.), "kg m**-2")
                if q_obj.dimensionality == length.dimensionality and q_thr.dimensionality == kgm2.dimensionality:
                    q_thr /= rh2o
                elif q_obj.dimensionality == kgm2.dimensionality and q_thr.dimensionality == length.dimensionality:
                    q_thr *= rh2o
                else:
                    logging.warning('Unit of precipitation data not compatible with threshold unit')
                    logging.warning('and cannot be made so by dividing/multiplying by water density.')
                    raise
            else:
                logging.warning('Units of data not compatible with threshold unit.')
                raise
        threshu = q_thr.to(c_obj.units).magnitude

    # Make a copy of the data, in case original data needs to be retained.
    if isinstance(c_obj.data, np.ma.core.MaskedArray):
        c_obj.data.harden_mask() # harden mask to preserve it.
        data = np.copy(np.ma.getdata(c_obj.data))
        mask = np.ma.getmaskarray(c_obj.data)
    elif isinstance(c_obj.data, np.ndarray):
        data = np.copy(c_obj.data)
        mask = np.zeros(data.shape, dtype=np.int)
    else:
        logging.warning('Data array is of unexpected type.')
        raise

    # Form complementary pairs of operators
    # Left operator corresponds to that in the threshold condition.
    # The right operator is its complement, i.e. !(left operator).
    comp_pr_ops = [('>=','<'),('>','<='),('==','!='),('!=','=='),('<','>='),('<=','>')]
    yes, no = list(map(list, list(zip(*comp_pr_ops))))
    try:
        i = yes.index(operator_str)
    except:
        logging.warning('Grid binary threshold operator unrecognized.')
        raise

    # Make grid binary masks and apply them.
    mask_yes = apply_condition(data, yes[i], float(threshu))
    mask_no = apply_condition(data, no[i], float(threshu))
    data[mask_yes] = 1
    data[mask_no] = 0

    # Set Camps object data to binary.
    # Currently, replaces original data.
    # We hope to have the capability to create a new Camps object for
    # the grid binary data and preserve the original data in the
    # original Camps object.
    c_obj.data = np.ma.array(data, mask=mask)

    # Denote that this procedure has been applied.
    c_obj.add_process('BinaryGrid')
    for index, proc in enumerate(c_obj.processes):
        if 'BinaryGrid' in proc.name:
            break
    bgrid = c_obj.processes[index]
    bgrid.add_attribute('operator', operator_str)
    bgrid.add_attribute('threshold_value', threshold)
    bgrid.add_attribute('threshold_units', unit)
    # The data of grid binary has no units.
    c_obj.units = 'dimensionless'
    c_obj.metadata.update( {'units' : 'dimensionless'} )



def apply_condition(data, operator_str, threshold_value):
    """Creates boolean mask of data where set True if data satisfies the
    condition 'operator_str threshold_value' is set True, otherwise set
    to False.
    """

    # Identify the operator in the threshold condition.
    if operator_str not in list(operator_to_func.keys()):
        err_str = "operator '" + operator_str + "' cannot be identified"
        raise ValueError(err_str)

    # Set the operator function
    operator_func = operator_to_func[operator_str]

    # Return the boolean mask from applying the operator function to the data.
    return operator_func(data,threshold_value)



def thresh_setup():
    """This function will be the gateway to producing from a continous,
    infinitely-valued variable multiple binary grid predictors or categorical
    predictors.
    """
    pass

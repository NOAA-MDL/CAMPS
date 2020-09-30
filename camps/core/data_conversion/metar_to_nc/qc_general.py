import logging
from .qc_error import qc_error
import pdb



"""Module: qc_general.py

Methods:
    check_consistency
    check_min_max
    check_bounds
"""



MISSING_VALUE = 9999


def check_consistency(in_array, type_array, tolerance=10):
    """Consistency check of a value in a series with its immediate neighbors. If there are 2 consecutive
    values with an absolute difference exceeding a specified tolerance, then check
    if the absolute difference between its value and the average of its immediate neighbors
    exceeds tolerance, report error, and change value to MISSING_VALUE.
    """

    errors = []
    first_num = in_array[:]
    second_num = first_num[1:]
    third_num = second_num[1:]
    # where each element is a tuple.
    # element 0 is previous temp
    # element 1 is current temp
    # element 2 is next temp
    array_iterable = list(zip(first_num, second_num, third_num))
    for counter, i in enumerate(array_iterable):
        is_auto = type_array[counter] >= 2 and type_array[counter] <= 8
        if tolerance < 10:
            if is_auto:
                tolerance *= 2.0
        elif not is_auto:
            tolerance = 10

        diff = abs(i[0] - i[1])
        if i[0] != MISSING_VALUE \
            and i[1] != MISSING_VALUE \
            and i[2] != MISSING_VALUE \
                and diff > tolerance:
            logging.debug(">10 degree array difference, checking if consistent")
            diff = abs(((i[0] + i[2]) / 2) - i[1])
            if diff > tolerance:
                new_error = qc_error(
                    old_data_value=in_array[counter],
                    new_data_value=MISSING_VALUE,
                    date_of_error=counter,
                    explanation="Consistency check failed.  An absolute difference "
                    + "of " + str(diff) + " between the current value of " + str(i[1]) +
                    " and the average of previous value, " + str(i[0]) + ", "
                    " and the following value, " + str(i[2]) + ", was not "
                    "within " + str(tolerance)
                )
                errors.append(new_error)
                in_array[counter+1] = MISSING_VALUE

    return errors


def check_min_max(min_array, max_array):
    """Performs QC to check whether min array is greater than the max_array.
    If so, changes both values to MISSING_VALUE.  Returns a list of occurrences
    of this error.
    """

    # Number of elements in the minimum array must equal that of the maximum array
    if len(min_array) != len(max_array):
        raise ValueError("min/max arrays not the same")

    errors = [] # initialize the error list that will note where min exceeds max
    for i, (minimum, maximum) in enumerate(zip(min_array, max_array)):
        if minimum != MISSING_VALUE and maximum != MISSING_VALUE \
                and minimum > maximum:
            new_error = qc_error(
                old_data_value=minimum, new_data_value=MISSING_VALUE,
                explanation="The minimum:                  " +
                str(minimum) + "\n"
                " is greater than the maximum: " + str(maximum)
            )
            errors.append(new_error)
            min_array[i] = MISSING_VALUE
            max_array[i] = MISSING_VALUE

    return errors


def check_bounds(in_arr, minimum, maximum):
    """Checks values of in_arr to see if they are within the bounds of
    minimum and maximum. If outside of bounds, sets value to MISSING_VALUE.
    Returns a list of occurrences of this error.
    """

    # minimum must not exceed maximum
    if minimum > maximum:
        raise ValueError("minimum is greater than maximum")

    errors = []
    for i, value in enumerate(in_arr):
        if value != MISSING_VALUE \
                and (value < minimum or value > maximum):
            in_arr[i] = MISSING_VALUE
            new_error = qc_error(
                old_data_value=value, new_data_value=MISSING_VALUE,
                explanation="The value not between " + str(minimum) +
                " and " + str(maximum)
            )
            errors.append(new_error)

    return errors

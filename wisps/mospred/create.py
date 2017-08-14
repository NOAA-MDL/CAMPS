# Many import statements here
import os
import sys
file_dir = os.path.dirname(os.path.realpath(__file__))
relative_path = "/.."
path = os.path.abspath(file_dir + relative_path)
sys.path.insert(0, path)


"""
If a fetch cannot be done directly from observation and model output, 
calculations will need to be performed to get the variable.
"""

def calc_vorticity():
    """Sets up the calculation for vorticity.
    """
    # Fetch what you need
    
    # Extract the data

    # Call Math function
    #mathlib.momentum.calc_vorticity()
    pass

    # Create new object and return

creation_functions = {
        'vorticity' : calc_vorticity
        }


def get_function(observedProperty):
    if observedProperty in creation_functions:
        return creation_functions[observedProperty]




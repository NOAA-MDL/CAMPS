# Many import statements here

"""
If a fetch cannot be done directly from observation and model output, 
calculations will need to be performed to get the variable.
"""


creation_functions = {
        vorticity : math.momentum.compute_vorticity
        }


def get(observedProperty):
    if observedProperty in creation_functions:
        return creation_functions[observedProperty]

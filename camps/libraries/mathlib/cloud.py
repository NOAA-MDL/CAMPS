###NOT CURRENTLY IN USE.###
###FUNCTIONALITY COMING SOON###

import os
import sys
import re
import pdb
import metpy.calc as calc
from metpy.units import units
import math
import numpy as np
import operator
relative_path = os.path.abspath(
    os.path.dirname(os.path.realpath(__file__)) + "/../..")
sys.path.insert(0, relative_path)
from core.fetch import *
from core.Time import epoch_to_datetime
import core.Time as Time
from core.Camps_data import Camps_data



#!/usr/env python

import os
import sys
relative_path = os.path.abspath(
    os.path.dirname(os.path.realpath(__file__)) + "/..")
sys.path.insert(0, relative_path)

from Wisps_data import Wisps_data


arr = np.random.rand(169, 300, 3)

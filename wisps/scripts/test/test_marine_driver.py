#!/usr/bin/env python
import sys
import os
file_dir = os.path.dirname(os.path.realpath(__file__))
relative_path = "/../.."
path = os.path.abspath(file_dir + relative_path)
sys.path.insert(0, path)
from marine_to_nc.marinereader import marinereader
import metar_to_nc.qc_main as qc_main
import scripts.marine_driver as marine_driver
import pickle
import pdb
import numpy
import data_mgmt.writer as writer
from data_mgmt.Wisps_data import Wisps_data
import registry.util as util


def test_marine():
    marine_driver.main()


test_marine()

#!/usr/bin/env python
import os
import sys
file_dir = os.path.dirname(os.path.realpath(__file__))
relative_path = "/../.."
path = os.path.abspath(file_dir + relative_path)
sys.path.insert(0, path)

import registry.util as cfg
from data_mgmt.Process import Process

def test_init():
    test_p = Process('MesoObProcStep1')
    assert test_p.process_step == 'https://codes.nws.noaa.gov/StatPP/Method/SfcObs/Mesonet'



if __name__ == "__main__":
    test_init()

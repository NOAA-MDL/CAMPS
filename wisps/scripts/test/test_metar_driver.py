#!/usr/bin/env python
import sys, os
file_dir = os.path.dirname(os.path.realpath(__file__))
relative_path = "/../.."
path = os.path.abspath(file_dir + relative_path)
sys.path.insert(0, path)

import scripts.metar_driver as metar_driver
import metar_to_nc.station
import metar_to_nc.qc_main as qc_main
import pickle

def test_obs_driver():
    metar_driver.main()


def test_qc():
    print "testing qc"
    with open('stations.pkl', 'rb') as input:
        mmk = pickle.load(input)

    qc_main.qc(mmk)

def test_alt():
    with open('stations.pkl', 'rb') as input:
        mmk = pickle.load(input)
        metar_driver.test_alt(mmk)




#test_alt()
test_obs_driver()

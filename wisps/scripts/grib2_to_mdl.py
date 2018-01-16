# Add a relative path
import sys
import os
file_dir = os.path.dirname(os.path.realpath(__file__))
relative_path = "/.."
path = os.path.abspath(file_dir + relative_path)
sys.path.insert(0, path)

import grib2_to_nc.grib2 as grb2


def main():
    grb2.reduce_grib()
    grb2.convert_grib2(
        '/scratch3/NCEPDEV/mdl/Riley.Conroy/output/mdl.gfs47.12.pgrb2')

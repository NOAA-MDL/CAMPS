#!/usr/bin/env python

import sys, os
file_dir = os.path.dirname(os.path.realpath(__file__))
relative_path = "/.."
path = os.path.abspath(file_dir + relative_path)
sys.path.insert(0, path)
import grib2_to_nc.grib2 as grib2
import registry.util as cfg
import numpy as np
import logging
import pdb

def main(control_file=None):
    """Reads grib2 files, changes the map projection
    and grid extent, and packages the gribs into a single grib file.
    Will append to grib file if multiple cycles are called
    """
    if control_file:
        if os.path.exists(control_file):
            control = cfg.read_yaml(control_file)
        else:
            print "control file:", "\""+control_file+"\"", "not found"
            print "Run with valid file, or omit arguments to use the default control:"
            default = cfg.read_grib2_control()
            for k,v in default.iteritems():
                print "#",k,":",v
            return
    else:
        control = cfg.read_grib2_control()
    log_file = control['log']
    debug_level = control['debug_level']
    out_log = None
    if log_file:
        out_log = open(log_file, 'w+')
        sys.stdout = out_log
        sys.stderr = out_log
    try:
        logging.getLogger('').handlers = []
        level = logging.getLevelName(debug_level)
        logging.basicConfig(level=level)
    except:
        print "Logging setup failed"
        raise

    # function that uses wgrib2 to reproject and subset an area
    new_grib_file = grib2.reduce_grib(control)
    grib2.convert_grib2(new_grib_file)

    if log_file:
        out_log.close()

if __name__ == "__main__":
    try:
        main(control_file=sys.argv[1])
    except IndexError:
        main()

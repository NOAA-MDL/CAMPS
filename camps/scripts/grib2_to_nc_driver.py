#!/usr/bin/env python
import sys
import os
import numpy as np
import logging
import pdb

from ..core.data_conversion.grib2_to_nc import grib2 as grib2
from ..registry import util as cfg


def main():
    """Reads grib2 files, changes the map projection
    and grid extent, and packages the gribs into a single grib file.
    Will append to grib file if multiple cycles are called
    """
    import sys
    control_file = None if len(sys.argv) != 2 else sys.argv[1]
    if control_file is not None:
        control = cfg.read_control(control_file)
        logging.info("Control File: " + str(control_file) + " successfully read")
    else:
        raise RuntimeError("A control file must be provided for camps_grib2_to_nc.  Exiting program.")

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

    # function that converts grib2 to netcdf
    grib2.convert_grib2(control)

    if log_file:
        out_log.close()

if __name__ == '__main__':
    main()


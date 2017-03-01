#!/usr/bin/env python
import sys
import os
sys.path.insert(0,os.path.abspath('..'))
import argparse
from convert_tdlpack import *
import pdb

parser = argparse.ArgumentParser(
        description="converts tdlpack files to NetCDF files",
        epilog="NOAA/MDL"
        )
parser.add_argument('files',metavar='filename', type=str,\
        nargs='+', help='A TLDPack filepath')
parser.add_argument('-o','--out', type=str,metavar="dir",\
        nargs=1, help='destination directory for output file to be stored',\
        default="./")
parser.add_argument('-i','--in_dir',type=str,metavar="dir",\
        nargs=1, help='directory that contains input file(s)',\
        default="")
parser.add_argument('-d','--debug',type=str,metavar="dir",\
        nargs=1, help='option to start up pdb on run',\
        default="")
args = parser.parse_args()

file_list = args.files
out_dir = args.out
in_dir = args.in_dir
debug = args.debug

if debug:
    pdb.set_trace()
if type(in_dir) is list:
    in_dir = str(in_dir[0])

for tdl_file in file_list:
    tdl_file = in_dir + str(tdl_file)
    # Decide if it's an oberservation or model tdlpack file
    if is_obs_tdl_file(tdl_file):
        convert_obs(tdl_file)
    else: # its a model file
        convert_model(tdl_file)


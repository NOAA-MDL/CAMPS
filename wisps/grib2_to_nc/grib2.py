#!/usr/bin/env python
from subprocess import call 
from subprocess import Popen
import subprocess
import pygrib



def reduce_grib(filename):
    # Init
    wgrib2 = "/apps/wgrib2/0.1.9.5.1/bin/wgrib2"
    grbindex = "/scratch3/NCEPDEV/nwprod/NWPROD.WCOSS/util/exec/grb2index"
    datadir = "/scratch3/NCEPDEV/mdl/Jason.Levit/data/"
    outpath = "./"
   
    # Grids
    gfs47 = "nps:255.0000:60.0000 210.0000:297:47625.0000 2.8320:169:47625.0000"
    gfs47a = "nps:255.0000:60.0000"
    gfs47b = "210.0000:297:47625.0000"
    gfs47c = "2.8320:169:47625.0000"
    
    gfs95 = "nps:255.0000:60.0000 210.0000:149:95250.0000 2.8320:85:95250.0000"
    gfs95old = "nps:255.0000:60.0000 212.9360:137:95250.0000 6.9870:81:95250.0000"
    gfs80pac = "mercator:20.0000 129.9058:105:80000.0000:209.5289 -19.3309:71:80000.0000:32.0658"
    
    infile = datadir + "gfs.t00z.pgrb2.0p25.f000"
    outfile = outpath + 'mdl.gfs47.00.pgrb2'
    
    PIPE = subprocess.PIPE
    
    non_pcp_cmd = [wgrib2, infile,                       # Specify infile
                   "-i",                                 # Use Inventory
                   "-new_grid_winds", "grid",            # new_grid wind orientation ('grid' or 'earth')
                   "-new_grid_interpolation", "bilinear",# new_grid interpolation ('bilinear','bicubic','neighbor', or 'budget')
                   "-append",                            # add to existing file if exist
                   "-new_grid", gfs47a, gfs47b, gfs47c,  # new_grid to specifications
                   outfile]
    
    command = ' '.join(non_pcp_cmd)
    print command
    
    p1 = Popen(['cat', 'grib200.inv'], stdout=PIPE)
    p2 = Popen(non_pcp_cmd, stdin=p1.stdout)
    p1.stdout.close()
    
    ## OR
    
    #subprocess.check_output("cat grib200.inv | " + command, shell=True)
    
def convert_grib(filename):
    """
    Converts grib file into Wisps Data
    """
    grbs = pygrib.open(filename)
    grbs_info = get_grbs(grbs)
    for grb,info in zip(grbs, gribs_info):
        data = grb.value()


def get_grbs(grbs):
    """
    Parse the grib headers
    """
    names = []
    for grb in grbs:
        grb_info = type('', (), {})()  # Create empty object
        grb = grb.split(':')
        grb_info.name = grb[1]
        grb_info.units = grb[2]
        grb_info.projection = grb[3]
        grb_info.coordinate = grb[4]
        grb_info.fcst_time = grb[5]
        grb_info.model_run = grb[6]
        names.append(grb_info)
    return names




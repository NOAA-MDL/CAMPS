import logging
import yaml
import os
import sys
import subprocess

wgrib2 = "/apps/wgrib2/0.1.9.5.1/bin/wgrib2"
grbindex = "/scratch3/NCEPDEV/nwprod/NWPROD.WCOSS/util/exec/grb2index"
datadir = "/scratch3/NCEPDEV/mdl/Jason.Levit/data/"

gfs47 = "nps:255.0000:60.0000 210.0000:297:47625.0000 2.8320:169:47625.0000"
gfs95 = "nps:255.0000:60.0000 210.0000:149:95250.0000 2.8320:85:95250.0000"
gfs95old = "nps:255.0000:60.0000 212.9360:137:95250.0000 6.9870:81:95250.0000"
gfs80pac = "mercator:20.0000 129.9058:105:80000.0000:209.5289 -19.3309:71:80000.0000:32.0658"

g2 = datadir + "gfs.t00z.pgrb2.0p25.f000"

create_g2_inv_cmd = ([wgrib2,g2])

g2_inv_out = subprocess.check_output(create_g2_inv_cmd)

with open("grib2.inv","w") as f:
    f.writelines(g2_inv_out)
    f.close()

non_pcp_cmd = ([wgrib2,"grib200.inv",g2,"-new_grid_winds","grid","-new_grid_interpolation","bilinear",
               '-append', "-new_grid",gfs47,"mdl.gfs47.00.pgrb2"])

print ' '.join(non_pcp_cmd)

#non_pcp_cmd = ([wgrib2,"-i",g2,"-new_grid_winds","grid","-new_grid_interpolation","bilinear" 
#               "-append","-new_grid",gfs47,"mdl.gfs47.00.pgrb2"])

g2_convert_out = subprocess.check_output(non_pcp_cmd)





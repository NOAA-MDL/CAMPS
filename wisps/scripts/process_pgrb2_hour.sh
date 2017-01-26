#!/bin/bash

grb_control='../registry/grib2_control.yml'
gfs_dir='/scratch3/NCEPDEV/mdl/Jason.Levit/gfs'
convert_script='../grib2_to_nc/grib2.py'
python='/usr/bin/env python'


if [[ ! $1 ]]; then
    echo "provide an model run hour argument"
    exit 1

fi
cd ../grib2_to_nc
pwd
for dir in $gfs_dir/*$1; do 
    echo $dir
    dir=`basename $dir`
    echo $dir
    sed -i -r "s/^datadir.*/datadir : \"\/scratch3\/NCEPDEV\/mdl\/Jason.Levit\/gfs\/$dir\/\"/" $grb_control
    $python $convert_script 
    echo "done"
    read
done

    





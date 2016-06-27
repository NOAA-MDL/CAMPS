#!/bin/sh --login
#
#PBS -l procs=1
#
#PBS -l vmem=8G
#
# -- Specify a maximum wallclock of 1 hour
#PBS -l walltime=1:00:00
#
# -- Specify name under which account a job should run
#PBS -A mdl
#
# -- Set the name of the job, or moab will default to STDIN
#PBS -N linreg

# change directory to the working directory of the job
# Use the if clause so that this script stays portable
#

module use /home/mdlstat/util/modulefiles
module load intel/16.1.150
module load netcdf/4.3.0
module load hdf5/1.8.14
module load contrib anaconda/2.3.0

cd /home/Jason.Levit/src/wisps

/home/Jason.Levit/src/wisps/linreg.py > /home/Jason.Levit/src/wisps/linreg.out

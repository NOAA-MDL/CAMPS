#!/bin/bash

# SET USER WHOSE DIRECTORY IS USED
if [[ -z $WEBUSER ]]; then
    export WEBUSER=$USER
fi
# SET WEB DIRECTORY AND CREATE IF NEEDED
if [[ -z $webdirwisps ]]; then
    export webdirwisps=/usr/project/www/users/wisps
fi
if [[ ! -d $webdirwisps ]]; then
    mkdir -p $webdirwisps
fi 
if [[ ! -d $webdirwisps/pdf ]]; then
    mkdir -p $webdirwisps/pdf
fi 

# RUN BUILD AND PUSH SCRIPT 
echo 
echo
echo "Starting at `date`"
. /home/MDL/$WEBUSER/.bash_profile
cd /home/MDL/$WEBUSER/repositories/wisps/docs
echo "Attepting to pull newest items in the repository..."
git fetch --all
ans=`git diff origin/development -- ./source`
echo "ans="$ans 
#pull from repository and update website if new items 
#in repository
#testing this again...
if [[ ! -z $ans ]]; then
    echo "Checking out origin/development ./source"
    git checkout origin/development ./source
    make clean
    make html
    ./rsynchtml
    make pdf
    cp /home/MDL/$WEBUSER/repositories/wisps/docs/build/pdf/wisps.pdf $webdirwisps/pdf/wisps.pdf
else
    echo "Nothing new to pull"
fi
echo "Ending at `date`"

# TRIM EXISTING LOG
if [[ -f cronlog.log ]]; then
   tail -1000 cronlog.log > tmp.log 
   mv tmp.log cronlog.log
fi 


#!/bin/bash

# SET USER WHOSE DIRECTORY IS USED
if [[ -z $WEBUSER ]]; then
    export WEBUSER=$USER
fi
# SET WEB DIRECTORY AND CREATE IF NEEDED
if [[ -z $webdirwisps ]]; then
    export webdirwisps=/mnt/project/users/wisps
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
. /home/$WEBUSER/.bash_profile
cd /home/$WEBUSER/repositories/wisps/docs
#echo "Attepting to pull newest items in the repository..."
#git fetch --all
#ans=`git diff origin/development -- ./source`
#echo "ans="$ans
#if [[ ! -z $ans ]]; then
#    echo "Checking out origin/development ./source"
#git checkout origin/development ./source
echo "got past checking out branch"
echo "starting clean"
make clean
echo "got past clean"
make html
echo "got past html"
./rsynchtml
echo "got past rsynchtml"
make pdf
echo "got past pdf"
export webdirwispspdf=/mnt/project/users/wisps/pdf/camps.pdf
cp /home/$WEBUSER/repositories/wisps/docs/build/pdf/camps.pdf $webdirwispspdf
#else
#    echo "Nothing new to pull"
#fi
echo "Ending at `date`"

# TRIM EXISTING LOG
if [[ -f cronlog.log ]]; then
   tail -1000 cronlog.log > tmp.log
   mv tmp.log cronlog.log
fi


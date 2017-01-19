#!/bin/bash

if [[ $1 ]]; 
then
    file=$1
    cat $file | awk -F':' '{printf "%s%s%s%s", $4,":", $5, "\n"}'
else
    echo "usage: printVars [file]"
fi

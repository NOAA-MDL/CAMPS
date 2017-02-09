#!/bin/bash


if [[ ! $1 ]]; then
    echo "please provide a filename"
    echo "usage get_dict_values.sh [filename]"
    exit 99
fi
file=$1

cat $file | awk -F: '{if($2){print $2}}'




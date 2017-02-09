#!/bin/bash

function createVar()
{
var=$1
var=`echo $var | sed 's/\"//g'`
has_bounds=`echo $var | egrep "hr"`
echo "$var :"
echo "  data_type : float32"
echo "  dimensions : [] "
echo "  fill_value : \"9999\""
echo "  attribute : "
echo "    OM_procedure : \"()\""
echo "    OM_observedProperty : \"\""
echo "    long_name : \"$var\""
echo "    standard_name : \"$var\""
echo "    units : \"\""
echo "    valid_min : \"\""
echo "    valid_max : \"\""
if [[ $has_bounds ]]; then
echo "    bounds : \"time_bounds\""
fi

}


if [[ ! -t 0 ]]; then
   while read -r var; do
       createVar $var
   done
   exit

fi
if [[ ! $1 ]]; then
    echo "no input var. Exiting"
    echo "Usage create_default_variable.sh [name]
    exit 0
fi

createVar $1




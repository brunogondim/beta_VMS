#!/bin/bash

# parse the space string in array
spo=$1
OIFS=$IFS
IFS=' '
spo_array=($spo)
IFS=$OIFS

# inside container
python /root/shoot_detection/main final.py ${spo_array[1]} ${spo_array[2]} ${spo_array[3]}

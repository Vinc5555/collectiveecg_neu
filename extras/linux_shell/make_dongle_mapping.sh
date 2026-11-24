#! /bin/bash 
# Script to create the dongle mapping
#
# Usage: 
# bash make_dongle_mapping.sh
#
# Authors: 
#   - Victor Chung, 
#   - Julien Karadayi
#   - Camille Straboni

dongle_list=$(mktemp) # create temporary file
hciconfig > $dongle_list # store dongle info

echo "updating dongle mapping at $(date +%T+%N)" >> experiment.log

python parse_dongleList.py -i $dongle_list -o dongle_mapping.csv


#! /bin/bash 
# Script to launch stream on one polar device.
# Needs make_dongle_mapping.sh to be run first.
# Usage: 
# bash launcher.sh A01
# 
# Authors: 
#   - Victor Chung, 
#   - Julien Karadayi
#   - Camille Straboni

# Inputs
POLAR_ID=$1

#if [[ ! -f dongle_mapping.csv ]]; then
#    echo "No mapping found for USB bluetooth dongle.\n"
#    echo "Please run bash make_dongle_mapping.sh"
#    exit 1
#fi

# Making dongle mapping
dongle_list=$(mktemp) # create temporary file
hciconfig > $dongle_list # store dongle info

echo "updating dongle mapping at $(date +%T+%N)" >> experiment.log

python parse_dongleList.py -i $dongle_list -o dongle_mapping.csv

# Launching recording on polar device
echo "launching device $POLAR_ID at $(date +%T+%N)" >> experiment.log

python heart_sync/heart_sync.py -p $POLAR_ID -c config.csv -dm dongle_mapping.csv &


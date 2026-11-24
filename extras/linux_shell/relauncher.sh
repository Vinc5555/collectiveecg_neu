#! /bin/bash 
# Script to relaunch stream on one polar device, in case of deconnection.
# Needs make_dongle_mapping.sh to be run first.
#
# Usage: 
# bash relauncher.sh A01
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

echo "relaunching (quit trigger + launch) device $POLAR_ID at $(date +%T+%N)" >> experiment.log
python trigger_sender.py -p $POLAR_ID -c config.csv -q
sleep 5
python heart_sync/heart_sync.py -p $POLAR_ID -c config.csv -dm dongle_mapping.csv &


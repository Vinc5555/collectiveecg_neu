#! /bin/bash 
# Script to launch stream on one polar device.
# Needs make_dongle_mapping.sh to be run first.
#
# Usage: 
# bash trigger.sh A01
# 
# Authors: 
#   - Victor Chung, 
#   - Julien Karadayi
#   - Camille Straboni

# Inputs
POLAR_ID=$1
QUIT=$2

echo "sending trigger to $POLAR_ID (quit option: $QUIT) at $(date +%T+%N)" >> experiment.log

python trigger_sender.py -p $POLAR_ID -c config.csv $QUIT

#! /bin/bash 
# Print the computer time and the android time (using adb).
# Used to measure the time difference between both devices.
# 
# Authors: 
#   - Victor Chung, 
#   - Julien Karadayi

echo "computer time $(date +%T+%N)"; echo "android time $(adb shell 'date +%T+%N')" >> experiment.log

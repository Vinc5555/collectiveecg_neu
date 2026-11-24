.. _introduction:

============
Introduction
============

Features
========

The Heart Sync package enables acquiring electrocardiogram (ECG) and accelerometer (ACC) data from one or multiple Polar H10 sensors simultaneously:
* handle a single or multiple simultaneous connections to Polar H10 sensors
* save ECG and ACC data in a local data file
* visualise data in real time
* include event markers in the recorded data
* resample recorded data at a fixed sampling rate 

About the Polar H10
===================

Description
-----------
The Polar H10 is a commercially-available wearable chest strap that records ECG  via three skin-contact sensors and ACC. It is positioned on the lower part of the sternum beneath the pectoral region. 
The validity of the Polar H10 in measuring HR and HR variability has been established both at rest and during physical exercise by comparing it to gold-standard ECG systems
Please read `Polar documentation`_ for more information.

.. _Polar documentation: https://github.com/polarofficial/polar-ble-sdk/blob/master/technical_documentation/online_measurement.pdf

Data samples
------------
- The raw data are transmitted from the Polar H10 sensor by packets of 73 samples (ECG) 36*3 samples (ACC) + 1 timestamp.
- The timestamp in each packet corresponds to the last sample of the packet.
- The raw values are in mV (ECG) and mG (ACC).
- The sampling rate for ECG is approximately 130hz but has a ±2% variation.
- The sampling rate for ACC is approximately 64hz.

Timestamps
----------
- For thorough explanations of the time system of the Polar H10, see `this document`_ 
- The timestamps are in nanoseconds, with epoch time at 01/01/2000
- Once the polar H10 device shuts down, its time is reset to 2019-01-01T00:00:00 
- The "TimeSetter" Android app can be used to set the correct time (see our User Guide)

.. _this document: https://github.com/polarofficial/polar-ble-sdk/blob/39c809ab4a3398d3ea88ff8a0cc6f6d44cd58bda/technical_documentation/TimeSystemExplained.md


Implementation details
======================

Bleakheart
----------
To connect to the belt through python, start and stop the stream, and to decode the ECG and accelerometer data, we use the bleackheart python package. 
Please read `bleakheart's documentation`_ doc for more information.

.. _bleakheart's documentation: https://github.com/fsmeraldi/bleakheart 

Bleak and Asyncio
--------------------
- The bluetooth connection is handled by Bleak, which works asyncronously, relying on the asyncio library.
- With Bleak/Asyncio, each function must be defined as "async". To run them, you need to call them through asyncio

Producer/Consumer Development Pattern
-------------------------------------
- The implementation follows the bleakheart examples and uses the Producer/Consumer design pattern.
- The "producer" receives the ECG or ACC raw data and put them in a queue.
- The "consumer" takes data from the queue and writes them in the output file.

Event Marker and Quit Triggers
------------------------------
- For each polar device, the python listens on two port defined by the user. 
- On the first port port, it receives triggers that are added to the output data (1 when trigger, 0 otherwise). 
- On the second port, it receives triggers that stops the ecg stream.


References
==========
1. Polar H10 User Manual: Polar H10 Heart Rate Sensor. Available online: https://support.polar.com/e_manuals/h10-heart-rate-sensor/polar-h10-user-manual-english/introduction.htm (accessed on 12 September 2025).
2. Smeraldi, F. BleakHeart, version 0.1.3. 2025. https://github.com/fsmeraldi/bleakheart
3. Schaffarczyk, M.; Rogers, B.; Reer, R.; Gronwald, T. Validity of the Polar H10 Sensor for Heart Rate Variability Analysis during Resting State and Incremental Exercise in Recreational Men and Women. Sensors 2022, 22, 6536. https://doi.org/10.3390/s22176536

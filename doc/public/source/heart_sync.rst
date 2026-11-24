.. _heart_sync:

==========
Heart Sync
==========

* The Heart Sync package is used to stream raw ECG data with a sampling 
  rate of 130 HZ ± 2%

Installation
============

* In the package's root folder, run:
    - pip install ./

* The requirements are automatically installed when installing the package. The list of requirements is :
    - bleak to handle the bluetooth connection,
    - asyncio to handle the bluetooth connection, which works asynchronously,
    - bleakheart, a package that handles sending/receiving messages to a Polar H10 devices,
    - ipdb, a package useful for debugging.

POLAR H10 
=========

Connection, data stream, data decoding
--------------------------------------

- To connect to the belt through python, start and stop the stream,
  and to decode the ECG and accelerometer data, we use the 
  bleakheart python package. Please read `Polar documentation`_  and 
  `bleakheart`_  doc for more information

.. _Polar documentation: https://github.com/polarofficial/polar-ble-sdk/blob/master/technical_documentation/online_measurement.pdf

.. _bleakheart: https://github.com/fsmeraldi/bleakheart

ECG data
--------
1/ Data packets
---------------

- The raw ECG Data is sent by packets of 73 samples + 1 timestamp.

- The timestamp in each packet corresponds to the last sample of the packet

- The raw ECG values are in mV.

2/ Timestamps
-------------

- See `this document` for thorough explanations of how the time system works in a polar H10 device.

- The timestamps are in nanoseconds, with epoch time at 01/01/2000

- Once the polar H10 device shuts down, its time is reset to 2019-01-01T00:00:00 

- The "TimeSetter" Android app can be used to set the correct time, using the "setLocalTime" method from Polar's SDK. This android app follows the recommandation from [this github issue](https://github.com/polarofficial/polar-ble-sdk/issues/580) :
    - Connect to the Polar H10 device
    - wait 7500s for service discovery to end
    - wait until the time is exactly at the second
    - send setLocalTime to the device

.. _this document: https://github.com/polarofficial/polar-ble-sdk/blob/39c809ab4a3398d3ea88ff8a0cc6f6d44cd58bda/technical_documentation/TimeSystemExplained.md
.. _this github issue: https://github.com/polarofficial/polar-ble-sdk/issues/580
3/ Sampling Rate
----------------

- The sampling is approximately 130hz but has a +-2% variation

- resampler.py can be used to force the raw ecg signal to a fixed sampling rate of exactly 130 HZ: 
    - we estimate the sampling rate for each data packet by taking the time 
      between previous and current timestamp (we assume the sampling rate to be
      constant for one packet and the timestamp to be correct)
    - we use a spline resampling to resample the signal to a fixed 130Hz


Implementation Details
----------------------

1/ Trigger and Quit Signal
--------------------------

- For each polar device, the python listens on two port defined by the user. On the first port port, it receives triggers that are added to the output data (1 when trigger, 0 otherwise). On the second port, it receives triggers that stops the ecg stream.

2/ Bleak and Asyncio
--------------------

- The bluetooth connection is handled by Bleak, which works asyncronously, relying on the asyncio library.

- With Bleak/Asyncio, each function must be defined as "async". To run them, you need to call them through asyncio

3/ Producer/Consumer Development Pattern
----------------------------------------

- The implementation follows the bleakheart examples and uses the Producer/Consumer design pattern.

- The "producer" receives the ECG (or accelerometer) raw data and put them in a queue

- The "consumer" takes data from the queue and writes them in the output file.

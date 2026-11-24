.. _getting-started:

===============
Getting Started
===============

Requirements
============

* Polar SDK:
* Bluetooth:
* Python:
* Python packages
    - bleak to handle the bluetooth connection,
    - asyncio to handle the bluetooth connection, which works asynchronously,
    - bleakheart, a package that handles sending/receiving messages to a Polar H10 devices,
    - ipdb, a package useful for debugging.

The requirements are automatically installed when installing the package. 


Installation
============

You can download the latest version from the `project repository <https://gitlab.com/jkara/collectiveecg>`_.
In the package's root folder, run::

  pip install ./


Quick start
===========

1. Prepare a configuration file (see config.csv for an example).

1.bis If your computer is running Windows11, you first need to pair your sensor manually. 
To do this, make sure the Polar device is turned on, then
    
    - go to Settings > Devices > Bluetooth & other devices,
    - select Add Bluetooth or other device
    - select the Polar device with the correct Serial number

2. Connects to the sensor via Bluetooth and start the stream - specify at the minimum the name of the configuration file and the sensor ID::

    python heart_sync/heart_sync.py -c MyConfigFile.csv -p MySensorID

3. Optionnally, visualise data in real time

    python ecg_visualiser.py

4. Optionnally, mark an event of interest
    
    python trigger_sender.py -c config.csv -p MySensorID

5. Stop the stream and disconnects from the sensor

    python trigger_sender.py -c config.csv -p MySensorID -q
  


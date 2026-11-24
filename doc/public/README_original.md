Heart Sync
==========

* Python code to stream ECG measurements for a polar H10 belt connected through bluetooth.

* The code will use the bleakheart library to stream ECG data from 1 belt.

Requirements
------------

* bleak
    - manage bluetooth connection in python

* asyncio
    - bleak requires asyncio, asynchronous context manager

* bleakheart
    - connect to polar H10 belt and stream ECG data

Known Issues
------------

* In the bleakheart library, and offset is added to the timestamp to sync it with 
  the computer. For our use case, we needi the exact timestamp from the polar device, 
  so we need to remove the timestamp offset in bleakheart (lines 383-387 in core.py)

* The polar H10 sampling rate is unstable, but variations are small, sampling rate 
  should be around 129.9 hz.
    - use resampler.py to force sampling rate to be at 130hz

* Sometimes the polar H10 sensors stays connected to android even after closing the app.
  In such cases, shutdown phone's bluetooth to force deconnection.

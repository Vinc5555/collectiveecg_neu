# HEART SYNC

* The Heart Sync package is used to stream raw ECG data with a sampling 
  rate of (approximately) 130 HZ

## Installation
- #TODO add requirements

- pip install yourself

## POLAR H10 

### connection, data stream, data decoding

- To connect to the belt through python, start and stop the stream,
  and to decode the ECG and accelerometer data, we use the 
  bleackheart python package. Please read Polar documentation and 
  bleakheart doc for more information # TODO ADD links

### ECG data

#### Data packets

- The raw ECG Data is sent by packets of 73 samples + 1 timestamp.

- The timestamp in each packet corresponds to the last sample of the packet

- The raw ECG values are in mV.

#### Timestamps

- The timestamps are in nanoseconds, with epoch time at 01/01/2000

- Once the polar H10 device shuts down, its time is reset to #TODO add date, 2019?

- The "TimeSetter" Android app can be used to set the correct time, using the "setLocalTime" method from Polar's SDK. This android app follows the recommandation from    #TODO add github link :
    - Connect to the Polar H10 device
    - wait 7500s for service discovery to end
    - wait until the time is exactly at the second
    - send setLocalTime to the device

#### Sampling Rate

- The sampling is approximately 130hz but has a +-5% variation #TODO check + add temp ?

- resampler.py can be used to force the raw ecg signal to a fixed sampling rate of exactly 130 HZ: 
    - it estimates the sampling rate for each data packet by taking the time 
      between previous and current timestamp (we assume the sampling rate to be
      constant for one packet)
    - it uses a spline resampling to resample the signal to a fixed 130Hz


### Implementation Details

#### Trigger and Quit Signal

- The Heart Sync python package uses UDP to receive triggers. 

- For each polar device, the python listens on two port. On one port, it receives triggers that are added to the output data (1 when trigger, 0 otherwise). On another port, it receives triggers that stops the ecg stream.

#### Bleak and Asyncio

- The bluetooth connection is handled by Bleak, which works asyncronously, relying on the asyncio library.

- With Bleak/Asyncio, each function must be defined as "async". To run them, you need to call them through asyncio

#### Producer/Consumer Development Pattern

- The implementation follows the bleakheart examples and uses the Producer/Consumer design pattern.

- The "producer" receives the ECG (or accelerometer) raw data and put them in a queue

- The "consumer" takes data from the queue and writes them in the output file.

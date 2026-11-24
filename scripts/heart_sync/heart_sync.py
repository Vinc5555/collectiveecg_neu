import os
import sys
import time
import asyncio

import argparse
import threading
import socketserver  # we use the socketsever module that comes with python3

from datetime import datetime
from bleak import BleakScanner, BleakClient
from bleakheart import PolarMeasurementData

# --- Ordner (collectiveecg_neu) -----------------------------------------
# Alle Pfade relativ zum Projektordner, egal aus welchem Ordner gestartet wird.
# Messungen  -> data/lab_internal/raw/
# Logdateien -> data/lab_internal/logs/ (experiment.log, streaming.csv)
PROJEKT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW_DIR = os.path.join(PROJEKT, "data", "lab_internal", "raw")
LOG_DIR = os.path.join(PROJEKT, "data", "lab_internal", "logs")
os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)
EXPERIMENT_LOG = os.path.join(LOG_DIR, "experiment.log")
STREAMING_CSV = os.path.join(LOG_DIR, "streaming.csv")
# -------------------------------------------------------------------------

"""
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.

Copyright (C) 2023 Fabrizio Smeraldi <fabrizio@smeraldi.net>
"""

""" ECG acquisition using an asynchronous queue - producer/consumer model
    Copied from bleakheart example
"""


class UDPHandler(socketserver.DatagramRequestHandler):

    def handle(self):

        # for line terminated massages
        # msgRecvd = self.rfile.readline().strip()
        print("received message - stopping stream")

        def server_shutdown(server):
            server.shutdown()

        threading.Thread(target=server_shutdown, kwargs={"server": self.server}).start()
        # with receive buffer - reads max 1024 bytes
        # rec_bytes = self.request.recv(1024)
        # your processing here


class EcgProducer:
    """Add ECG data from one polar h10 device to a queue.
    Based on producer/consumer design pattern.
    """

    def __init__(self, polar_sn, polar_id):
        self.quitclient = asyncio.Event()
        self.polar_sn = polar_sn  # polar h10 serial number
        self.polar_id = polar_id
        self.stream_flag = False
        self.stop_stream = False
        self.stream_ended = False

    def udp_handler(self, loop=None, port=5354):
        """UDP socket listening on port for signal to stop ECG stream."""
        # using logger results in an error..
        print(f"listening on port {port}")
        listen_addr = ("0.0.0.0", port)
        # socketserver.UDPServer("0.0.0.0", port)
        # with allowing to reuse the address we dont get into problems
        # running it consecutively sometimes
        socketserver.UDPServer.allow_reuse_address = True

        serverUDP = socketserver.UDPServer(listen_addr, UDPHandler)
        serverUDP.serve_forever()
        print("stopping stream")
        self.stop_stream = True
        if loop is None:
            self.quitclient.set()  # we are in the event loop thread
        else:
            # we are in a separate thread - call set in the event loop thread
            loop.call_soon_threadsafe(self.quitclient.set)

    def disconnected_callback(self, client):
        """Called by BleakClient if the sensor disconnects"""
        print(f"Sensor {self.polar_id} disconnected")
        self.stream_ended = True
        self.quitclient.set()  # causes the ble client task to exit

    async def connect_to_sn(self, devices):
        """Scan bluetooth devices and find polar devices by their Serial Numbers"""
        # devices = await BleakScanner.discover()
        polar_devices = [
            dev for dev in devices if dev.name and "polar" in dev.name.lower()
        ]
        print(
            f"Bluetooth scanning found {len(devices)} devices, {len(polar_devices)} polar device"
        )
        # print(devices)
        # print(polar_devices)
        # for SN in polar_list:

        device = [dev for dev in polar_devices if self.polar_sn in dev.name]
        # print(device)
        if len(device) == 0:
            # logger.error(f"failure to find device")
            print("failure to find device")
        return device

    # async def run_multiple_devices(self, device, queue):
    #    """connect to multiple polar devices and stream ECG data
    #    Design pattern : Multiple producers - 1 consumer?

    #    """

    # async def run_ble_client(self, device, queue, logger, port, dongle_name):
    async def run_ble_client(
        self, device, polar_id, ecg_queue, acc_queue, port, dongle_name
    ):
        """This task connects to the BLE server (the heart rate sensor)
        identified by device, starts ECG notification and pushes the ECG
        data to the queue. The tasks terminates when the sensor disconnects
        or the user hits enter."""
        ## Flag stream launched
        # self.stream_flag = False
        # listen_addr = ("0.0.0.0", 5354)

        ## with allowing to reuse the address we dont get into problems running it consecutively sometimes
        # socketserver.UDPServer.allow_reuse_address = True

        ## register our class
        # serverUDP = socketserver.UDPServer(listen_addr, UDPHandler)
        self.quitclient = asyncio.Event()

        # while True and not self.stop_stream:
        print("scanning for device")
        found_device = await BleakScanner.find_device_by_address(device.address)

        if found_device is None:
            # logger.warning("no device found, wait 5s then scan again")
            print("no device found, wait 5s then scan again")

            await asyncio.sleep(5)

        try:
            # logger.info(f"Connecting to {device}...")
            print(f"Connecting to {device}...")
            # the context manager will handle connection/disconnection for us

            async with BleakClient(
                device,
                disconnected_callback=self.disconnected_callback,
                adapter=dongle_name,
            ) as client:
                # logger.info(f"Connected: {client.is_connected}")
                print(f"Connected: {client.is_connected}")

                # create the Polar Measurement Data object; set queue for
                # ecg data
                # pmd = PolarMeasurementData(client, ecg_queue=queue)
                pmd = PolarMeasurementData(
                    client, ecg_queue=ecg_queue, acc_queue=acc_queue
                )

                # ask about ECG settings
                if not self.stream_flag:
                    ecg_settings = await pmd.available_settings("ECG")
                    # logger.info
                    print("Request for available ECG settings returned the following:")
                    for k, v in ecg_settings.items():
                        # logger.info(f"{k}:\t{v}")
                        print(f"{k}:\t{v}")
                    acc_settings = await pmd.available_settings("ACC")
                    # logger.info
                    print("Request for available ECG settings returned the following:")
                    for k, v in acc_settings.items():
                        # logger.info
                        print(f"{k}:\t{v}")

                # press enter to stop streaming
                loop = asyncio.get_running_loop()
                # Set the loop to call keyboard_handler when one line of input is
                # ready on stdin
                # loop.add_reader(sys.stdin, self.keyboard_handler)
                # loop.add_reader(sys.stdin, self.udp_handler)

                # else:
                #    # run keyboard_handler in a daemon thread
                threading.Thread(
                    target=self.udp_handler,
                    kwargs={"loop": loop, "port": port},
                    daemon=True,
                ).start()

                # start notifications; bleakheart will start pushing
                # data to the queue we passed to PolarMeasurementData
                # start streaming if not already done
                # if not self.stream_flag :
                (err_code, err_msg, _) = await pmd.start_streaming("ECG")
                (err_code, err_msg, _) = await pmd.start_streaming("ACC")
                with open(EXPERIMENT_LOG, "a") as xp_fout:
                    xp_fout.write(
                        f"ecg & acc stream start at {datetime.fromtimestamp(time.time()).strftime('%A, %B %d, %Y %H:%M:%S')} for {polar_id}\n"
                    )

                self.stream_flag = True
                self.stream_ended = False
                if err_code != 0:
                    # logger.error
                    print(f"PMD returned an error: {err_msg}")
                    sys.exit(err_code)
                # else: # disconnected - try to stop and restart stream
                # this task does not need to do anything else; wait until
                # user hits enter or the sensor disconnects
                await self.quitclient.wait()

                # no need to stop notifications if we are exiting the context
                # manager anyway, as they will disconnect the client; however,
                # it's easy to stop them if we want to
                if client.is_connected and self.stop_stream:
                    await pmd.stop_streaming("ECG")
                    self.stream_flag = False
                # if ADD_READER_SUPPORT:
                # loop.remove_reader(sys.stdin)
                # signal the consumer task to quit
                ecg_queue.put_nowait(("QUIT", None, None, None))
            self.stream_ended = True

        except:
            # logger.warning
            self.stream_ended = True
            print(f"lost connection for {polar_id}")


async def run_consumer_task(
    # queue,
    polar_id,
    ecg_queue,
    acc_queue,
    stream_ended,
    output,
    stream_not_started,
    trigger_port=5355,
):
    """This task retrieves ECG data from the queue and does
    all the processing. You should ensure it returns control before
    the next frame is received from the sensor.

    In this example, we simply prints decoded ECG data as it
    is received"""
    print("After connecting, will print ECG data in the form")
    print("('ECG', tstamp, [s1,S2,...,sn])")
    print("where samples s1,...sn are in microVolt, tstamp is in ns")
    print("and it refers to the last sample sn.")
    trigger = 0
    trigger_ts = 0
    trigger_flag = False

    # --- Timer-Anzeige (collectiveecg_neu) ---------------------------------
    # Zeigt im Terminal die Aufnahmedauer und die Marker. Läuft in einem
    # eigenen Hintergrund-Thread und berührt die Datenaufnahme nicht.
    anzeige = {"start": None, "marker": 0, "letzter": None, "aktiv": True}

    def zeit_text(sekunden):
        h, rest = divmod(int(sekunden), 3600)
        m, s = divmod(rest, 60)
        return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"

    def timer_anzeige():
        while anzeige["aktiv"]:
            if anzeige["start"] is not None:
                text = f"Aufnahme läuft: {zeit_text(time.time() - anzeige['start'])}"
                text += f"  |  Marker: {anzeige['marker']}"
                if anzeige["letzter"] is not None:
                    text += f" (zuletzt bei {zeit_text(anzeige['letzter'])})"
                print("\r" + text + "   ", end="", flush=True)
            time.sleep(1)
    # -------------------------------------------------------------------------

    class TriggerHandler(socketserver.DatagramRequestHandler):

        def handle(self):

            # for line terminated massages
            # msgRecvd = self.rfile.readline().strip()
            # Meldung korrigiert (Original: "received message - stopping stream",
            # obwohl hier nur ein Marker gesetzt wird)
            if anzeige["start"] is not None:
                anzeige["marker"] += 1
                anzeige["letzter"] = time.time() - anzeige["start"]
            print(f"\nMarker {anzeige['marker']} empfangen")

            # def server_shutdown(server):
            #    server.shutdown()

            # threading.Thread(
            #    target=server_shutdown, kwargs={"server": self.server}
            # ).start()
            # with receive buffer - reads max 1024 bytes
            # rec_bytes = self.request.recv(1024)
            # your processing here
            nonlocal trigger
            nonlocal trigger_ts
            trigger = 1
            trigger_ts = time.time()

    def trigger_handler(loop=None, serverUDP=None, port=5355):
        """UDP socket listening on port for signal to stop ECG stream."""
        # using logger results in an error..
        print(f"listening on port {port}")

        # with allowing to reuse the address we dont get into problems
        # running it consecutively sometimes
        socketserver.UDPServer.allow_reuse_address = True

        # serverUDP = socketserver.UDPServer(listen_addr, TriggerHandler)
        serverUDP.serve_forever()
        print("stopping stream")

    loop = asyncio.get_running_loop()
    listen_addr = ("0.0.0.0", trigger_port)

    trigger_server = socketserver.UDPServer(listen_addr, TriggerHandler)

    threading.Thread(
        target=trigger_handler,
        kwargs={"loop": loop, "serverUDP": trigger_server, "port": trigger_port},
        daemon=True,
    ).start()
    while True and not stream_ended:
        # frame = await queue.get()
        ecg_frame = await ecg_queue.get()
        acc_frame = await acc_queue.get()
        if ecg_frame[0] == "QUIT":  # intercept exit signal
            # if ecg_frame[0] == "QUIT":
            break
        # print(len(frame[2]))
        # print(frame)
        if stream_not_started:  # record time of first packet
            stream_not_started = False
            # Timer starten (nur Anzeige)
            anzeige["start"] = time.time()
            threading.Thread(target=timer_anzeige, daemon=True).start()
            ecg_output = os.path.join(RAW_DIR, str(int(time.time())) + "_ecg_" + output)
            acc_output = os.path.join(RAW_DIR, str(int(time.time())) + "_acc_" + output)

            # Check if file already exists, and replace line if polar id is already in it
            if os.path.isfile(STREAMING_CSV):
                with open(STREAMING_CSV, "r") as stream_out:
                    file_in = []
                    found_polar = False
                    for line in stream_out.readlines():
                        if line.startswith(f"{polar_id}"):
                            found_polar = True
                            file_in.append(f"{polar_id},{ecg_output}\n")
                        else:
                            file_in.append(line)
                with open(STREAMING_CSV, "w") as stream_out:
                    for line in file_in:
                        stream_out.write(line)
                    if not found_polar:
                        stream_out.write(f"{polar_id},{ecg_output}\n")

            else:
                with open(STREAMING_CSV, "w") as stream_out:
                    stream_out.write(f"{polar_id},{ecg_output}\n")

        with open(ecg_output, "a") as ecg_fout, open(acc_output, "a") as acc_fout:
            if trigger and not trigger_flag:
                trigger_flag = True
            computer_timestamp = time.time()
            ecg_fout.write(
                ",".join(
                    [str(ecg_frame[1])]
                    + [str(computer_timestamp)]
                    + [str(trigger)]
                    # + [str(trigger_ts)]
                    # + [str(val) for val in frame[2]]
                    + [str(val) for val in ecg_frame[2]]
                )
                + "\n"
            )
            acc_fout.write(
                ",".join(
                    [str(ecg_frame[1])]
                    + [str(computer_timestamp)]
                    + [str(trigger)]
                    # + [str(trigger_ts)]
                    # + [str(val) for val in frame[2]]
                    + [str(val) for val in acc_frame[2]]
                )
                + "\n"
            )

            if trigger and trigger_flag:
                trigger = 0
                trigger_ts = 0
                trigger_flag = False
            #    def server_shutdown(server):
            # server.shutdown()

        # threading.Thread(target=server_shutdown, kwargs={"server": self.server}).start()
    # Timer-Anzeige beenden
    anzeige["aktiv"] = False
    print()
    # Add exiting timestamp
    with open(EXPERIMENT_LOG, "a") as xp_fout:
        xp_fout.write(
            f"ecg & acc stream stop at {datetime.fromtimestamp(time.time()).strftime('%A, %B %d, %Y %H:%M:%S')} for {polar_id}\n"
        )
    trigger_server.shutdown()


def read_config(polar_id, config):
    """Read configuration file and output config data.
    Expected format for the configuration file is:

    POLAR_ID,POLAR_SERIALNUMBER,QUIT_PORT,TRIGGER_PORT,OUTPUT_FILE,DONGLE_MAC

    Returns
    -------
    sn: string
        the polar device serial number to which we connect
    port: int
        the port which is used to stop the stream
    trigger_port: int
        the port which is used to write a trigger
    output: string
        the name used for the output file
    dongle_mac: string
        the mac address of the dongle to use for connection
    """
    with open(config, "r") as fin:
        for line in fin.readlines():
            if line.startswith(polar_id):
                _, sn, port, trigger_port, output, dongle_mac = line.strip().split(",")

    return sn, int(port), int(trigger_port), output, dongle_mac


async def main():
    #  parse arguments
    parser = argparse.ArgumentParser(description="heartSync")

    # input output arguments
    parser.add_argument(
        "-p", "--polar_id", type=str, help="ID of the polar device used"
    )

    parser.add_argument(
        "-c",
        "--config",
        type=str,
        help="csv file containing the config used for this polar id",
    )

    parser.add_argument(
        "-dm",
        "--dongle_mapping",
        type=str,
        help="path to the file"
        "containing the mapping from dongle name to its mac address",
    )

    args = parser.parse_args()
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit()

    # Get configuration
    polar_sn, port, trigger_port, output, dongle_mac = read_config(
        args.polar_id, args.config
    )

    if args.dongle_mapping is not None:
        with open(args.dongle_mapping, "r") as fin:
            # mac2dongle = {}
            for line in fin.readlines():
                if dongle_mac in line:
                    dongle_name, _ = line.strip().split(",")
                # mac2dongle[daddress] = dname
    else:
        # mac2dongle = None
        dongle_name = None

    # define logger
    print("Scanning for BLE devices")

    # polar_sn = args.serial_number
    devices = await BleakScanner.discover(adapter=dongle_name)
    ecgprod = EcgProducer(polar_sn, args.polar_id)
    polar_devices = await ecgprod.connect_to_sn(devices)

    # if len(devices) == 0:
    #    logger.error("Polar device not found.")
    #    sys.exit(-4)
    # the queue needs to be long enough to cache all the frames, since
    # PolarMeasurementData uses put_nowait
    # ecgqueues = [asyncio.Queue() for dev in polar_devices] # create 1 queue per device

    ecgqueue = asyncio.Queue()
    accqueue = asyncio.Queue()  #

    stream_not_started = True
    # while not ecgprod.stop_stream:  # try reconnection after connection is lost
    producer = ecgprod.run_ble_client(
        polar_devices[0],
        args.polar_id,
        ecgqueue,
        accqueue,
        port,
        dongle_name,
    )

    consumer = run_consumer_task(
        args.polar_id,
        ecgqueue,
        accqueue,
        ecgprod.stream_ended,
        output,
        stream_not_started,
        trigger_port,
    )
    await asyncio.gather(producer, consumer)

    print("Bye.")


if __name__ == "__main__":
    # execute the main coroutine
    asyncio.run(main())

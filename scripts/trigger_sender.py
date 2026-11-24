import sys
import time
import socket
import argparse

from datetime import datetime
import os

# --- Ordner (collectiveecg_neu): Log liegt in data/lab_internal/logs/ ---
PROJEKT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(PROJEKT, "data", "lab_internal", "logs")
os.makedirs(LOG_DIR, exist_ok=True)
EXPERIMENT_LOG = os.path.join(LOG_DIR, "experiment.log")


def send_trigger(polar_id, port, trig_type):
    UDP_IP = "127.0.0.1"

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Internet  # UDP

    with open(EXPERIMENT_LOG, "a") as xp_fout:
        xp_fout.write(
            f"{trig_type} sent at {datetime.fromtimestamp(time.time()).strftime('%A, %B %d, %Y %H:%M:%S')} to {polar_id}\n"
        )
    for p in port:
        sock.sendto("triggering!".encode(), (UDP_IP, p))


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
        if polar_id == "ALL":
            ports = []
            trigger_ports = []

        for line_idx, line in enumerate(fin.readlines()):
            if line_idx == 0:
                continue  # skip header

            if polar_id != "ALL" and line.startswith(polar_id):
                _, _, port, trigger_port, _, _ = line.strip().split(",")
                return [int(port)], [int(trigger_port)]

            elif polar_id == "ALL":
                _, _, port, trigger_port, _, _ = line.strip().split(",")
                ports.append(int(port))
                trigger_ports.append(int(trigger_port))
        return ports, trigger_ports


def main():
    parser = argparse.ArgumentParser(description="send trigger via UDP")

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
        "-q",
        "--quit",
        action="store_true",
        help="if enabled, the trigger will stop the stream, "
        "otherwise it just adds the trigger to the output.",
    )

    args = parser.parse_args()
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit()

    # Get configuration
    port, trigger_port = read_config(args.polar_id, args.config)

    # send trigger
    # Log-Texte korrigiert (im Original vertauscht): -q = Stopp, sonst Marker
    if args.quit:
        send_trigger(args.polar_id, port, "quit trigger")
    else:
        send_trigger(args.polar_id, trigger_port, "trigger")


if __name__ == "__main__":
    main()

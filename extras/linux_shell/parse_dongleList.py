import argparse

parser = argparse.ArgumentParser(description="k edge swap")

# input output arguments
parser.add_argument(
    "-i",
    "--dongle_list",
    type=str,
    help="path to the file containing the output of hciconfig",
)
parser.add_argument(
    "-o",
    "--dongle_mapping",
    type=str,
    help="path to the output csv containing the name of the dongle as first column, and its mac address as second column",
)

args = parser.parse_args()

with open(args.dongle_list, "r") as fin:
    dongle2mac = dict()
    for line in fin.readlines():
        if line.startswith("hci"):
            dongle_name = line.strip().split(":")[0]
        elif "BD Address" in line:
            mac_address = line.strip().split(" ")[2]
            dongle2mac[dongle_name] = mac_address

print(dongle2mac)
with open(args.dongle_mapping, "w") as fout:
    for dongle_name, mac_address in dongle2mac.items():
        fout.write(f"{dongle_name},{mac_address}\n")

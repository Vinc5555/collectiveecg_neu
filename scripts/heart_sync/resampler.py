import time
import logging
import argparse
import scipy

"""
Tool to preprocess ECG Data measured using a Polar H10 device.
ECG Data from the device has small variations of the sampling rate, 
this tool estimates the sampling rate using the timestamps, and resamples
the data to 130hz for each packet of 73 data points.

"""


def read_input_ecg(csv):
    """Read data measured using the collectiveHeart python package.
    Expected format is a csv with 75 columns :
        packet timestamp, trigger, ecg[0], ecg[1] ..., ecg[72]
    where ecg[0]...ecg[72] is a packet of samples as sent by the Polar H10 device,
    and 'packet timestamp' is the timestamp sent by the device.
    """
    with open(csv, "r") as fin:
        timestamps = []
        raw_ecg = []
        trig_flag = False
        for line in fin.readlines():
            vals = line.strip().split(",")
            trig = int(vals[1])
            if trig == 1:
                trig_flag = True
            if trig_flag:
                raw_ecg += [int(v) for v in vals[2:]]
                timestamps.append(int(vals[0]))

    return timestamps, raw_ecg


def resample_packets(timestamps, raw_ecg):
    """For each packet of 73 ECG samples, estimate the sampling rate using the timestamps,
    and resample to a fixed 130 HZ.

    """
    # TODO specify resampling method
    resampled_ecg = []
    for i in range(0, len(timestamps[:-60]), 60):
        ti = timestamps[i]
        ti20 = timestamps[i + 59]
        t_diff = (ti20 - ti) * 10**-9
        corr_samp = 130 * t_diff
        print(f"resampling {corr_samp} from {59 * 73}")
        rs = scipy.signal.resample(raw_ecg[i * 73 : (i + 59) * 73], int(corr_samp))
        resampled_ecg += list(rs)

    return resampled_ecg


def write_processed_ecg(resampled_ecg, csv):
    with open("resampled_" + csv, "w") as fout:
        for line in resampled_ecg:
            fout.write(f"{line}\n")


def main():
    parser = argparse.ArgumentParser(description="k edge swap")

    # input output arguments
    parser.add_argument("-f", "--csv", type=str, help="path to ecg csv")
    args = parser.parse_args()

    timestamps, raw_ecg = read_input_ecg(args.csv)
    resampled_ecg = resample_packets(timestamps, raw_ecg)
    write_processed_ecg(resampled_ecg, args.csv)


if __name__ == "__main__":
    main()

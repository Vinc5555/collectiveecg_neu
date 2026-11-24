# from https://dsp.stackexchange.com/a/8551
import numpy as np
import pylab as py
import argparse
import scipy.interpolate as spi
import numpy.random as npr
import numpy.linalg as npl
import matplotlib.pyplot as plt
import ipdb

# npr.seed(0)


class Signal(object):

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def plot(self, title):
        self._plot(title)
        py.plot(self.x, self.y, "bo-")
        py.ylim([-1.8, 1.8])
        py.plot(hires.x, hires.y, "k-", alpha=0.5)

    def _plot(self, title):
        py.grid()
        py.title(title)
        py.xlim([0.0, 1.0])

    def sinc_resample(self, xnew):
        m, n = (len(self.x), len(xnew))
        T = 1.0 / n
        A = np.zeros((m, n))

        for i in range(0, m):
            A[i, :] = np.sinc((self.x[i] - xnew) / T)

        return Signal(xnew, npl.lstsq(A, self.y)[0])

    def spline_resample(self, xnew):
        s = spi.splrep(self.x, self.y)
        return Signal(xnew, spi.splev(xnew, s))


class Error(Signal):

    def __init__(self, a, b):
        self.x = a.x
        self.y = np.abs(a.y - b.y)

    def plot(self, title):
        self._plot(title)
        py.plot(self.x, self.y, "bo-")
        py.ylim([0.0, 0.5])


def grid(n):
    return np.linspace(0.0, 1.0, n)


def sample(f, x):
    return Signal(x, f(x))


def random_offsets(n, amt=0.5):
    return (amt / n) * (npr.random(n) - 0.5)


def jittered_grid(n, amt=0.5):
    return np.sort(grid(n) + random_offsets(n, amt))


def f(x):
    t = np.pi * 2.0 * x
    return np.sin(t) + 0.5 * np.sin(14.0 * t)


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
        line_nb = 0
        prev_timestamp = 0
        for line in fin.readlines():

            vals = line.strip().split(",")
            trig = int(vals[1])
            raw_ecg += [int(v) for v in vals[2:]]
            timestamp = int(vals[0])
            # timestamps.append(int(vals[0]))

            if line_nb > 0:  # assume constant sampling rate for 1 packet of 73 samples
                _temp_ts = np.linspace(prev_timestamp, timestamp, 74)
                timestamps += list(_temp_ts[1:])
            if line_nb == 0:  # assume 130hz for first batch
                TS = 1 / 130
                _temp_ts = np.linspace(timestamp - 73 * TS * 10**9, timestamp, 74)

            prev_timestamp = timestamp

            # if trig == 1:
            #    trig_flag = True
            # if trig_flag:
            line_nb += 1

    return timestamps, raw_ecg


parser = argparse.ArgumentParser(description="k edge swap")

# input output arguments
parser.add_argument("-f", "--csv", type=str, help="path to ecg csv")
args = parser.parse_args()

with open(args.csv, "r") as fin:
    timestamps = []
    raw_ecg = []
    trig_flag = False
    for line_idx, line in enumerate(fin.readlines()):
        vals = line.strip().split(",")
        trig = int(vals[2])
        trig_ts = int(vals[3])

        ts = float(vals[0]) * 10**-9
        # if trig == 1:
        #    trig_flag = True
        # if trig_flag:
        if line_idx > 0:
            cur_timestamps = np.linspace(prev_ts, ts, 74)
            timestamps += list(cur_timestamps[1:])
        else:
            prev_ts = ts
            continue
        raw_ecg += [int(v) for v in vals[4:]]
        # timestamps.append(int(vals[0]))
        prev_ts = ts
assert len(raw_ecg) == len(
    timestamps
), f"ecg and timestamps are not the same length, {len(raw_ecg)}, {len(timestamps)}"
raw_ecg_signal = Signal(timestamps, raw_ecg)
print(
    f"{timestamps[0]}, {timestamps[-1]}, {int((timestamps[-1] - timestamps[0]) * 130) + 1}"
)

# BEWARE TODO TIMESTAMPS IN SECONDS ...
desired_timestamps = np.linspace(
    timestamps[0], timestamps[-1], int((timestamps[-1] - timestamps[0]) * 130) + 1
)
spline_ecg = raw_ecg_signal.spline_resample(desired_timestamps)
with open("resampled_" + args.csv, "w") as fout:
    for val_idx, val in enumerate(spline_ecg.y):
        fout.write(f"{desired_timestamps[val_idx]},{spline_ecg.y[val_idx]}\n")


# n = 30
# m = n + 1
#
## Signals
# even = sample(f, np.r_[1 : n + 1] / float(n))
# uneven = sample(f, jittered_grid(m))
# hires = sample(f, grid(10 * n))
#
# sinc = uneven.sinc_resample(even.x)
# spline = uneven.spline_resample(even.x)
#
# sinc_err = Error(sinc, even)
# spline_err = Error(spline, even)
#
## Plot Labels
# sn = lambda x, n: "%sly Sampled (%s points)" % (x, n)
# r = lambda x: "%s Reconstruction" % x
# re = lambda x: "%s Error" % r(x)
#
# plots = [
#    [even, sn("Even", n)],
#    [uneven, sn("Uneven", m)],
#    [sinc, r("Sinc")],
#    [sinc_err, re("Sinc")],
#    [spline, r("Cubic Spline")],
#    [spline_err, re("Cubic Spline")],
# ]
#
# for i in range(0, len(plots)):
#    py.subplot(3, 2, i + 1)
#    p = plots[i]
#    p[0].plot(p[1])
#
# py.show()

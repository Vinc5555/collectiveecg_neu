import os
import glob

from datetime import datetime

# --- Ordner (collectiveecg_neu) ---
PROJEKT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(PROJEKT, "data", "lab_internal", "raw")
LOG_DIR = os.path.join(PROJEKT, "data", "lab_internal", "logs")
os.makedirs(LOG_DIR, exist_ok=True)
EXPERIMENT_LOG = os.path.join(LOG_DIR, "experiment.log")
STREAMING_CSV = os.path.join(LOG_DIR, "streaming.csv")


def archive_experiment_log():
    """rename previous experiment.log file and start new one"""
    if os.path.isfile(EXPERIMENT_LOG):
        print("archiving previous experiment log")
        cur_date = datetime.today().strftime("%y_%m_%d__%H_%M")
        os.rename(EXPERIMENT_LOG, os.path.join(LOG_DIR, f"{cur_date}_experiment.log"))

    with open(EXPERIMENT_LOG, "w") as fout:
        cur_date = datetime.today().strftime("%Y %m %d, %H:%M:%S")
        fout.write(f"starting new experiment at {cur_date}")


def cleaning_streaming():
    if os.path.isfile(STREAMING_CSV):
        with open(STREAMING_CSV, "w") as fout:
            fout.write("")


def detect_unarchived_streams():
    prev_streams = glob.glob(os.path.join(RAW_DIR, "17*csv"))
    if len(prev_streams) > 0:
        print("WARNING: Found ecg recordings, please archive them")
        print(prev_streams)


def main():
    archive_experiment_log()
    cleaning_streaming()
    detect_unarchived_streams()


if __name__ == "__main__":
    main()

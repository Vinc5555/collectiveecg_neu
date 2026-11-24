# Visualization App for Theater Project, LNC2, Grezes team
# Streams 2 polar chestbelts that records ECG
# Allows to send trigger and comments.
# Naviguation buttons allows to visu 5 pages (for the 5 bluetooth dongles) showing data of 7 chestbelts per page (last page only 6)
# To be done :
#   - Visu button turns red when 1 of the chestbels wihtin this corresponding page is not retrieving data BUT color is not updated every second and button stays red.
#   -
# Camille Straboni, February 2025

import tkinter as tk  # to install : pip install python-tk
import random
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import gc  # Force garbage collection to free memory (otherwise page crashes)
from collections import deque
import os

# --- Ordner (collectiveecg_neu): streaming.csv liegt in data/lab_internal/logs/ ---
PROJEKT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STREAMING_CSV = os.path.join(PROJEKT, "data", "lab_internal", "logs", "streaming.csv")


class DataGraphApp:
    """
    Visualise in real time 10 seconds of ECG Data streamed from a Polar H10 device
    """

    def __init__(self, root):
        self.root = root
        self.root.title("Device Data Streaming")
        self.root.geometry("1800x1000")

        # Create top section
        self.top_frame = tk.Frame(root)
        self.top_frame.grid(row=0, column=0, sticky="ew")

        # Initialize graph area
        self.main_frame = tk.Frame(root)
        self.main_frame.grid(row=1, column=0, sticky="nsew")

        # Initialize graphs
        self.graph_status = {}
        self.timestamps = {}  # used to check if a stream stops
        self.page_frames = tk.Frame(self.main_frame)
        self.graphs = []

        # start visualisation
        self.create_graphs(self.page_frames)
        self.page_frames.grid(row=0, column=0, padx=10, pady=10)

    def create_graphs(self, frame):
        """Initialize all graphs"""
        # Creates graphs and updates page status for navigation button colors
        start_id = 1
        num_graphs = 8

        # define window sizes for graphs
        self.root.update_idletasks()
        window_width = self.root.winfo_width()
        window_height = self.root.winfo_height()

        graph_height = int(window_height * 0.1)  # Keep dynamic height
        graph_width = int(window_width * 1)  # Keep dynamic width

        # Destroy old widgets
        for widget in frame.winfo_children():
            widget.destroy()

        # Free memory
        for fig, ax, canvas in self.graphs:
            fig.clf()
            canvas.get_tk_widget().destroy()
        self.graphs = []

        gc.collect()  # Force garbage collection

        # initialise visualisation for 8 graphs
        for i in range(num_graphs):
            self.graph_status[i] = "good"
            graph_id = start_id + i
            graph_title = f"ID {graph_id}"

            # Create Label for Graph Title
            title_label = tk.Label(frame, text=graph_title, bg="black", fg="white")
            title_label.grid(row=i, column=0, pady=5, sticky="w")

            # Create Figure
            fig = plt.Figure(
                figsize=(graph_width / 100, graph_height / 100)
            )  # Keep dynamic sizing
            ax = fig.add_subplot(111)

            # initialize with "no data" text
            ax.text(
                0.5,
                0.5,
                "No Data",
                ha="center",
                va="center",
                fontsize=12,
                color="red",
            )

            ax.set_xticks([])
            ax.set_yticks(range(0, 101, 25))

            # Embed Matplotlib Figure in Tkinter
            canvas = FigureCanvasTkAgg(fig, master=frame)
            canvas_widget = canvas.get_tk_widget()
            canvas_widget.grid(row=i, column=1, pady=5, sticky="ew")
            canvas.draw()

            # Store figure and canvas
            self.graphs.append((fig, ax, canvas))

            plt.close(fig)  # Free memory (otherwise window crashes)

        # Start periodic refresh of the graphs (every 1 sec)
        self.refresh_graphs(frame)

    def read_last_18_lines(self, file_idx, filename):
        """Read last 10 seconds of ECG Data. If stream has started less than
        10 seconds ago, fill with 0s instead.
        """

        # Retrieve ECG data : last 10 seconds (130 Hz) = 1300 data points => 18 lines of 73 data points
        with open(filename, "r") as fin:
            lines = deque(
                fin, maxlen=18
            )  # Read only the last 18 lines to improve the memory efficiency
        data_list = []
        for line in lines:
            val = line.strip().split(",")
            timestamp = int(val[0])
            data_list += [
                int(v) / 10.0 for v in val[3:]
            ]  # divide by 10 to enhance the graph
        # get last timestamp
        # self.timestamps[filename] = timestamp
        if filename in self.timestamps and timestamp == self.timestamps[filename]:
            self.graph_status[file_idx] = "bad"
        else:
            self.graph_status[file_idx] = "good"
        self.timestamps[filename] = timestamp
        if (
            len(data_list) < 1314
        ):  # In case of restarting stream, fill the first values with 0s to catch up - 1314 = 18 * 73
            missing_values_len = 1314 - len(data_list)
            data_list = missing_values_len * [0] + data_list

        return data_list

    def refresh_graphs(self, frame):
        """Refresh graphs every seconds, display last 10 seconds of ecg data"""

        # Read list of files currently streaming
        with open(STREAMING_CSV, "r") as fin:
            stream_files = []
            polar_ids = []
            for line_idx, line in enumerate(fin.readlines()):
                # if (line_idx>= page_num *7) and (line_idx <(page_num+1) * 7):
                polar_ids.append(line.strip().split(",")[0])
                stream_files.append(line.strip().split(",")[1])

        # read last 10 seconds of data (= last 18 lines in the file)
        ecg_data_list = []
        for file_idx, stream in enumerate(stream_files):
            ecg_data_list.append(self.read_last_18_lines(file_idx, stream))

        # if there are less than 8 streams, display graph with 0s
        if len(stream_files) < 8:
            missing_stream_len = 8 - len(stream_files)
            zeros_graph = 1314 * [0]
            for j in range(missing_stream_len):
                ecg_data_list.append(zeros_graph)
            for i in range(len(stream_files), 8):
                self.graph_status[i] = "good"

        # display device ID at the left of each graph
        for pidx, polar_id in enumerate(polar_ids):
            graph_title = f"{polar_id}"

            # Create Label for Graph Title
            title_label = tk.Label(frame, text=graph_title, bg="black", fg="white")
            title_label.grid(row=pidx, column=0, pady=5, sticky="w")

        # Refresh all graphs on the page
        for index, (fig, ax, canvas) in enumerate(self.graphs):
            if self.graph_status[index] == "good":

                ecg_data = ecg_data_list[index]  # Use different data for each graph
                ax.clear()
                ax.plot(range(73 * 18), ecg_data, color="cyan")
                ax.set_xticks([])
                ax.set_yticks([])
                # ax.set_yticks(range(-105, 105, 25)) # y ticks removed to save graphic memory

                canvas.draw_idle()  # Refresh the canvas
            else:
                ax.clear()
                polar_id = polar_ids[index]
                ax.text(
                    0.42,
                    0.5,
                    f"DATA STOP FOR {polar_id}",
                    color="red",
                    fontsize="xx-large",
                )

                canvas.draw_idle()  # Refresh the canvas

        # Schedule the next update in 1000 ms (1 second)
        self.root.after(1000, lambda: self.refresh_graphs(frame))


if __name__ == "__main__":
    root = tk.Tk()
    app = DataGraphApp(root)
    root.mainloop()

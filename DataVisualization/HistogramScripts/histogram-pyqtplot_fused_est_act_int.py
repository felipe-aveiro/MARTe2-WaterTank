import pandas as pd
import numpy as np
import pyqtgraph as pg
import pyqtgraph.exporters
from pyqtgraph.Qt import QtWidgets, QtGui
import sys
import os


# ============================================================
# HELPER FUNCTION TO PARSE HISTOGRAM STRINGS
# ============================================================

def parse_hist_string(s):
    return list(map(int, str(s).strip("{} ").split()))


# ============================================================
# USER CONFIGURATION
# ============================================================

histogram_files = {
    "Shot 48555": "/home/felipe/git-repos/MARTe2-WaterTank/DataVisualization/Outputs/IsttokOutput_DataFusion_48555_histogram_act_interval.csv",
    "Shot 53071": "/home/felipe/git-repos/MARTe2-WaterTank/DataVisualization/Outputs/IsttokOutput_DataFusion_53071_histogram_act_interval.csv",
}

export_path = "/home/felipe/git-repos/MARTe2-WaterTank/DataVisualization/Outputs/EstimationHistogramPlots/Estimation_Fusion_CycleTime_Histograms_act_interval.png"

# HistogramGAM configuration
min_lim = 160.0      # microseconds
max_lim = 200.0     # microseconds

# Plot configuration
Y_MIN = 0
Y_MAX = 108         # leaves space above 100 so the tick label is not clipped
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 500


# ============================================================
# LOAD HISTOGRAM DATA
# ============================================================

def load_last_histogram_row(file_path):
    df = pd.read_csv(file_path, sep=";", comment="#", engine="python")
    df = df.dropna(axis=0, how="all")
    df = df.dropna(axis=1, how="all")

    if df.empty:
        raise ValueError(f"Empty or unreadable file: {file_path}")

    first_value = str(df.iloc[-1, 0])

    if "{" in first_value and "}" in first_value:
        raw_strings = df.iloc[:, 0]
        parsed = raw_strings.apply(parse_hist_string)
        return list(parsed.iloc[-1])

    numeric_df = df.apply(pd.to_numeric, errors="coerce")
    numeric_df = numeric_df.dropna(axis=0, how="all")
    numeric_df = numeric_df.dropna(axis=1, how="all")

    return numeric_df.iloc[-1].astype(int).tolist()


last_rows = {}

for shot_name, file_path in histogram_files.items():
    last_rows[shot_name] = load_last_histogram_row(file_path)


# ============================================================
# HISTOGRAM CONFIGURATION
# ============================================================

num_bins = len(next(iter(last_rows.values())))
internal_bins = num_bins - 2
bin_width = (max_lim - min_lim) / internal_bins

# Bar centers
x_values = [
    min_lim - bin_width + bin_width * i + bin_width / 2
    for i in range(num_bins)
]

# Tick positions are bin edges
tick_edges = [
    min_lim - bin_width + bin_width * i
    for i in range(num_bins + 1)
]


# ============================================================
# X-AXIS TICK LABELS
# ============================================================

tick_labels = []

for x in tick_edges:
    label = f"{x:.1f}"

    if label in ["165.0", "170.0", "175.0", "180.0", "185.0", "190.0", "195.0"]:
        tick_labels.append(f"{int(round(x))}")
    else:
        tick_labels.append("")

tick_labels[0] = ""
tick_labels[1] = "≤160"
tick_labels[-2] = "≥200"
tick_labels[-1] = ""

xticks = list(zip(tick_edges, tick_labels))


# ============================================================
# Y-AXIS TICKS
# ============================================================

yticks = [
    (0, "0"),
    (20, "20"),
    (40, "40"),
    (60, "60"),
    (80, "80"),
    (100, "100")
]


# ============================================================
# COMPUTE PERCENTAGES
# ============================================================

def compute_percentages(row):
    total = sum(row)
    if total <= 0:
        return [0.0 for _ in row]
    return [(count / total) * 100.0 for count in row]


percentages = {}

for shot_name, row in last_rows.items():
    percentages[shot_name] = compute_percentages(row)


# ============================================================
# CREATE PYQTGRAPH APPLICATION
# ============================================================

app = QtWidgets.QApplication([])

win = pg.GraphicsLayoutWidget(title="Estimation Cycle Duration Histograms")
win.resize(WINDOW_WIDTH, WINDOW_HEIGHT)

# Fonts matched to old plot style:
# axis tick values are NOT bold
bold_font = QtGui.QFont("Arial", 11, QtGui.QFont.Bold)
tick_font = QtGui.QFont("Arial", 10)
title_font = QtGui.QFont("Arial", 16, QtGui.QFont.Bold)
value_font = QtGui.QFont("Arial", 8, QtGui.QFont.Bold, italic=True)
shot_font = QtGui.QFont("Arial", 16, QtGui.QFont.Bold)

bar_width = bin_width
bar_half_width = bar_width / 2

x_min = min(x_values) - bar_half_width
x_max = max(x_values) + bar_half_width

colors = [
    QtGui.QColor("#de9331"),
    QtGui.QColor("#2285c5"),
]

for color in colors:
    color.setAlpha(180)


# ============================================================
# CREATE STACKED PLOTS
# ============================================================

shot_items = list(percentages.items())

for idx, (shot_name, shot_percentages) in enumerate(shot_items):

    if idx > 0:
        win.nextRow()

    plot = win.addPlot(title="Histograms of Estimation Cycle Duration" if idx == 0 else "")
    plot.setMaximumHeight(220)

    if idx == 0:
        plot.titleLabel.item.setFont(title_font)

    plot.setXRange(x_min, x_max, padding=0)
    plot.setYRange(Y_MIN, Y_MAX, padding=0)

    plot.getAxis("bottom").setTicks([xticks])
    plot.getAxis("left").setTicks([yticks])

    # Axis values: normal font, like the old graph
    plot.getAxis("bottom").setStyle(tickFont=tick_font)
    plot.getAxis("left").setStyle(tickFont=tick_font)

    # Keeps axis proportions closer to the old plot
    plot.getAxis("left").setWidth(55)

    if idx == len(shot_items) - 1:
        plot.setLabel("bottom", "Cycle duration [µs]")
        plot.getAxis("bottom").label.setFont(bold_font)
    else:
        plot.setLabel("bottom", "")

    plot.setLabel("left", "Percentage", units="%")
    plot.getAxis("left").label.setFont(bold_font)

    plot.showGrid(x=True, y=True)

    bar = pg.BarGraphItem(
        x=np.array(x_values),
        height=shot_percentages,
        width=bar_width,
        brush=colors[idx % len(colors)]
    )
    plot.addItem(bar)

    shot_counts = last_rows[shot_name]

    for i, (x, y, count) in enumerate(zip(x_values, shot_percentages, shot_counts)):

        if count == 0:
            continue

        if i == len(x_values) - 1:
            text = pg.TextItem(f"{y:.2f}%", anchor=(0.5, 1.0))
            text.setFont(value_font)
            text.setPos(x, min(y + 0.5, Y_MAX - 1.0))
            plot.addItem(text)

        else:
            text = pg.TextItem(f"{y:.2f}%", anchor=(0.5, 1.0))
            text.setFont(value_font)

            if y < 0.5:
                y_pos = 1.6
            elif y < 1.0:
                y_pos = 2.0
            elif y < 2.0:
                y_pos = 2.5
            else:
                y_pos = y + 0.5

            text.setPos(x, y_pos)
            plot.addItem(text)

    shot_text = pg.TextItem(shot_name, anchor=(0.5, 0.0))
    shot_text.setFont(shot_font)
    shot_text.setColor(QtGui.QColor("#00bfff"))
    shot_text.setPos((x_min + x_max) / 2.0, 62.0)
    plot.addItem(shot_text)


# ============================================================
# EXPORT IMAGE
# ============================================================

os.makedirs(os.path.dirname(export_path), exist_ok=True)

screenshot = win.grab()
screenshot.save(export_path, "PNG")

print(f"Image saved to {export_path}")

sys.exit()
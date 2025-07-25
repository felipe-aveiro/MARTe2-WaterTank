import pandas as pd
import numpy as np
import pyqtgraph as pg
import pyqtgraph.exporters
from pyqtgraph.Qt import QtWidgets, QtGui
import sys

# === Helper function to parse histogram strings ===
def parse_hist_string(s):
    return list(map(int, s.strip("{} ").split()))

# === Load Simulink data ===
file_simulink = "/home/felipe/git-repos/MARTe2-WaterTank/DataVisualization/Outputs/WTM-Simulink-histogram.csv"
df_simulink = pd.read_csv(file_simulink)
raw_strings_simulink = df_simulink.iloc[:, 0]
parsed_simulink = raw_strings_simulink.apply(parse_hist_string)
last_row_simulink = parsed_simulink.iloc[59999]

# === Load MARTe2 data ===
file_marte2 = "/home/felipe/git-repos/MARTe2-WaterTank/DataVisualization/Outputs/WTM-GAM-histogram.csv"
df_marte2 = pd.read_csv(file_marte2)
raw_strings_marte2 = df_marte2.iloc[:, 0]
parsed_marte2 = raw_strings_marte2.apply(parse_hist_string)
last_row_marte2 = parsed_marte2.iloc[59999]

# === Histogram configuration ===
bin_width = 25  # microseconds
min_lim = 800   # microseconds
num_bins = len(last_row_simulink)

# === Compute common X values (both histograms share the same bin positions) ===
x_values = [min_lim - bin_width + bin_width * i + bin_width / 2 for i in range(num_bins)]
x_values_ms = [x / 1000 for x in x_values]

tick_edges = [min_lim - bin_width + bin_width * i for i in range(num_bins + 1)]
tick_edges_ms = [x / 1000 for x in tick_edges]

# === Tick labels for X axis ===
tick_labels = []
for x in tick_edges_ms:
    label = f"{x:.3f}"
    if label in ["0.850", "0.900", "0.950", "1.000", "1.050", "1.100", "1.150"]:
        tick_labels.append(label)
    else:
        tick_labels.append("")
tick_labels[0] = ""
tick_labels[1] = "<0.800"
tick_labels[-2] = "≥1.200"
tick_labels[-1] = ""
xticks = list(zip(tick_edges_ms, tick_labels))

# === Compute percentages for both sources ===
def compute_percentages(row):
    total = sum(row)
    return [(count / total) * 100 if total > 0 else 0 for count in row]

percentages_simulink = compute_percentages(last_row_simulink)
percentages_marte2 = compute_percentages(last_row_marte2)

# === Create PyQtGraph application ===
app = QtWidgets.QApplication([])

# === Main window with stacked layout ===
win = pg.GraphicsLayoutWidget(title="Cycle Duration Histograms")
win.resize(800, 500)  # Taller for stacking vertically

# Common X range with margin
x_min = min(x_values_ms) - 0.01
x_max = max(x_values_ms) + 0.01

bold_font = QtGui.QFont("Arial", 11, QtGui.QFont.Bold)

# === FIRST PLOT: Simulink Histogram ===
plot_simulink = win.addPlot(title="Histograms of Cycle Duration")
plot_simulink.setMaximumHeight(400)  # Compress vertically
plot_simulink.titleLabel.item.setFont(QtGui.QFont("Arial", 16, QtGui.QFont.Bold))
plot_simulink.setXRange(x_min, x_max, padding=0)
plot_simulink.setYRange(0, 55, padding=0)
plot_simulink.getAxis("bottom").setTicks([xticks])
plot_simulink.setLabel('bottom', 'Cycle duration (ms)')
plot_simulink.setLabel('left', 'Percentage', units='%')
plot_simulink.getAxis("bottom").label.setFont(bold_font)
plot_simulink.getAxis("left").label.setFont(bold_font)
plot_simulink.showGrid(x=True, y=True)

color_simulink = QtGui.QColor("#de9331")
color_simulink.setAlpha(180)
bar_simulink = pg.BarGraphItem(x=np.array(x_values_ms), height=percentages_simulink, width=0.025, brush=color_simulink)
plot_simulink.addItem(bar_simulink)

for x, y in zip(x_values_ms, percentages_simulink):
    if y > 0:
        text = pg.TextItem(f"{y:.1f}%", anchor=(0.5, 1.0))
        text.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold, italic=True))
        text.setPos(x, y)
        plot_simulink.addItem(text)

# === SECOND PLOT: MARTe2 Histogram (stacked below) ===
win.nextRow()  # Move to next row
plot_marte2 = win.addPlot(title="")
plot_marte2.setMaximumHeight(400)  # Compress vertically
#plot_marte2.titleLabel.item.setFont(QtGui.QFont("Arial", 16, QtGui.QFont.Bold))
plot_marte2.setXRange(x_min, x_max, padding=0)
plot_marte2.setYRange(0, 55, padding=0)
plot_marte2.getAxis("bottom").setTicks([xticks])
plot_marte2.setLabel('bottom', 'Cycle duration [ms]')
plot_marte2.setLabel('left', 'Percentage', units='%')
plot_marte2.getAxis("bottom").label.setFont(bold_font)
plot_marte2.getAxis("left").label.setFont(bold_font)
plot_marte2.showGrid(x=True, y=True)

color_marte2 = QtGui.QColor("#2285c5")
color_marte2.setAlpha(180)
bar_marte2 = pg.BarGraphItem(x=np.array(x_values_ms), height=percentages_marte2, width=0.025, brush=color_marte2)
plot_marte2.addItem(bar_marte2)

for x, y in zip(x_values_ms, percentages_marte2):
    if y > 0:
        text = pg.TextItem(f"{y:.1f}%", anchor=(0.5, 1.0))
        text.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold, italic=True))
        text.setPos(x, y)
        plot_marte2.addItem(text)

# === Export final stacked image ===
export_path = "/home/felipe/git-repos/MARTe2-WaterTank/DataVisualization/Outputs/MARTe2-Engine/Histograms_Stacked.png"
screenshot = win.grab()
screenshot.save(export_path, 'PNG')
print(f"Image saved to {export_path}")

sys.exit()
"""

# Bar midpoints for plotting
x_values = [min_lim - bin_width + bin_width * i + bin_width / 2 for i in range(num_bins)]
x_values_ms = [x / 1000 for x in x_values]

# Tick positions (edges between bins)
tick_edges = [min_lim - bin_width + bin_width * i for i in range(num_bins + 1)]
tick_edges_ms = [x / 1000 for x in tick_edges]

# Tick labels
tick_labels = [f"{x:.3f}" for x in tick_edges_ms]
tick_labels[1] = "<0.800"
tick_labels[0] = ""
tick_labels[-2] = "≥1.200"
tick_labels[-1] = ""

# Compute percentages
total_counts = sum(last_row)
percentages = [(count / total_counts) * 100 if total_counts > 0 else 0 for count in last_row]

# Create PyQtGraph app
app = QtWidgets.QApplication([])
win = pg.GraphicsLayoutWidget(title="Cycle Duration Histogram")
win.resize(700, 500)
plot = win.addPlot(title="Histogram of Cycle Duration")
plot.titleLabel.item.setFont(QtGui.QFont("Arial", 18, QtGui.QFont.Bold))
color = QtGui.QColor("#de9331")  # Simulink color
#color = QtGui.QColor("#2285c5")  # GAM color
color.setAlpha(180)
brush = QtGui.QBrush(color)
bar_graph = pg.BarGraphItem(x=np.array(x_values_ms), height=percentages, width=0.025, brush=brush)
plot.addItem(bar_graph)

# Set ranges to remove paddings
bar_half_width = 0.025 / 2
min_x = min(x_values_ms) - bar_half_width
max_x = max(x_values_ms) + bar_half_width
plot.setXRange(min_x, max_x, padding=0)
min_y = 0
max_y = 50
plot.setYRange(min_y, max_y, padding=0)

# Set ticks (edges between bars)

tick_labels = []
for x in tick_edges_ms:
    label = f"{x:.3f}"
    if label in ["0.850", "0.900", "0.950", "1.000", "1.050", "1.100", "1.150"]:
        tick_labels.append(label)
    else:
        tick_labels.append("")

tick_labels[0] = ""
tick_labels[1] = "<0.800"
tick_labels[-2] = "≥1.200"
tick_labels[-1] = ""

xticks = list(zip(tick_edges_ms, tick_labels))
plot.getAxis("bottom").setTicks([xticks])
plot.getAxis("bottom").setStyle(tickFont=QtGui.QFont("Arial", 10))
plot.getAxis("left").setStyle(tickFont=QtGui.QFont("Arial", 10))

# Set axis labels
plot.setLabel('bottom', 'Cycle duration (ms)')
plot.setLabel('left', 'Percentage', units='%')

bold_font = QtGui.QFont("Arial", 12, QtGui.QFont.Bold)
plot.getAxis("bottom").label.setFont(bold_font)
plot.getAxis("left").label.setFont(bold_font)

plot.showGrid(x=True, y=True)

# Add percentage text above each bar
for x, y in zip(x_values_ms, percentages):
    if y > 0:
        text = pg.TextItem(f"{y:.1f}%", anchor=(0.5, 1.0))
        text.setFont(QtGui.QFont("Arial", 9, QtGui.QFont.Bold, italic=True))
        text.setPos(x, y)
        plot.addItem(text)

# Save image
export_path = "/home/felipe/git-repos/MARTe2-WaterTank/DataVisualization/Outputs/MARTe2-Engine/WTM_Simulink_histogram.png"
screenshot = win.grab()
screenshot.save(export_path, 'PNG')
print(f"Image saved to {export_path}")

# Exit
sys.exit()"""

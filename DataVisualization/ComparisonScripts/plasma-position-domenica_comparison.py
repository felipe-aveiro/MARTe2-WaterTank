import sys
import os
import re
import numpy as np
import pandas as pd
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets, QtCore, QtGui
from pyqtgraph.exporters import ImageExporter
from sdas.core.client.SDASClient import SDASClient

app = QtWidgets.QApplication(sys.argv)

HOST = 'baco.ipfn.tecnico.ulisboa.pt'
PORT = 8888

# === Load CSV file ===
def load_csv(path):
    df = pd.read_csv(path, delimiter=';')
    df.columns = df.columns.str.strip()
    time_col = next((c for c in df.columns if c.startswith("#time")), None)
    if not time_col:
        raise ValueError("Time column not found in CSV.")
    time = (df[time_col] - df[time_col].iloc[0]) * 1e3  # ms
    return df, time.to_numpy()

# === Load SDAS data ===
def load_sdas_channel(client, channel_id, shot_number):
    data_struct = client.getData(channel_id, '0x0000', shot_number)
    data_array = np.array(data_struct[0].getData())
    length = len(data_array)
    t_start = data_struct[0].getTStart()
    t_end = data_struct[0].getTEnd()
    dt_us = (t_end.getTimeInMicros() - t_start.getTimeInMicros()) / (length - 1)
    time_vector = np.linspace(0, dt_us * (length - 1), length) * 1e-3  # ms
    return data_array, time_vector

# === Choose CSV file ===
csv_path, _ = QtWidgets.QFileDialog.getOpenFileName(
    None,
    "Select CSV file with your reconstruction",
    "/home/felipe/git-repos/MARTe2-WaterTank/DataVisualization/Outputs/",
    "CSV Files (*.csv);;All Files (*)"
)

if not csv_path:
    QtWidgets.QMessageBox.critical(None, "Error", "No file selected. Exiting...")
    sys.exit()

df, csv_time = load_csv(csv_path)
csv_filename = os.path.basename(csv_path)

# === Extract shot number ===
match = re.search(r'(\d{5})', csv_filename)
shot_number = int(match.group(1)) if match else None
if not shot_number:
    QtWidgets.QMessageBox.critical(None, "Error", "Shot number not found in file name.")
    sys.exit()

# === Determine dtype ===
dtype = "float32" if "Atca" in csv_filename else "float64"

# === Check available columns for reconstructions ===
options_map = {}
if f"outputMpR ({dtype})[1]" in df.columns and f"outputMpZ ({dtype})[1]" in df.columns:
    options_map["Magnetic Reconstruction"] = (
        df[f"outputMpR ({dtype})[1]"].values,
        df[f"outputMpZ ({dtype})[1]"].values
    )

if f"outputEpR ({dtype})[1]" in df.columns and f"outputEpZ ({dtype})[1]" in df.columns:
    options_map["Electric Reconstruction"] = (
        df[f"outputEpR ({dtype})[1]"].values,
        df[f"outputEpZ ({dtype})[1]"].values
    )

if f"outputFusedR ({dtype})[1]" in df.columns and f"outputFusedZ ({dtype})[1]" in df.columns:
    options_map["Fused Reconstruction"] = (
        df[f"outputFusedR ({dtype})[1]"].values,
        df[f"outputFusedZ ({dtype})[1]"].values
    )

if not options_map:
    QtWidgets.QMessageBox.critical(None, "Error", "No valid reconstruction columns found in CSV.")
    sys.exit()

# === Load Domenica's SDAS channels (083 and 084) ===
client = SDASClient(HOST, PORT)
radial_dom, sdas_time = load_sdas_channel(client, "MARTE_NODE_IVO3.DataCollection.Channel_083", shot_number)
vertical_dom, _ = load_sdas_channel(client, "MARTE_NODE_IVO3.DataCollection.Channel_084", shot_number)

# === Dialog to choose reconstruction ===
dialog = QtWidgets.QDialog()
dialog.setWindowTitle("Choose the reconstruction to compare with reference")
dialog.resize(800, 100) 
layout = QtWidgets.QVBoxLayout(dialog)
label = QtWidgets.QLabel("Select the reconstruction:")
layout.addWidget(label)

combo = QtWidgets.QComboBox()
for key in options_map.keys():
    combo.addItem(key)
layout.addWidget(combo)

ok_button = QtWidgets.QPushButton("OK")
layout.addWidget(ok_button)
ok_button.clicked.connect(dialog.accept)
dialog.exec_()

selected_option = combo.currentText()
radial_recon, vertical_recon = options_map[selected_option]

# === Color mapping based on selected option ===
color_map = {
    "Magnetic Reconstruction": ('m', "Mirnov Coils"),
    "Electric Reconstruction": ('g', "Langmuir Probes"),
    "Fused Reconstruction": ('b', "Fused State")
}

selected_color, selected_label = color_map.get(selected_option, ('w', selected_option))  # Default to white if unknown

# === Main window with stacked plots ===
win = QtWidgets.QMainWindow()
win.setWindowTitle(f"Comparison with reference - Shot {shot_number}")
central_widget = QtWidgets.QWidget()
layout = QtWidgets.QVBoxLayout(central_widget)
win.setCentralWidget(central_widget)

plot_widget = pg.GraphicsLayoutWidget()
layout.addWidget(plot_widget)
plot_widget.setFixedSize(1200, 600)

# === Fonts ===
title_font = QtGui.QFont("Arial", 14, QtGui.QFont.Bold)
axis_font = QtGui.QFont("Arial", 11, QtGui.QFont.Bold)

# === Radial plot ===
plot_r = plot_widget.addPlot(title=f"Radial Position ({selected_option} vs Reference)")
plot_r.titleLabel.item.setFont(title_font)
plot_r.setLabel("bottom", "Time [ms]")
plot_r.setLabel("left", "R [m]")
plot_r.getAxis("bottom").label.setFont(axis_font)
plot_r.getAxis("left").label.setFont(axis_font)
legend_r = plot_r.addLegend()
#legend_r.setLabelTextSize("14pt")
plot_r.showGrid(x=True, y=True)

# === Vertical plot ===
plot_widget.nextRow()
plot_z = plot_widget.addPlot(title=f"Vertical Position ({selected_option} vs Reference)")
plot_z.titleLabel.item.setFont(title_font)
plot_z.setLabel("bottom", "Time [ms]")
plot_z.setLabel("left", "Z [m]")
plot_z.getAxis("bottom").label.setFont(axis_font)
plot_z.getAxis("left").label.setFont(axis_font)
#legend_z = plot_z.addLegend()
#legend_z.setLabelTextSize("14pt")
plot_z.showGrid(x=True, y=True)

# === Add curves ===
plot_r.plot(csv_time, radial_recon, pen=pg.mkPen(selected_color, width=2), name=selected_label)
plot_z.plot(csv_time, vertical_recon, pen=pg.mkPen(selected_color, width=2), name=selected_label)

zero_lineR_center = pg.InfiniteLine(pos=0.46, angle=0, pen=pg.mkPen('w', width=1, style=QtCore.Qt.DashLine))
zero_lineR_upper = pg.InfiniteLine(pos=0.46+0.085, angle=0, pen=pg.mkPen('r', width=2, style=QtCore.Qt.DotLine))
zero_lineR_lower = pg.InfiniteLine(pos=0.46-0.085, angle=0, pen=pg.mkPen('r', width=2, style=QtCore.Qt.DotLine))
plot_r.addItem(zero_lineR_center)
plot_r.addItem(zero_lineR_upper)
plot_r.addItem(zero_lineR_lower)

plot_r.plot(sdas_time, radial_dom + 0.46, pen=pg.mkPen('y', width=2), name="Reference")

zero_lineZ_center = pg.InfiniteLine(pos=0, angle=0, pen=pg.mkPen('w', width=1, style=QtCore.Qt.DashLine))
zero_lineZ_upper = pg.InfiniteLine(pos=0.085, angle=0, pen=pg.mkPen('r', width=2, style=QtCore.Qt.DotLine))
zero_lineZ_lower = pg.InfiniteLine(pos=-0.085, angle=0, pen=pg.mkPen('r', width=2, style=QtCore.Qt.DotLine))
plot_z.addItem(zero_lineZ_center)
plot_z.addItem(zero_lineZ_upper)
plot_z.addItem(zero_lineZ_lower)
               
plot_z.plot(sdas_time, vertical_dom, pen=pg.mkPen('y', width=2), name="Reference")

plot_r.setYRange(0.46 - 0.1, 0.46 + 0.1)
plot_z.setYRange(-0.1,0.1)
time_min = max(csv_time.min(), sdas_time.min())
time_max = min(csv_time.max(), sdas_time.max())
#plot_r.setXRange(time_min, time_max, padding=0)
#plot_z.setXRange(time_min, time_max, padding=0)
plot_r.setXRange(160, 400, padding=0)
plot_z.setXRange(160, 400, padding=0)
plot_r.setLimits(xMin=time_min, xMax=time_max)
plot_z.setLimits(xMin=time_min, xMax=time_max)

plot_r.setXLink(plot_z)

# Calculate Y center offsets
r_center = (plot_r.vb.viewRange()[1][0] + plot_r.vb.viewRange()[1][1]) / 2
z_center = (plot_z.vb.viewRange()[1][0] + plot_z.vb.viewRange()[1][1]) / 2
offset_r_to_z = z_center - r_center
offset_z_to_r = r_center - z_center

# Connect signals to sync Y zoom
plot_r.vb.sigYRangeChanged.connect(lambda: sync_y_range(plot_r, plot_z, offset_r_to_z))
plot_z.vb.sigYRangeChanged.connect(lambda: sync_y_range(plot_z, plot_r, offset_z_to_r))

def sync_y_range(source_plot, target_plot, offset):
    if not target_plot.vb:
        return

    source_ymin, source_ymax = source_plot.vb.viewRange()[1]
    source_center = (source_ymin + source_ymax) / 2
    source_size = source_ymax - source_ymin

    target_center = source_center + offset
    new_target_range = (
        target_center - source_size / 2,
        target_center + source_size / 2
    )

    target_plot.vb.blockSignals(True)
    target_plot.vb.setYRange(*new_target_range, padding=0)
    target_plot.vb.blockSignals(False)

# === Export button ===
export_btn = QtWidgets.QPushButton("Export Image")
layout.addWidget(export_btn)

def export_plots():
    default_dir = "/home/felipe/git-repos/MARTe2-WaterTank/DataVisualization/Outputs/PositionComparison"
    os.makedirs(default_dir, exist_ok=True)
    safe_option = selected_option.replace(" ", "_")
    default_path = os.path.join(default_dir, f"comparison_{safe_option}_vs_reference_{shot_number}.png")
    path, _ = QtWidgets.QFileDialog.getSaveFileName(
        None, "Save as PNG", default_path, "PNG Files (*.png)"
    )
    if path:
        exporter = ImageExporter(plot_widget.scene())
        exporter.parameters()['width'] = 1400
        exporter.export(path)
        print(f"\nImage saved to {path}\n")

export_btn.clicked.connect(export_plots)

# === Show window ===
win.showMaximized()
win.keyPressEvent = lambda event: app.quit() if event.key() == QtCore.Qt.Key_Escape else None
sys.exit(app.exec_())

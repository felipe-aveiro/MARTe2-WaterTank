import sys
import os
import re
import numpy as np
import pandas as pd
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets, QtCore
import pyqtgraph.exporters

from sdas.core.client.SDASClient import SDASClient
from sdas.core.SDAStime import TimeStamp

# === SDAS connection ===
HOST = 'baco.ipfn.tecnico.ulisboa.pt'
PORT = 8888

# === Domenica database channel for actuation ===
SDAS_SEND_TO_HORIZONTAL_CH = 'MARTE_NODE_IVO3.DataCollection.Channel_126'  # SendToHorizontalValue

# === Start Qt app ===
app = QtWidgets.QApplication(sys.argv)

# === Select CSV ===
csv_path, _ = QtWidgets.QFileDialog.getOpenFileName(
    None, "Select CSV File",
    os.path.expanduser("~/git-repos/MARTe2-WaterTank/DataVisualization/Outputs/"),
    "CSV Files (*.csv);;All Files (*)"
)

if not csv_path:
    sys.exit("No file selected.")

# === Load CSV ===
with open(csv_path, 'r') as f:
    header_line = f.readline()
delimiter = ';' if header_line.count(';') > header_line.count(',') else ','
df = pd.read_csv(csv_path, delimiter=delimiter)
df.columns = df.columns.str.strip()

# === Identify shot nº ===
csv_filename = os.path.basename(csv_path)
match = re.search(r'(\d{5})', csv_filename)
use_float32 = "Atca" in csv_filename
dtype = "float32" if use_float32 else "float64"
shot_number = match.group(1) if match else "unknown"

# === Columns (CSV) ===
time_col = f"#timeI ({dtype})[1]"
vertical_ref_col = f"vertical_reference ({dtype})[1]"
vertical_current_request_col = f"vertical_current_request ({dtype})[1]"

# IMPORTANT: PositionZ comes from Domenica's reconstruction output exported to CSV
position_z_col = f"PositionZ ({dtype})[1]"

for col in [time_col, position_z_col, vertical_ref_col, vertical_current_request_col]:
    if col not in df.columns:
        sys.exit(f"Missing column: {col}")

# === CSV Data ===
# Keep your original convention: time starts at 0 and is shown in ms
time_csv_ms = (df[time_col] - df[time_col].iloc[0]) * 1e3
position_z = df[position_z_col].values
vertical_ref = df[vertical_ref_col].values
vertical_request_generated = df[vertical_current_request_col].values

# === Load SDAS data (SendToHorizontalValue / channel 126) ===
def load_sdas_signal(client, channel_id, shotnr):
    dataStruct = client.getData(channel_id, '0x0000', int(shotnr))
    dataArray = dataStruct[0].getData()
    n = len(dataArray)

    tstart = dataStruct[0].getTStart()
    tend = dataStruct[0].getTEnd()
    tbs = (tend.getTimeInMicros() - tstart.getTimeInMicros()) / (n - 1)

    # Build time vector aligned to the shot event timestamp (same as SDAS exporter)
    events = dataStruct[0].get('events')[0]
    tevent = TimeStamp(tstamp=events.get('tstamp'))
    delay = tstart.getTimeInMicros() - tevent.getTimeInMicros()

    # Time in ms
    time_ms = np.linspace(
        delay / 1000.0,
        (delay + tbs * (n - 1)) / 1000.0,
        n,
        dtype=np.float64
    )

    return np.asarray(dataArray, dtype=np.float64), time_ms

try:
    client = SDASClient(HOST, PORT)
    sdas_send_to_horizontal, time_sdas_ms = load_sdas_signal(client, SDAS_SEND_TO_HORIZONTAL_CH, shot_number)
except Exception as e:
    sys.exit(f"Failed to download SDAS channel 126 (SendToHorizontalValue): {e}")

# === Make SDAS time start at 0 ms (to be directly comparable with the CSV plot) ===
time_sdas_ms = time_sdas_ms - time_sdas_ms[0]

# === Define common X range (based on CSV) ===
time_min, time_max = float(time_csv_ms.min()), float(time_csv_ms.max())

# === Interpolate SDAS actuation onto CSV time base (clean overlay comparison) ===
# If SDAS does not fully cover the CSV time window, extrapolation is not allowed -> clamp to edges.
t_interp = time_csv_ms.values if hasattr(time_csv_ms, "values") else np.asarray(time_csv_ms)
sdas_interp = np.interp(
    t_interp,
    time_sdas_ms,
    sdas_send_to_horizontal,
    left=sdas_send_to_horizontal[0],
    right=sdas_send_to_horizontal[-1]
)

# === Main Window ===
main_window = QtWidgets.QMainWindow()
central = QtWidgets.QWidget()
layout = QtWidgets.QVBoxLayout(central)
main_window.setCentralWidget(central)

# === Export Button ===
button_layout = QtWidgets.QHBoxLayout()

export_top_btn = QtWidgets.QPushButton("Export Top Plot")
export_bottom_btn = QtWidgets.QPushButton("Export Bottom Plot")

button_layout.addWidget(export_top_btn)
button_layout.addWidget(export_bottom_btn)

layout.addLayout(button_layout)

# === Plot Widget ===
plot_widget = pg.GraphicsLayoutWidget()
plot_widget.setBackground('k')
layout.addWidget(plot_widget)

# === Initial ranges ===
plot1_y_init = (-0.1, 0.1)

# Use both generated request and SDAS request to set a sensible Y init
req_min = float(np.nanmin([vertical_request_generated.min(), sdas_interp.min()]))
req_max = float(np.nanmax([vertical_request_generated.max(), sdas_interp.max()]))
if np.isfinite(req_min) and np.isfinite(req_max) and req_min != req_max:
    plot2_y_init = (req_min, req_max)
else:
    plot2_y_init = (-1.0, 1.0)

plot1_center_init = sum(plot1_y_init) / 2
plot2_center_init = sum(plot2_y_init) / 2
plot1_height_init = plot1_y_init[1] - plot1_y_init[0]
plot2_height_init = plot2_y_init[1] - plot2_y_init[0]

# === Sync Flag ===
syncing = False

# === Plot 1: PositionZ vs Reference (Domenica comparison) ===
plot1 = plot_widget.addPlot(title="Vertical Position")
plot1.setLabel('left', 'Z [m]')
plot1.setLabel('bottom', 'Time [ms]')
plot1.setXRange(time_min, time_max)
plot1.setLimits(xMin=time_min, xMax=time_max)
plot1.setYRange(*plot1_y_init)
plot1.addLegend()

plot1.plot(time_csv_ms, position_z, pen=pg.mkPen('c', width=2), name="PositionZ")
plot1.plot(time_csv_ms, vertical_ref, pen=pg.mkPen('m', width=2, style=QtCore.Qt.DashLine), name="Reference")

plot1.addItem(pg.InfiniteLine(pos=0, angle=0, pen=pg.mkPen('w', width=1, style=QtCore.Qt.DashLine)))
plot1.addItem(pg.InfiniteLine(pos=0.085, angle=0, pen=pg.mkPen('r', width=2, style=QtCore.Qt.DotLine)))
plot1.addItem(pg.InfiniteLine(pos=-0.085, angle=0, pen=pg.mkPen('r', width=2, style=QtCore.Qt.DotLine)))

# === Plot 2: Vertical current request comparison (Generated vs SDAS ch126) ===
plot_widget.nextRow()
plot2 = plot_widget.addPlot(title="Vertical Current Request")
plot2.setLabel('left', 'Current [A]')
plot2.setLabel('bottom', 'Time [ms]')
plot2.setXRange(time_min, time_max)
plot2.setLimits(xMin=time_min, xMax=time_max)
plot2.setYRange(*plot2_y_init)
plot2.addLegend()

plot2.plot(time_csv_ms, vertical_request_generated, pen=pg.mkPen('y', width=2), name="Simulated (CSV)")
plot2.plot(time_csv_ms, sdas_interp, pen=pg.mkPen('w', width=2, style=QtCore.Qt.DashLine), name="Actual (SDAS)")

# === Make plots look more scientific ===
plot1.showGrid(x=True, y=True, alpha=0.3)
plot2.showGrid(x=True, y=True, alpha=0.3)

# === Sync logic (bidirectional) ===
def sync(source, target, source_init_center, source_init_height,
         target_init_center, target_init_height):
    global syncing
    if syncing:
        return
    syncing = True

    xr, yr = source.vb.viewRange()
    source_center = (yr[0] + yr[1]) / 2
    source_height = yr[1] - yr[0]

    # Compute relative scale and offset
    scale = source_height / source_init_height if source_init_height != 0 else 1.0
    offset = source_center - source_init_center

    # Apply to target
    new_center = target_init_center + offset
    new_height = target_init_height * scale
    target.vb.setRange(
        xRange=xr,
        yRange=(new_center - new_height / 2, new_center + new_height / 2),
        padding=0
    )

    syncing = False

# === Export function ===
def export_plot_top():
    options = QtWidgets.QFileDialog.Options()
    default_name = os.path.join(
        os.path.expanduser("~"),
        "git-repos/MARTe2-WaterTank/DataVisualization/Outputs/VerticalControlPlots/",
        f"vertical_position_{shot_number}.png"
    )

    file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
        main_window,
        "Export Top Plot...",
        default_name,
        "PNG Files (*.png);;All Files (*)",
        options=options
    )

    if file_path:
        exporter = pg.exporters.ImageExporter(plot1)
        exporter.export(file_path)


def export_plot_bottom():
    options = QtWidgets.QFileDialog.Options()
    default_name = os.path.join(
        os.path.expanduser("~"),
        "git-repos/MARTe2-WaterTank/DataVisualization/Outputs/VerticalControlPlots/",
        f"vertical_current_{shot_number}.png"
    )

    file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
        main_window,
        "Export Bottom Plot...",
        default_name,
        "PNG Files (*.png);;All Files (*)",
        options=options
    )

    if file_path:
        exporter = pg.exporters.ImageExporter(plot2)
        exporter.export(file_path)

export_top_btn.clicked.connect(export_plot_top)
export_bottom_btn.clicked.connect(export_plot_bottom)

# Connect both ways
plot1.sigRangeChanged.connect(lambda: sync(plot1, plot2, plot1_center_init, plot1_height_init, plot2_center_init, plot2_height_init))
plot2.sigRangeChanged.connect(lambda: sync(plot2, plot1, plot2_center_init, plot2_height_init, plot1_center_init, plot1_height_init))

# === Show ===
main_window.showMaximized()
main_window.keyPressEvent = lambda e: app.quit() if e.key() == QtCore.Qt.Key_Escape else None
sys.exit(app.exec_())

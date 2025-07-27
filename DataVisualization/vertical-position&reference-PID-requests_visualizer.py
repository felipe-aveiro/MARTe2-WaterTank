import sys
import os
import re
import pandas as pd
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets, QtCore, QtGui
import pyqtgraph.exporters

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

# === Columns ===
time_col = f"#timeI ({dtype})[1]"
fused_z_col = f"outputFusedZ ({dtype})[1]"
vertical_ref_col = f"vertical_reference ({dtype})[1]"
vertical_current_request_col = f"vertical_current_request ({dtype})[1]"

for col in [time_col, fused_z_col, vertical_ref_col, vertical_current_request_col]:
    if col not in df.columns:
        sys.exit(f"Missing column: {col}")

# === Data ===
time = (df[time_col] - df[time_col].iloc[0]) * 1e3
fused_z = df[fused_z_col].values
vertical_ref = df[vertical_ref_col].values
vertical_request = df[vertical_current_request_col].values

time_min, time_max = time.min(), time.max()

# === Main Window ===
main_window = QtWidgets.QMainWindow()
central = QtWidgets.QWidget()
layout = QtWidgets.QVBoxLayout(central)
main_window.setCentralWidget(central)

# === Export Button ===
button_layout = QtWidgets.QHBoxLayout()
export_btn = QtWidgets.QPushButton("Export Both Plots")
button_layout.addWidget(export_btn)
layout.addLayout(button_layout)

# === Plot Widget ===
plot_widget = pg.GraphicsLayoutWidget()
plot_widget.setBackground('k')
layout.addWidget(plot_widget)

# === Initial ranges ===
plot1_y_init = (-0.1, 0.1)
plot2_y_init = (vertical_request.min(), vertical_request.max())
plot1_center_init = sum(plot1_y_init) / 2
plot2_center_init = sum(plot2_y_init) / 2
plot1_height_init = plot1_y_init[1] - plot1_y_init[0]
plot2_height_init = plot2_y_init[1] - plot2_y_init[0]

# === Sync Flag ===
syncing = False

# === Plot1 ===
plot1 = plot_widget.addPlot(title="Vertical Position vs Reference")
plot1.setXRange(time_min, time_max)
plot1.setLimits(xMin=time_min, xMax=time_max)
plot1.setYRange(*plot1_y_init)
plot1.addLegend()
plot1.plot(time, fused_z, pen=pg.mkPen('c', width=2), name="Fused Z")
plot1.plot(time, vertical_ref, pen=pg.mkPen('m', width=2, style=QtCore.Qt.DashLine), name="Reference")
plot1.addItem(pg.InfiniteLine(pos=0, angle=0, pen=pg.mkPen('w', width=1, style=QtCore.Qt.DashLine)))
plot1.addItem(pg.InfiniteLine(pos=0.085, angle=0, pen=pg.mkPen('r', width=2, style=QtCore.Qt.DotLine)))
plot1.addItem(pg.InfiniteLine(pos=-0.085, angle=0, pen=pg.mkPen('r', width=2, style=QtCore.Qt.DotLine)))

# === Plot2 ===
plot_widget.nextRow()
plot2 = plot_widget.addPlot(title="Vertical Current Request")
plot2.setXRange(time_min, time_max)
plot2.setLimits(xMin=time_min, xMax=time_max)
plot2.setYRange(*plot2_y_init)
plot2.plot(time, vertical_request, pen=pg.mkPen('y', width=2))

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
    scale = source_height / source_init_height
    offset = source_center - source_init_center

    # Apply to target
    new_center = target_init_center + offset
    new_height = target_init_height * scale
    target.vb.setRange(xRange=xr, yRange=(new_center - new_height/2, new_center + new_height/2), padding=0)

    syncing = False

# === Export function ===
def export_plots():
    options = QtWidgets.QFileDialog.Options()
    default_name = os.path.join(os.path.expanduser("~"), "git-repos/MARTe2-WaterTank/DataVisualization/Outputs/VerticalControlPlots/", f"vertical_control_plots_{shot_number}.png")
    file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
        main_window,
        "Export Plots As...",
        default_name,
        "PNG Files (*.png);;All Files (*)",
        options=options
    )
    if file_path:
        exporter = pg.exporters.ImageExporter(plot_widget.scene())
        exporter.export(file_path)
        QtWidgets.QMessageBox.information(main_window, "Export Successful", f"Plots saved to:\n{file_path}")

export_btn.clicked.connect(export_plots)

# Connect both ways
plot1.sigRangeChanged.connect(lambda: sync(plot1, plot2, plot1_center_init, plot1_height_init, plot2_center_init, plot2_height_init))
plot2.sigRangeChanged.connect(lambda: sync(plot2, plot1, plot2_center_init, plot2_height_init, plot1_center_init, plot1_height_init))

# === Show ===
main_window.showMaximized()
main_window.keyPressEvent = lambda e: app.quit() if e.key() == QtCore.Qt.Key_Escape else None
sys.exit(app.exec_())

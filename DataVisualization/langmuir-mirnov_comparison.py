import sys
import os
import pandas as pd
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets, QtCore

# === Start Qt app FIRST ===
app = QtWidgets.QApplication(sys.argv)

# === File dialog to select CSV ===
csv_path, _ = QtWidgets.QFileDialog.getOpenFileName(
    None,
    "Open CSV File",
    "/home/felipe/git-repos/MARTe2-WaterTank/DataVisualization/Outputs/",
    "CSV Files (*.csv);;All Files (*)"
)

if not csv_path:
    QtWidgets.QMessageBox.critical(None, "Error", "No CSV file selected. Exiting.")
    sys.exit()

# === Try loading CSV ===
try:
    with open(csv_path, 'r') as f:
        header_line = f.readline()

    semicolon_count = header_line.count(']') - header_line.count('];')
    comma_count = header_line.count(']') - header_line.count('],')

    delimiter = ';' if semicolon_count < comma_count else ','
    df = pd.read_csv(csv_path, delimiter=delimiter)
    df.columns = df.columns.str.strip()

except Exception as e:
    QtWidgets.QMessageBox.critical(None, "Error loading CSV", f"An error occurred:\n{e}")
    sys.exit()

# === Identify relevant columns ===
time_col = "#timeI (float64)[1]"
mpr_col = "outputMpR (float64)[1]"
mpz_col = "outputMpZ (float64)[1]"
epr_col = "outputEpR (float64)[1]"
epz_col = "outputEpZ (float64)[1]"

required_columns = [time_col, mpr_col, mpz_col, epr_col, epz_col]
missing = [col for col in required_columns if col not in df.columns]
if missing:
    QtWidgets.QMessageBox.critical(None, "Missing Columns", f"Missing required columns:\n{missing}")
    sys.exit()

# === Prepare time in ms ===
time = (df[time_col] - df[time_col].iloc[0]) * 1e3
time_min, time_max = time.min(), time.max()

# === Main window and layout ===
main_window = QtWidgets.QMainWindow()
main_window.setWindowTitle("Magnetic Coils vs Electric Probes Position Comparison")
central_widget = QtWidgets.QWidget()
main_layout = QtWidgets.QVBoxLayout()
central_widget.setLayout(main_layout)
main_window.setCentralWidget(central_widget)

plot_widget = pg.GraphicsLayoutWidget()
main_layout.addWidget(plot_widget)

# === Plot 1: Radial Position ===
plot_r = plot_widget.addPlot(title="Radial Position: Magnetic Coils vs Electric Probes")
plot_r.setLabel('bottom', 'Time [ms]')
plot_r.setLabel('left', 'R [m]')
plot_r.setXRange(time_min, time_max, padding=0)
plot_r.setLimits(xMin=time_min, xMax=time_max)
plot_r.setYRange(0.46-0.1, 0.46+0.1)
plot_r.addLegend()
zero_lineR_center = pg.InfiniteLine(pos=0.46, angle=0, pen=pg.mkPen('w', width=1, style=QtCore.Qt.DashLine))
zero_lineR_upper = pg.InfiniteLine(pos=0.46+0.085, angle=0, pen=pg.mkPen('r', width=2, style=QtCore.Qt.DotLine))
zero_lineR_lower = pg.InfiniteLine(pos=0.46-0.085, angle=0, pen=pg.mkPen('r', width=2, style=QtCore.Qt.DotLine))
plot_r.addItem(zero_lineR_center)
plot_r.addItem(zero_lineR_upper)
plot_r.addItem(zero_lineR_lower)
plot_r.plot(time, df[mpr_col], pen='c', name="Magnetic Coils")
plot_r.plot(time, df[epr_col], pen='y', name="Electric Probes")

plot_widget.nextRow()

# === Plot 2: Vertical Position ===
plot_z = plot_widget.addPlot(title="Vertical Position: Magnetic Coils vs Electric Probes")
plot_z.setLabel('bottom', 'Time [ms]')
plot_z.setLabel('left', 'Z [m]')
plot_z.setXRange(time_min, time_max, padding=0)
plot_z.setLimits(xMin=time_min, xMax=time_max)
plot_z.setYRange(-0.1, 0.1)
plot_z.addLegend()
zero_lineZ_center = pg.InfiniteLine(pos=0, angle=0, pen=pg.mkPen('w', width=1, style=QtCore.Qt.DashLine))
zero_lineZ_upper = pg.InfiniteLine(pos=0.085, angle=0, pen=pg.mkPen('r', width=2, style=QtCore.Qt.DotLine))
zero_lineZ_lower = pg.InfiniteLine(pos=-0.085, angle=0, pen=pg.mkPen('r', width=2, style=QtCore.Qt.DotLine))
plot_z.addItem(zero_lineZ_center)
plot_z.addItem(zero_lineZ_upper)
plot_z.addItem(zero_lineZ_lower)
plot_z.plot(time, df[mpz_col], pen='m', name="Magnetic Coils")
plot_z.plot(time, df[epz_col], pen='g', name="Electric Probes")

# === Link X axis ===
plot_r.setXLink(plot_z)

# === Synchronize Y-axis zoom/pan ===
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

r_center = (plot_r.vb.viewRange()[1][0] + plot_r.vb.viewRange()[1][1]) / 2
z_center = (plot_z.vb.viewRange()[1][0] + plot_z.vb.viewRange()[1][1]) / 2
offset_r_to_z = z_center - r_center
offset_z_to_r = r_center - z_center

plot_r.vb.sigYRangeChanged.connect(lambda: sync_y_range(plot_r, plot_z, offset_r_to_z))
plot_z.vb.sigYRangeChanged.connect(lambda: sync_y_range(plot_z, plot_r, offset_z_to_r))

# === Show window and run ===
main_window.showMaximized()
main_window.keyPressEvent = lambda event: app.quit() if event.key() == QtCore.Qt.Key_Escape else None
sys.exit(app.exec_())

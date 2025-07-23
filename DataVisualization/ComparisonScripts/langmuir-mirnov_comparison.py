import sys
import os
import pandas as pd
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets, QtCore, QtGui
from pyqtgraph.exporters import ImageExporter
import re


# === Start Qt app FIRST ===
app = QtWidgets.QApplication(sys.argv)

custom_legend_items = []

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

# === Identify shot nº ===
csv_filename = os.path.basename(csv_path)
use_float32 = "Atca" in csv_filename
dtype = "float32" if use_float32 else "float64"
match = re.search(r'(\d{5})', csv_filename)
shot_number = match.group(1) if match else "unknown"

# === Identify relevant columns ===
time_col = f"#timeI ({dtype})[1]"
mpr_col = f"outputMpR ({dtype})[1]"
mpz_col = f"outputMpZ ({dtype})[1]"
epr_col = f"outputEpR ({dtype})[1]"
epz_col = f"outputEpZ ({dtype})[1]"

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

button_layout = QtWidgets.QHBoxLayout()
export_r_btn = QtWidgets.QPushButton("Export Langmuir Comparison Radial Plot")
export_z_btn = QtWidgets.QPushButton("Export Langmuir Comparison Vertical Plot")
button_layout.addWidget(export_r_btn)
button_layout.addWidget(export_z_btn)
main_layout.addLayout(button_layout)

plot_widget = pg.GraphicsLayoutWidget()
# === TEMPORARY SIZE FOR EXPORT PREVIEW ========================================================================
plot_widget.setFixedSize(800,400)
# === REMOVE AFTER EXTRACTING RELEVANT PLOTS ===================================================================
main_layout.addWidget(plot_widget)
export_r_btn.show()
export_z_btn.show()

bold_font = QtGui.QFont("Arial", 11, QtGui.QFont.Bold)

# === Plot 1: Radial Position ===
plot_r = plot_widget.addPlot(title="Time Evolution of Estimated Plasma Radial Position - Magnetic Reconstruction vs Electric Reconstruction")
plot_r.titleLabel.item.setFont(QtGui.QFont("Arial", 14, QtGui.QFont.Bold))
plot_r.setLabel('bottom', 'Time [ms]')
plot_r.setLabel('left', 'R [m]')
plot_r.getAxis("bottom").label.setFont(bold_font)
plot_r.getAxis("left").label.setFont(bold_font)
#plot_r.setXRange(time_min, time_max, padding=0)
plot_r.setXRange(160, 400, padding=0)
plot_r.setLimits(xMin=time_min, xMax=time_max)
plot_r.setYRange(0.46-0.1, 0.46+0.1)
plot_r.addLegend()


zero_lineR_center = pg.InfiniteLine(pos=0.46, angle=0, pen=pg.mkPen('w', width=1, style=QtCore.Qt.DashLine))
zero_lineR_upper = pg.InfiniteLine(pos=0.46+0.085, angle=0, pen=pg.mkPen('r', width=2, style=QtCore.Qt.DotLine))
zero_lineR_lower = pg.InfiniteLine(pos=0.46-0.085, angle=0, pen=pg.mkPen('r', width=2, style=QtCore.Qt.DotLine))
plot_r.addItem(zero_lineR_center)
plot_r.addItem(zero_lineR_upper)
plot_r.addItem(zero_lineR_lower)

plot_widget.nextRow()

# === Plot 2: Vertical Position ===
plot_z = plot_widget.addPlot(title="Time Evolution of Estimated Plasma Vertical Position - Magnetic Reconstruction vs Electric Reconstruction")
plot_z.titleLabel.item.setFont(QtGui.QFont("Arial", 14, QtGui.QFont.Bold))
plot_z.setLabel('bottom', 'Time [ms]')
plot_z.setLabel('left', 'Z [m]')
plot_z.getAxis("bottom").label.setFont(bold_font)
plot_z.getAxis("left").label.setFont(bold_font)
#plot_z.setXRange(time_min, time_max, padding=0)
plot_z.setXRange(160, 400, padding=0)
plot_z.setLimits(xMin=time_min, xMax=time_max)
plot_z.setYRange(-0.1, 0.1)
plot_z.addLegend()


zero_lineZ_center = pg.InfiniteLine(pos=0, angle=0, pen=pg.mkPen('w', width=1, style=QtCore.Qt.DashLine))
zero_lineZ_upper = pg.InfiniteLine(pos=0.085, angle=0, pen=pg.mkPen('r', width=2, style=QtCore.Qt.DotLine))
zero_lineZ_lower = pg.InfiniteLine(pos=-0.085, angle=0, pen=pg.mkPen('r', width=2, style=QtCore.Qt.DotLine))
plot_z.addItem(zero_lineZ_center)
plot_z.addItem(zero_lineZ_upper)
plot_z.addItem(zero_lineZ_lower)

x_offset = 70
y_offset = 30
spacing = 120
legend_font = QtGui.QFont("Arial", 10)

curves_r = [
    (plot_r.plot(time, df[mpr_col], pen=pg.mkPen('m', width=2)), "Magnetic Coils"),
    (plot_r.plot(time, df[epr_col], pen=pg.mkPen('g', width=2)), "Electric Probes")
]

curves_z = [
    (plot_z.plot(time, df[mpz_col], pen=pg.mkPen('m', width=2)), "Magnetic Coils"),
    (plot_z.plot(time, df[epz_col], pen=pg.mkPen('g', width=2)), "Electric Probes")
]

for i, (curve, label) in enumerate(curves_r):
    # Sample color box
    sample = pg.graphicsItems.LegendItem.ItemSample(curve)
    sample.setParentItem(plot_r.graphicsItem())
    legend_y = y_offset + i * 20
    sample.setPos(x_offset, legend_y)
    custom_legend_items.append(sample)

    # Text label
    text = pg.TextItem(label, anchor=(0, 0), color='w')
    text.setFont(legend_font)
    text.setParentItem(plot_r.graphicsItem())
    text.setPos(x_offset + 25, legend_y)
    custom_legend_items.append(text)

for i, (curve, label) in enumerate(curves_z):
    sample = pg.graphicsItems.LegendItem.ItemSample(curve)
    sample.setParentItem(plot_z.graphicsItem())
    legend_y = y_offset + i * 20
    sample.setPos(x_offset, legend_y)
    custom_legend_items.append(sample)

    text = pg.TextItem(label, anchor=(0, 0), color='w')
    text.setFont(legend_font)
    text.setParentItem(plot_z.graphicsItem())
    text.setPos(x_offset + 25, legend_y)
    custom_legend_items.append(text)
    
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

def export_plot_with_dialog(suggested_name, target):
    options = QtWidgets.QFileDialog.Options()
    file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
        main_window,
        "Save Plot As...",
        os.path.join(os.path.expanduser("~"), "git-repos/MARTe2-WaterTank/DataVisualization/Outputs/PositionComparison/", suggested_name),
        "PNG Files (*.png);;All Files (*)",
        options=options
    )
    if file_path:
        exporter = ImageExporter(target)
        exporter.export(file_path)

suffix = "_float32" if use_float32 else ""

export_r_btn.clicked.connect(lambda: export_plot_with_dialog(f"langmuir_comparison_radial_plot_shot_{shot_number}{suffix}.png", plot_r))
export_z_btn.clicked.connect(lambda: export_plot_with_dialog(f"langmuir_comparison_vertical_plot_shot_{shot_number}{suffix}.png", plot_z))

# === Show window and run ===
main_window.showMaximized()
main_window.keyPressEvent = lambda event: app.quit() if event.key() == QtCore.Qt.Key_Escape else None
sys.exit(app.exec_())

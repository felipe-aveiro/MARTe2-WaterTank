from pyqtgraph.Qt import QtWidgets, QtCore, QtGui
import pyqtgraph as pg
import numpy as np
import sys
import os
import pandas as pd
import pyqtgraph.exporters

# === 1. Load CSV with coefficients per shot ===
csv_path = '/home/felipe/git-repos/MARTe2-WaterTank/DataVisualization/Outputs/langmuir_coeficients.csv'
df = pd.read_csv(csv_path)

# === 2. Define weights based on plasma behavior quality (AC pulse stability, symmetry, etc.) ===
# Higher weights represent better performance and relevance for defining global coefficients
shot_weights = {
    45754: 1.35, # Multiple AC pulses, but irregular shape and premature endings
    45967: 3.0, # Several perfect positive pulses, all nominal current
    46241: 3.0, # Best overall, perfect regular AC pulses, ideal case
    52856: 1.0, # Two AC pulses, below nominal and irregular
    52857: 1.35, # Six AC pulses, below nominal and irregular
    53058: 2.06, # One positive + three negatives, nominal current, some irregularity
    53071: 2.41, # One positive + two negatives, good regularity but slight current drop on negatives
    53099: 1.82, # Poor quality pulses, irregular current, below nominal
    53105: 2.06, # Single AC cycle, regular behavior but slightly under nominal current
    53197: 1.35, # Three AC pulses, well below nominal and irregular
}

# === 3. Map weights to the DataFrame ===
df['Weight'] = df['Shot'].astype(int).map(shot_weights)

# === 4. Filter only valid shots with defined weights ===
df_filtered = df.dropna(subset=['Weight']).copy()

# === 5. Compute weighted average of calibration coefficients ===
coeff_names = ['C1', 'C2', 'C3', 'C4']
total_weight = df_filtered['Weight'].sum()

# Dictionary to store the final weighted coefficients
weighted_coeffs = {
    name: (df_filtered[name] * df_filtered['Weight']).sum() / total_weight
    for name in coeff_names
}

C1 = weighted_coeffs['C1']
C2 = weighted_coeffs['C2']
C3 = weighted_coeffs['C3']
C4 = weighted_coeffs['C4']

# === Data range ===
deltaV_R = np.linspace(-5000, 5000, 200)
deltaV_Z = np.linspace(-5000, 5000, 200)

# Convert positions to cm
Rp_cm = (C1 * deltaV_R + C2) * 100
Zp_cm = (C3 * deltaV_Z + C4) * 100

# Center and limits in cm
R_center_cm = 0.46 * 100
Z_center_cm = 0.0
R_min, R_max = R_center_cm - 10, R_center_cm + 10
Z_min, Z_max = Z_center_cm - 10, Z_center_cm + 10

# Physical limits ±8.5 cm
R_upper = R_center_cm + 8.5
R_lower = R_center_cm - 8.5
Z_upper = Z_center_cm + 8.5
Z_lower = Z_center_cm - 8.5

# === Start PyQtGraph App ===
app = QtWidgets.QApplication(sys.argv)
main_window = QtWidgets.QMainWindow()
win = pg.GraphicsLayoutWidget(title="Position Models with Physical Limits")

central_widget = QtWidgets.QWidget()
main_layout = QtWidgets.QVBoxLayout()
main_layout.addWidget(win)

central_widget.setLayout(main_layout)
main_window.setCentralWidget(central_widget)
win.setFixedSize(1200,350)

button_layout = QtWidgets.QHBoxLayout()
export1_btn = QtWidgets.QPushButton("Export Radial Model")
export2_btn = QtWidgets.QPushButton("Export Vertical Model")

button_layout.addWidget(export1_btn)
button_layout.addWidget(export2_btn)
main_layout.addLayout(button_layout)

# === Plot 1: Radial ===
plot_r = win.addPlot(title="Radial Position Langmuir Model")
plot_r.titleLabel.item.setFont(QtGui.QFont("Arial", 14, QtGui.QFont.Bold))
plot_r.setLabel('bottom', 'ΔV [V]')
plot_r.setLabel('left', 'R [cm]')
bold_font = QtGui.QFont("Arial", 11, QtGui.QFont.Bold)
plot_r.getAxis("bottom").label.setFont(bold_font)
plot_r.getAxis("left").label.setFont(bold_font)
plot_r.setYRange(R_min, R_max)
plot_r.setXRange(-1200, 1200)
plot_r.showGrid(x=True, y=True)

# Curve for R
curve_r = pg.PlotCurveItem(deltaV_R, Rp_cm, pen=pg.mkPen('b', width=2))
plot_r.addItem(curve_r)

# Horizontal lines (physical limits)
line_r_upper = pg.InfiniteLine(pos=R_upper, angle=0, pen=pg.mkPen('r', width=1, style=QtCore.Qt.DashLine))
line_r_lower = pg.InfiniteLine(pos=R_lower, angle=0, pen=pg.mkPen('r', width=1, style=QtCore.Qt.DashLine))
plot_r.addItem(line_r_upper)
plot_r.addItem(line_r_lower)

# === Plot 2: Vertical ===
plot_z = win.addPlot(title="Vertical Position Langmuir Model")
plot_z.titleLabel.item.setFont(QtGui.QFont("Arial", 14, QtGui.QFont.Bold))
plot_z.setLabel('bottom', 'ΔV [V]')
plot_z.setLabel('left', 'Z [cm]')
plot_z.getAxis("bottom").label.setFont(bold_font)
plot_z.getAxis("left").label.setFont(bold_font)
plot_z.setYRange(Z_min, Z_max)
plot_z.setXRange(-1200, 1200)
plot_z.showGrid(x=True, y=True)

# Curve for Z
curve_z = pg.PlotCurveItem(deltaV_Z, Zp_cm, pen=pg.mkPen('orange', width=2))
plot_z.addItem(curve_z)

# Horizontal lines (physical limits)
line_z_upper = pg.InfiniteLine(pos=Z_upper, angle=0, pen=pg.mkPen('r', width=1, style=QtCore.Qt.DashLine))
line_z_lower = pg.InfiniteLine(pos=Z_lower, angle=0, pen=pg.mkPen('r', width=1, style=QtCore.Qt.DashLine))
plot_z.addItem(line_z_upper)
plot_z.addItem(line_z_lower)

plot_r.setXLink(plot_z)

# Legends
custom_legend_items = []
x_offset = 250
y_offset = 40
spacing = 600
legend_font = QtGui.QFont("Arial", 10)

legend_items = [
    (curve_r, f"R = ({C1:.5e}) * ΔV + ({C2:.5e})"),
    (curve_z, f"Z = ({C3:.5e}) * ΔV + ({C4:.5e})")
]

for i, (curve, label) in enumerate(legend_items):
    legend_x = x_offset + i * spacing
    sample = pg.graphicsItems.LegendItem.ItemSample(curve)
    sample.setParentItem(plot_r.graphicsItem())  # attach to first plot
    sample.setPos(legend_x, y_offset)
    custom_legend_items.append(sample)

    text = pg.TextItem(label, anchor=(0, 0), color='w')
    text.setFont(legend_font)
    text.setParentItem(plot_r.graphicsItem())
    text.setPos(legend_x + 25, y_offset)
    custom_legend_items.append(text)

def export_plot_with_dialog(plot, suggested_name):
    options = QtWidgets.QFileDialog.Options()
    file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
        main_window,
        "Save Plot As...",
        os.path.join(os.path.expanduser("~"), "git-repos/MARTe2-WaterTank/DataVisualization/Outputs/LangmuirModelPlots/", suggested_name),
        "PNG Files (*.png);;All Files (*)",
        options=options
    )
    if file_path:
        exporter = pg.exporters.ImageExporter(plot)
        exporter.export(file_path)


export1_btn.clicked.connect(lambda: export_plot_with_dialog(plot_r, f"radial-langmuir-model.png"))
export2_btn.clicked.connect(lambda: export_plot_with_dialog(plot_z, f"vertical-langmuir-model.png"))

# Escape to close window
def keyPressEvent(event):
    if event.key() == QtCore.Qt.Key_Escape:
        app.quit()

main_window.keyPressEvent = keyPressEvent

# Execute
if __name__ == '__main__':
    main_window.show()
    QtWidgets.QApplication.instance().exec_()

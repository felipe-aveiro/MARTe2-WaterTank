import sys
import os
import pandas as pd
import numpy as np
from pyqtgraph.Qt import QtWidgets, QtCore, QtGui
import pyqtgraph as pg

# === CONFIGURATION ===
shots_weights = {
    45754: 1.0,
    45967: 2.0,
    46241: 3.0,
    53071: 1.5,
    53099: 0.5,
    53105: 1.5
}

base_path = "/home/felipe/git-repos/MARTe2-WaterTank/DataVisualization/Outputs/"
csv_template = "IsttokOutput_Tesla_{}.csv"

# Physical limits
a = 0.085
R0 = 0.46
rp_min, rp_max = R0 - a, R0 + a
zp_min, zp_max = -a, a

# Arrays for data
all_Rp_EP, all_Zp_EP, all_weights_LP = [], [], []
all_Rp_MP, all_Zp_MP, all_weights_MP = [], [], []

# === Load data for all shots ===
for shot, weight in shots_weights.items():
    filepath = os.path.join(base_path, csv_template.format(shot))
    try:
        df = pd.read_csv(filepath, delimiter=';')

        # Langmuir
        Rp_LP = df["outputEpR (float64)[1]"].values
        Zp_LP = df["outputEpZ (float64)[1]"].values
        mask_LP = ~np.isnan(Rp_LP) & ~np.isnan(Zp_LP)
        Rp_LP, Zp_LP = Rp_LP[mask_LP], Zp_LP[mask_LP]

        # Mirnov
        Rp_MP = df["outputMpR (float64)[1]"].values
        Zp_MP = df["outputMpZ (float64)[1]"].values
        mask_MP = ~np.isnan(Rp_MP) & ~np.isnan(Zp_MP)
        Rp_MP, Zp_MP = Rp_MP[mask_MP], Zp_MP[mask_MP]

        # Apply physical range filter
        mask_LP = (Rp_LP > rp_min) & (Rp_LP < rp_max) & (Zp_LP > zp_min) & (Zp_LP < zp_max)
        Rp_LP, Zp_LP = Rp_LP[mask_LP], Zp_LP[mask_LP]

        mask_MP = (Rp_MP > rp_min) & (Rp_MP < rp_max) & (Zp_MP > zp_min) & (Zp_MP < zp_max)
        Rp_MP, Zp_MP = Rp_MP[mask_MP], Zp_MP[mask_MP]

        # Append data
        all_Rp_EP.extend(Rp_LP)
        all_Zp_EP.extend(Zp_LP)
        all_weights_LP.extend([weight] * len(Rp_LP))

        all_Rp_MP.extend(Rp_MP)
        all_Zp_MP.extend(Zp_MP)
        all_weights_MP.extend([weight] * len(Rp_MP))

    except Exception as e:
        print(f"Failed to process shot {shot}: {e}")

# Convert to numpy arrays
all_Rp_EP, all_Zp_EP = np.array(all_Rp_EP), np.array(all_Zp_EP)
all_Rp_MP, all_Zp_MP = np.array(all_Rp_MP), np.array(all_Zp_MP)

# === PyQtGraph APP ===
app = QtWidgets.QApplication(sys.argv)
win = pg.GraphicsLayoutWidget(title="Plasma Position Estimates")
# === TEMPORARY SIZE FOR EXPORT PREVIEW ========================================================================
win.setFixedSize(700,350) # (800, 400) for position plots
# === REMOVE AFTER EXTRACTING RELEVANT PLOTS ===================================================================
win.setFixedSize(800,400)
win.showMaximized()

bold_font = QtGui.QFont("Arial", 11, QtGui.QFont.Bold)

plot = win.addPlot(title="Plasma Position Estimates: Mirnov vs Langmuir")
plot.titleLabel.item.setFont(QtGui.QFont("Arial", 14, QtGui.QFont.Bold))
plot.setLabel('bottom', 'Radial Position [m]')
plot.setLabel('left', 'Vertical Position [m]')
plot.getAxis("bottom").label.setFont(bold_font)
plot.getAxis("left").label.setFont(bold_font)
plot.showGrid(x=True, y=True)

# Scatter plots
mirnov_scatter = pg.ScatterPlotItem(
    x=all_Rp_MP, y=all_Zp_MP, pen=None, symbol='o',
    size=3, brush=pg.mkBrush(0, 0, 255, 150)  # Blue
)
langmuir_scatter = pg.ScatterPlotItem(
    x=all_Rp_EP, y=all_Zp_EP, pen=None, symbol='o',
    size=3, brush=pg.mkBrush(255, 140, 0, 150)  # Orange
)

plot.addItem(mirnov_scatter)
plot.addItem(langmuir_scatter)
plot.setXRange(rp_min - 0.01, rp_max + 0.01)
plot.setYRange(zp_min - 0.01, zp_max + 0.01)
plot.setLimits(xMin=rp_min - 0.01, xMax=rp_max + 0.01, yMin=zp_min - 0.01, yMax=zp_max + 0.01)

# Add physical boundary as a dashed rectangle
rect = QtWidgets.QGraphicsRectItem(rp_min, zp_min, rp_max - rp_min, zp_max - zp_min)
rect.setPen(pg.mkPen('r', width=2, style=QtCore.Qt.DashLine))
plot.addItem(rect)

# === Custom Legend ===
x_offset = 70   # Distance from left
y_offset = 27   # Distance from top
spacing = 140    # Vertical spacing between legend items
legend_font = QtGui.QFont("Arial", 12)

legend_items = [
    (mirnov_scatter, "Mirnov Coils"),
    (langmuir_scatter, "Langmuir Probes")
]

for i, (item, label) in enumerate(legend_items):
    # Sample color box
    legend_x = x_offset + i * spacing
    sample = pg.ScatterPlotItem(
        x=[82 + i * 140], y=[37], size=8,
        brush=item.opts['brush'], pen=None
    )
    sample.setParentItem(plot.graphicsItem())

    # Text label
    text = pg.TextItem(label, anchor=(0, 0), color='gray')
    text.setFont(legend_font)
    text.setParentItem(plot.graphicsItem())
    text.setPos(legend_x + 25, y_offset)

def keyPressEvent(event):
    if event.key() == QtCore.Qt.Key_Escape:
        QtWidgets.QApplication.quit()
win.keyPressEvent = keyPressEvent

# Add button to save figure
btn = QtWidgets.QPushButton('Save Scatter Plot')
proxy = QtWidgets.QGraphicsProxyWidget()
layout = QtWidgets.QVBoxLayout()
layout.addWidget(win)
layout.addWidget(btn)
container = QtWidgets.QWidget()
container.setLayout(layout)
container.showMaximized()

def save_plot():
    exporter = pg.exporters.ImageExporter(plot)
    exporter.export('/home/felipe/git-repos/MARTe2-WaterTank/DataVisualization/Outputs/CovarianceScatterPlots/scatter-plot.png')
    print("Plot saved to Desktop!")
btn.clicked.connect(save_plot)

if __name__ == '__main__':
    QtWidgets.QApplication.instance().exec_()

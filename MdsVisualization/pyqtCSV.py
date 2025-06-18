import sys
import os
import pandas as pd
import csv
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets, QtCore
import pyqtgraph.exporters

# === Start Qt app FIRST ===
app = QtWidgets.QApplication(sys.argv)

# === Remember last directory ===
LAST_DIR_FILE = os.path.join(os.path.expanduser("~"), "git-repos/MARTe2-WaterTank/MdsVisualization/", "mirnov_viewer_last_dir.txt")
if os.path.exists(LAST_DIR_FILE):
    with open(LAST_DIR_FILE, "r") as f:
        last_dir = f.read().strip()
else:
    last_dir = ""

# === Ask user to open a CSV file ===
csv_path, _ = QtWidgets.QFileDialog.getOpenFileName(
    None,
    "Open CSV File",
    last_dir,
    "CSV Files (*.csv);;All Files (*)"
)

if not csv_path:
    QtWidgets.QMessageBox.critical(None, "Error", "No CSV file selected... Exiting.")
    sys.exit()

# === Save directory for future use ===
with open(LAST_DIR_FILE, "w") as f:
    f.write(os.path.dirname(csv_path))

# === Try loading CSV with reliable delimiter detection based on ']' separator ===
try:
    with open(csv_path, 'r') as f:
        header_line = f.readline()

    # Count delimiters that separate closing brackets
    semicolon_count = header_line.count(']') - header_line.count('];')
    comma_count = header_line.count(']') - header_line.count('],')

    delimiter = ';' if semicolon_count < comma_count else ','
    df = pd.read_csv(csv_path, delimiter=delimiter)
    df.columns = df.columns.str.strip()
    print(f"\nCSV loaded using delimiter: '{delimiter}'\n")

except Exception as e:
    QtWidgets.QMessageBox.critical(None, "Error loading CSV", f"An error occurred:\n{e}")
    sys.exit()


# === Identify columns ===
time_col = "#Time (uint32)[1]" # = df.columns[0]
mirnov_cols = [f"correctedMirnov{i} (float64)[1]" for i in range(12)] # = df.columns[i + 1] for i in range(12)
mpip_col = "outputMpIp (float64)[1]" # = df.columns[13]
time = df[time_col].values
time_min, time_max = time.min(), time.max()

# === App main window ===
main_window = QtWidgets.QMainWindow()
main_window.setWindowTitle("Mirnov coils + Plasma Current Magnetic Reconstruction Viewer")

# === Central layout ===
central_widget = QtWidgets.QWidget()
main_layout = QtWidgets.QVBoxLayout()
central_widget.setLayout(main_layout)
main_window.setCentralWidget(central_widget)

# === Export buttons ===
button_layout = QtWidgets.QHBoxLayout()
export1_btn = QtWidgets.QPushButton("Export Mirnov Plot")
export2_btn = QtWidgets.QPushButton("Export MpIp Plot")
button_layout.addWidget(export1_btn)
button_layout.addWidget(export2_btn)
main_layout.addLayout(button_layout)

# === Plot widget ===
plot_widget = pg.GraphicsLayoutWidget()
main_layout.addWidget(plot_widget, stretch=1)

# === Plot 1: Mirnov ===
plot1 = plot_widget.addPlot(title="correctedMirnov vs Time")
plot1.setLabel('bottom', 'Time [\u00b5s]')
plot1.setLabel('left', 'Magnetic Field [T]')
plot1.addLegend()
plot1.setXRange(time_min, time_max, padding=0)
plot1.setLimits(xMin=time_min, xMax=time_max)
plot1.setAutoVisible(y=True)
zero_line1 = pg.InfiniteLine(pos=0, angle=0, pen=pg.mkPen('w', width=1, style=QtCore.Qt.DashLine))
plot1.addItem(zero_line1)

colors = [
    'r', 'g', 'b', 'c', 'm', 'y',
    (255, 128, 0), (128, 0, 255), (0, 128, 128),
    (255, 0, 128), (0, 255, 128), (128, 128, 0)
]

for col, color in zip(mirnov_cols, colors):
    y = df[col].values
    plot1.plot(time, y, pen=pg.mkPen(color=color, width=1), name=col)

# === Plot 2: MpIp ===
plot_widget.nextRow()
plot2 = plot_widget.addPlot(title="outputMpIp vs Time")
plot2.setLabel('bottom', 'Time [\u00b5s]')
plot2.setLabel('left', 'Plasma Current [A]')
plot2.setXRange(time_min, time_max, padding=0)
plot2.setLimits(xMin=time_min, xMax=time_max)
plot2.setAutoVisible(y=True)
zero_line2 = pg.InfiniteLine(pos=0, angle=0, pen=pg.mkPen('w', width=1, style=QtCore.Qt.DashLine))
plot2.addItem(zero_line2)
plot2.plot(time, df[mpip_col].values, pen='r')

# === Plot 3: chopper_trigger ===
plot_widget.nextRow()
plot3 = plot_widget.addPlot(title="chopper_trigger vs Time")
plot3.setLabel('bottom', 'Time [\u00b5s]')
plot3.setLabel('left', 'Chopper Trigger')
plot3.setXRange(time_min, time_max, padding=0)
plot3.setLimits(xMin=time_min, xMax=time_max)
plot3.setYRange(0, 3)
plot3.setLimits(yMin=0, yMax=3)
plot3.setAutoVisible(y=False)
zero_line3 = pg.InfiniteLine(pos=0, angle=0, pen=pg.mkPen('w', width=1, style=QtCore.Qt.DashLine))
plot3.addItem(zero_line3)

chopper_col = "chopper_trigger (float64)[1]"
plot3.plot(time, df[chopper_col].values, pen=pg.mkPen('w', width=1))
plot3.getViewBox().setMinimumHeight(60)
plot3.setMaximumHeight(100)

# === Export logic ===
def export_plot_with_dialog(plot, suggested_name):
    options = QtWidgets.QFileDialog.Options()
    file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
        main_window,
        "Save Plot As...",
        os.path.join(os.path.dirname(csv_path), suggested_name),
        "PNG Files (*.png);;All Files (*)",
        options=options
    )
    if file_path:
        exporter = pg.exporters.ImageExporter(plot)
        exporter.export(file_path)

        # Floating confirmation
        message = QtWidgets.QLabel(f"✔ Successfully exported to:\n{file_path}")
        message.setStyleSheet("""
            background-color: #b2f2bb;
            color: black;
            padding: 6px 12px;
            border-radius: 6px;
            font-weight: bold;
        """)
        message.setParent(plot_widget)
        message.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        message.adjustSize()


        # Position top-right
        message.move(plot_widget.width() - message.width() - 20, 20)
        message.show()

        def reposition():
            message.move(plot_widget.width() - message.width() - 20, 20)
        plot_widget.resizeEvent = lambda e: reposition()

        QtCore.QTimer.singleShot(4000, message.deleteLater)

export1_btn.clicked.connect(lambda: export_plot_with_dialog(plot1, "mirnov_plot.png"))
export2_btn.clicked.connect(lambda: export_plot_with_dialog(plot2, "mpip_plot.png"))

# === ESC to quit ===
def handle_key(event):
    if event.key() == QtCore.Qt.Key_Escape:
        app.quit()
main_window.keyPressEvent = handle_key

# === Launch ===
main_window.showMaximized()
sys.exit(app.exec_())

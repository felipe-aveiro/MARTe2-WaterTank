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
    print(f"\n'{csv_path}' loaded using delimiter: '{delimiter}'\n")

except Exception as e:
    QtWidgets.QMessageBox.critical(None, "Error loading CSV", f"An error occurred:\n{e}")
    sys.exit()

# === Identify columns ===
time_col = "#timeI (float64)[1]" # = df.columns[0]
mirnov_cols = [f"inputMirnov{i} (float64)[1]" for i in range(12)] # = df.columns[i + 1] for i in range(12)
mpip_col = "outputMpIp (float64)[1]" # = df.columns[13]
mpr_col = "outputMpR (float64)[1]" # = df.columns[14]
mpz_col = "outputMpZ (float64)[1]" # = df.columns[15]
chopper_col = "chopper_trigger (float64)[1]" # = df.columns[16]
time = df[time_col].values * 1e6
time_min, time_max = time.min(), time.max()

main_window = QtWidgets.QMainWindow()
main_window.setWindowTitle("Magnetic Reconstruction Viewer")
central_widget = QtWidgets.QWidget()
main_layout = QtWidgets.QVBoxLayout()
central_widget.setLayout(main_layout)
main_window.setCentralWidget(central_widget)

button_layout = QtWidgets.QHBoxLayout()
export1_btn = QtWidgets.QPushButton("Export Mirnov Plot")
export2_btn = QtWidgets.QPushButton("Export Plasma Current Plot")
export3_btn = QtWidgets.QPushButton("Export Radial Position Plot")
export4_btn = QtWidgets.QPushButton("Export Vertical Position Plot")

for btn in (export3_btn, export4_btn):
    btn.hide()

button_layout.addWidget(export1_btn)
button_layout.addWidget(export2_btn)
button_layout.addWidget(export3_btn)
button_layout.addWidget(export4_btn)
main_layout.addLayout(button_layout)

plot_widget = pg.GraphicsLayoutWidget()
main_layout.addWidget(plot_widget, stretch=1)

def show_main_plots():
    plot_widget.clear()
    global plot1, plot2, plot3

    export1_btn.show()
    export2_btn.show()
    export3_btn.hide()
    export4_btn.hide()

    plot1 = plot_widget.addPlot(title="inputMirnov vs Time")
    plot1.setLabel('bottom', 'Time [µs]')
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

    plot_widget.nextRow()
    plot2 = plot_widget.addPlot(title="outputMpIp vs Time")
    plot2.setLabel('bottom', 'Time [µs]')
    plot2.setLabel('left', 'Plasma Current [A]')
    plot2.setXRange(time_min, time_max, padding=0)
    plot2.setLimits(xMin=time_min, xMax=time_max)
    plot2.setAutoVisible(y=True)
    zero_line2 = pg.InfiniteLine(pos=0, angle=0, pen=pg.mkPen('w', width=1, style=QtCore.Qt.DashLine))
    plot2.addItem(zero_line2)
    plot2.plot(time, df[mpip_col].values, pen='r')

    plot_widget.nextRow()
    plot3 = plot_widget.addPlot(title="chopper_trigger vs Time")
    plot3.setLabel('bottom', 'Time [µs]')
    plot3.setLabel('left', 'Trigger')
    plot3.setXRange(time_min, time_max, padding=0)
    plot3.setLimits(xMin=time_min, xMax=time_max)
    plot3.setYRange(0, 3)
    plot3.setLimits(yMin=0, yMax=3)
    plot3.setAutoVisible(y=False)
    zero_line3 = pg.InfiniteLine(pos=0, angle=0, pen=pg.mkPen('w', width=1, style=QtCore.Qt.DashLine))
    plot3.addItem(zero_line3)
    plot3.plot(time, df[chopper_col].values, pen=pg.mkPen('w', width=1))
    plot3.getViewBox().setMinimumHeight(60)
    plot3.setMaximumHeight(100)

def toggle_buttons(show_right):
    right_arrow.setVisible(show_right)
    left_arrow.setVisible(not show_right)

def show_mprz_plots():
    plot_widget.clear()
    export1_btn.hide()
    export2_btn.hide()
    export3_btn.show()
    export4_btn.show()

    p1 = plot_widget.addPlot(title="outputMpR vs Time")
    p1.setLabel('bottom', 'Time [µs]')
    p1.setLabel('left', 'Radial Position [m]')
    p1.plot(time, df[mpr_col].values, pen='c')

    plot_widget.nextRow()
    p2 = plot_widget.addPlot(title="outputMpZ vs Time")
    p2.setLabel('bottom', 'Time [µs]')
    p2.setLabel('left', 'Vertical Position [m]')
    p2.plot(time, df[mpz_col].values, pen='m')

    toggle_buttons(False)

def return_to_main_plots():
    show_main_plots()
    toggle_buttons(True)

def export_plot_with_dialog(plot, suggested_name):
    options = QtWidgets.QFileDialog.Options()
    file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
        main_window,
        "Save Plot As...",
        os.path.join(os.path.expanduser("~"), "git-repos/MARTe2-WaterTank/Startup/Outputs/pyqtCSV-plots/", suggested_name),
        "PNG Files (*.png);;All Files (*)",
        options=options
    )
    if file_path:
        exporter = pg.exporters.ImageExporter(plot)
        exporter.export(file_path)

right_arrow = QtWidgets.QPushButton("⊳", main_window)
right_arrow.setToolTip("Show MpR & MpZ Plots")
right_arrow.setFixedSize(40, 40)
right_arrow.setStyleSheet("""
    QPushButton {
        border: 2px solid #AAA;
        background-color: rgba(0, 0, 0, 0);
        color: white;
        font-size: 20px;
        font-weight: bold;
        border-radius: 8px;
    }
    QPushButton:hover {
        border: 2px solid #4caf50;
        background-color: rgba(255, 255, 255, 0.05);
    }
""")
right_arrow.clicked.connect(show_mprz_plots)

left_arrow = QtWidgets.QPushButton("⊲", main_window)
left_arrow.setToolTip("Show Mirnov & MpIp Plots")
left_arrow.setFixedSize(40, 40)
left_arrow.setStyleSheet(right_arrow.styleSheet())
left_arrow.clicked.connect(return_to_main_plots)

for btn in (right_arrow, left_arrow):
    btn.setParent(main_window)
    btn.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, False)

export1_btn.clicked.connect(lambda: export_plot_with_dialog(plot1, "mirnov_plot.png"))
export2_btn.clicked.connect(lambda: export_plot_with_dialog(plot2, "mpip_plot.png"))
export3_btn.clicked.connect(lambda: export_plot_with_dialog(plot_widget.getItem(0, 0), "mpr_plot.png"))
export4_btn.clicked.connect(lambda: export_plot_with_dialog(plot_widget.getItem(1, 0), "mpz_plot.png"))

main_window.showMaximized()

def reposition_arrows():
    h = main_window.height()
    right_arrow.move(main_window.width() - 60, h // 2 - 20)
    left_arrow.move(main_window.width() - 60, h // 2 - 20)

main_window.resizeEvent = lambda e: reposition_arrows()
reposition_arrows()
toggle_buttons(True)

main_window.keyPressEvent = lambda event: app.quit() if event.key() == QtCore.Qt.Key_Escape else None

show_main_plots()

sys.exit(app.exec_())

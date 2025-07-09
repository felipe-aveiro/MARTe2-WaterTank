import sys
import os
import pandas as pd
import csv
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets, QtCore
import pyqtgraph.exporters

# === Start Qt app FIRST ===
app = QtWidgets.QApplication(sys.argv)

# === Global variables for annotations ===
all_annotations = {}
all_markers = {}
selected_points = {}
active_plot = None

def clear_selection(plot):
    if plot in all_annotations:
        for item in all_annotations[plot] + all_markers[plot]:
            if item in plot.items:
                plot.removeItem(item)
    selected_points[plot] = []
    all_annotations[plot] = []
    all_markers[plot] = []


def annotate_distance(plot, point1, point2, y_index, y_unit):
    x1, y1 = point1
    x2, y2 = point2

    pen = pg.mkPen('w', width=2, style=QtCore.Qt.DashLine)
    h_line = pg.PlotDataItem([x1, x2], [y1, y1], pen=pen)
    v_line = pg.PlotDataItem([x2, x2], [y1, y2], pen=pen)

    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    label = pg.TextItem(f"\u0394t = {dx:.2f} ms\n\u0394{y_index} = {dy:.3f} {y_unit}", anchor=(0, 1), color='w')
    label.setPos(min(x1, x2), min(y1, y2))

    for item in [h_line, v_line, label]:
        plot.addItem(item)
        all_annotations[plot].append(item)


def setup_clickable_plot(plot, y_index, y_unit):
    all_annotations[plot] = []
    all_markers[plot] = []
    selected_points[plot] = []

    def on_mouse_click(event):
        pos = event.scenePos()
        if plot.sceneBoundingRect().contains(pos):
            mouse_point = plot.vb.mapSceneToView(pos)
            x, y = mouse_point.x(), mouse_point.y()

            if len(selected_points[plot]) >= 2:
                clear_selection(plot)
                return

            selected_points[plot].append((x, y))
            marker = pg.ScatterPlotItem([x], [y], symbol='x', size=12, pen=pg.mkPen('r', width=2))
            plot.addItem(marker)
            all_markers[plot].append(marker)

            if len(selected_points[plot]) == 2:
                annotate_distance(plot, selected_points[plot][0], selected_points[plot][1], y_index, y_unit)

    plot.scene().sigMouseClicked.connect(on_mouse_click)

# === Ask user to open a CSV file ===
csv_path, _ = QtWidgets.QFileDialog.getOpenFileName(
    None,
    "Open CSV File",
    "/home/felipe/git-repos/MARTe2-WaterTank/DataVisualization/Outputs/",
    "CSV Files (*.csv);;All Files (*)"
)

if not csv_path:
    QtWidgets.QMessageBox.critical(None, "Error", "No CSV file selected... Exiting.")
    sys.exit()

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
time_col = "#timeI (float64)[1]"
mirnov_cols = [f"inputMirnov{i} (float64)[1]" for i in range(12)]
mpip_col = "outputMpIp (float64)[1]"
mpr_col = "outputMpR (float64)[1]"
mpz_col = "outputMpZ (float64)[1]"
chopper_col = "chopper_trigger (float64)[1]"
rogowski_names = ["rogowski_ch (float64)[1]", "rogowski_ch_c (float64)[1]", "mds_ch12 (float64)[1]"]
rogowski_col = next((col for col in rogowski_names if col in df.columns), None)
pid_v_col = "VerticalPFCVoltageRequest (float64)[1]"
pid_r_col = "RadialPFCVoltageRequest (float64)[1]"
pid_available = pid_v_col in df.columns and pid_r_col in df.columns

has_chopper = chopper_col in df.columns
has_rogowski = rogowski_col is not None

full_time = (df[time_col] - df[time_col].iloc[0]) * 1e3
full_time_min, full_time_max = full_time.min(), full_time.max()

if has_chopper:
    start_index = df[df[chopper_col] == 3].index.min()
    if pd.notna(start_index):
        df_filtered = df.loc[start_index:].reset_index(drop=True)
        time = (df_filtered[time_col] - df_filtered[time_col].iloc[0]) * 1e3
        time = time.values
    else:
        QtWidgets.QMessageBox.warning(None, "Warning", "No chopper_trigger == 3 found. Showing full signal.")
        df_filtered = df.copy()
        time = full_time.values
    chopper_time = full_time.values - full_time.values[start_index] if pd.notna(start_index) else full_time.values
else:
    df_filtered = df.copy()
    time = full_time.values
    chopper_time = full_time.values  # default to full time if no chopper

time_min, time_max = time.min(), time.max()
current_xrange = [time_min, time_max]

def save_current_xrange():
    global current_xrange
    try:
        view = plot_widget.getItem(0, 0).vb.viewRange()[0]
        current_xrange = view
    except Exception:
        pass

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
export5_btn = QtWidgets.QPushButton("Export Comparison Plot")
export6_btn = QtWidgets.QPushButton("Export PID Request Plot")

for btn in (export3_btn, export4_btn, export5_btn, export6_btn):
    btn.hide()

button_layout.addWidget(export1_btn)
button_layout.addWidget(export2_btn)
button_layout.addWidget(export3_btn)
button_layout.addWidget(export4_btn)
button_layout.addWidget(export5_btn)
button_layout.addWidget(export6_btn)
main_layout.addLayout(button_layout)

plot_widget = pg.GraphicsLayoutWidget()
main_layout.addWidget(plot_widget, stretch=1)

def show_main_plots():
    save_current_xrange()
    plot_widget.clear()
    global plot1, plot2, plot3

    export3_btn.hide()
    export4_btn.hide()
    export5_btn.hide()
    export6_btn.hide()
    export1_btn.show()
    export2_btn.show()

    plot1 = plot_widget.addPlot(title="inputMirnov vs Time")
    plot1.setLabel('bottom', 'Time [ms]')
    plot1.setLabel('left', 'Magnetic Field [T]')
    plot1.addLegend()
    plot1.setXRange(time_min, time_max, padding=0)
    plot1.setLimits(xMin=time_min, xMax=time_max)
    plot1.setAutoVisible(y=True)
    zero_line1 = pg.InfiniteLine(pos=0, angle=0, pen=pg.mkPen('w', width=1, style=QtCore.Qt.DashLine))
    plot1.addItem(zero_line1)
    setup_clickable_plot(plot1, "B", "T")


    colors = [
        'r', 'g', 'b', 'c', 'm', 'y',
        (255, 128, 0), (128, 0, 255), (0, 128, 128),
        (255, 0, 128), (0, 255, 128), (128, 128, 0)
    ]

    for col, color in zip(mirnov_cols, colors):
        y = df_filtered[col].values
        clean_name = col.split(" ")[0]  # remove everything after first space
        plot1.plot(time, y, pen=pg.mkPen(color=color, width=1), name=clean_name)

    plot_widget.nextRow()
    plot2 = plot_widget.addPlot(title="outputMpIp vs Time")
    plot2.setLabel('bottom', 'Time [ms]')
    plot2.setLabel('left', 'Plasma Current [A]')
    plot2.setXRange(time_min, time_max, padding=0)
    plot2.setLimits(xMin=time_min, xMax=time_max)
    plot2.setAutoVisible(y=True)
    zero_line2 = pg.InfiniteLine(pos=0, angle=0, pen=pg.mkPen('w', width=1, style=QtCore.Qt.DashLine))
    plot2.addItem(zero_line2)
    plot2.plot(time, df_filtered[mpip_col].values, pen='r')
    setup_clickable_plot(plot2, "Iₚ", "A")

    plot1.setXLink(plot2)

    plot1.setXRange(*current_xrange, padding=0)
    plot2.setXRange(*current_xrange, padding=0)

    if has_chopper:
        plot_widget.nextRow()
        plot3 = plot_widget.addPlot()
        plot3.setLabel('bottom', 'Time [ms]')
        plot3.setLabel('left', 'Trigger')
        plot3.setXRange(chopper_time.min(), chopper_time.max(), padding=0)
        plot3.setLimits(xMin=chopper_time.min(), xMax=chopper_time.max())
        plot3.setYRange(0, 3)
        plot3.setLimits(yMin=0, yMax=3)
        plot3.setAutoVisible(y=False)
        plot3.plot(chopper_time, df[chopper_col].values, pen=pg.mkPen('w', width=1))
        plot3.getViewBox().setMinimumHeight(60)
        plot3.setMaximumHeight(100)

    toggle_buttons(show_right1=True)

def show_mprz_plots():
    save_current_xrange()
    plot_widget.clear()
    
    export1_btn.hide()
    export2_btn.hide()
    export5_btn.hide()
    export6_btn.hide()
    export3_btn.show()
    export4_btn.show()

    plot4 = plot_widget.addPlot(title="outputMpR vs Time")
    plot4.setLabel('bottom', 'Time [ms]')
    plot4.setLabel('left', 'Radial Position [m]')
    plot4.setXRange(time_min, time_max, padding=0)
    plot4.setLimits(xMin=time_min, xMax=time_max)
    plot4.setYRange(0.46-0.1, 0.46+0.1)
    zero_lineR_center = pg.InfiniteLine(pos=0.46, angle=0, pen=pg.mkPen('w', width=1, style=QtCore.Qt.DashLine))
    zero_lineR_upper = pg.InfiniteLine(pos=0.46+0.085, angle=0, pen=pg.mkPen('r', width=2, style=QtCore.Qt.DotLine))
    zero_lineR_lower = pg.InfiniteLine(pos=0.46-0.085, angle=0, pen=pg.mkPen('r', width=2, style=QtCore.Qt.DotLine))
    plot4.addItem(zero_lineR_center)
    plot4.addItem(zero_lineR_upper)
    plot4.addItem(zero_lineR_lower)
    plot4.plot(time, df_filtered[mpr_col].values, pen='c')
    setup_clickable_plot(plot4, "R", "m")

    plot_widget.nextRow()
    plot5 = plot_widget.addPlot(title="outputMpZ vs Time")
    plot5.setLabel('bottom', 'Time [ms]')
    plot5.setLabel('left', 'Vertical Position [m]')
    plot5.setXRange(time_min, time_max, padding=0)
    plot5.setLimits(xMin=time_min, xMax=time_max)
    plot5.setYRange(-0.1, 0.1)
    zero_lineZ_center = pg.InfiniteLine(pos=0, angle=0, pen=pg.mkPen('w', width=1, style=QtCore.Qt.DashLine))
    zero_lineZ_upper = pg.InfiniteLine(pos=0.085, angle=0, pen=pg.mkPen('r', width=2, style=QtCore.Qt.DotLine))
    zero_lineZ_lower = pg.InfiniteLine(pos=-0.085, angle=0, pen=pg.mkPen('r', width=2, style=QtCore.Qt.DotLine))
    plot5.addItem(zero_lineZ_center)
    plot5.addItem(zero_lineZ_upper)
    plot5.addItem(zero_lineZ_lower)
    plot5.plot(time, df_filtered[mpz_col].values, pen='m')
    setup_clickable_plot(plot5, "z", "m")

    plot4.setXLink(plot5)

    r_center = (plot4.vb.viewRange()[1][0] + plot4.vb.viewRange()[1][1]) / 2
    z_center = (plot5.vb.viewRange()[1][0] + plot5.vb.viewRange()[1][1]) / 2
    offset_4to5 = z_center - r_center
    offset_5to4 = r_center - z_center

    plot4.vb.sigYRangeChanged.connect(lambda: sync_y_range(plot4, plot5, offset_4to5))
    plot5.vb.sigYRangeChanged.connect(lambda: sync_y_range(plot5, plot4, offset_5to4))

    plot4.setXRange(*current_xrange, padding=0)
    plot5.setXRange(*current_xrange, padding=0)

    toggle_buttons(show_right2=True, show_left1=True)


def show_rogowski_comparison_plot():
    save_current_xrange()
    plot_widget.clear() 
    export1_btn.hide()
    export2_btn.hide()
    export3_btn.hide()
    export4_btn.hide()
    export6_btn.hide()
    export5_btn.show()

    plot_rogowski = plot_widget.addPlot(title="Rogowski Measurements vs Magnetic Reconstruction")
    plot_rogowski.setLabel('bottom', 'Time [ms]')
    plot_rogowski.setLabel('left', 'A')
    plot_rogowski.addLegend()
    plot_rogowski.setXRange(time_min, time_max, padding=0)
    plot_rogowski.setLimits(xMin=time_min, xMax=time_max)
    if pd.notna(rogowski_col): plot_rogowski.plot(time, df_filtered[rogowski_col].values, pen='m', name="Rogowski Measurement")
    else: QtWidgets.QMessageBox.warning(None, "Warning", "No Rogowski data found.")
    plot_rogowski.plot(time, df_filtered[mpip_col].values, pen='r', name="Magnetic Reconstruction") # df_filtered[mpip_col].values * 1e-3 * -1 to guarantee that both signals are essentially in the same range and polarity
    plot_rogowski.setAutoVisible(y=True)
    zero_line = pg.InfiniteLine(pos=0, angle=0, pen=pg.mkPen('w', width=1, style=QtCore.Qt.DashLine))
    plot_rogowski.addItem(zero_line)
    setup_clickable_plot(plot_rogowski, "Iₚ", "A")

    plot_rogowski.setXRange(*current_xrange, padding=0)

    toggle_buttons(show_left2=True, show_right3=True)

    if pid_available:
        right_arrow3.show()
    else:
        right_arrow3.hide()

    if not has_rogowski:
        right_arrow3.hide()
        QtWidgets.QMessageBox.information(None, "Info", "Rogowski column not available. Comparison limited.")

def show_pid_request_plots():
    save_current_xrange()
    plot_widget.clear()

    export1_btn.hide()
    export2_btn.hide()
    export3_btn.hide()
    export4_btn.hide()
    export5_btn.hide()
    export6_btn.show()

    # --- Radial Voltage Request ---
    plot_vr = plot_widget.addPlot(title="RadialPFCVoltageRequest vs Time")
    plot_vr.setLabel('bottom', 'Time [ms]')
    plot_vr.setLabel('left', 'Radial Voltage [V]')
    plot_vr.setXRange(time_min, time_max, padding=0)
    plot_vr.setLimits(xMin=time_min, xMax=time_max)
    plot_vr.setAutoVisible(y=True)
    zero_line_r = pg.InfiniteLine(pos=0, angle=0, pen=pg.mkPen('w', width=1, style=QtCore.Qt.DashLine))
    plot_vr.addItem(zero_line_r)
    plot_vr.plot(time, df_filtered[pid_r_col].values, pen='c')
    setup_clickable_plot(plot_vr, "Signal", "")

    plot_widget.nextRow()

    # --- Vertical Voltage Request ---
    plot_vz = plot_widget.addPlot(title="VerticalPFCVoltageRequest vs Time")
    plot_vz.setLabel('bottom', 'Time [ms]')
    plot_vz.setLabel('left', 'Vertical Voltage [V]')
    plot_vz.setXRange(time_min, time_max, padding=0)
    plot_vz.setLimits(xMin=time_min, xMax=time_max)
    plot_vz.setAutoVisible(y=True)
    zero_line_z = pg.InfiniteLine(pos=0, angle=0, pen=pg.mkPen('w', width=1, style=QtCore.Qt.DashLine))
    plot_vz.addItem(zero_line_z)
    plot_vz.plot(time, df_filtered[pid_v_col].values, pen='m')
    plot_vz.setYRange(plot_vr.vb.viewRange()[1][0], plot_vr.vb.viewRange()[1][1])

    setup_clickable_plot(plot_vz, "Signal", "")

    # Link horizontal zoom/pan
    plot_vr.setXLink(plot_vz)

    # Sync Y range logic (if needed)
    vr_center = (plot_vr.vb.viewRange()[1][0] + plot_vr.vb.viewRange()[1][1]) / 2
    vz_center = (plot_vz.vb.viewRange()[1][0] + plot_vz.vb.viewRange()[1][1]) / 2
    offset_4to5 = vz_center - vr_center
    offset_5to4 = vr_center - vz_center

    plot_vr.vb.sigYRangeChanged.connect(lambda: sync_y_range(plot_vr, plot_vz, offset_4to5))
    plot_vz.vb.sigYRangeChanged.connect(lambda: sync_y_range(plot_vz, plot_vr, offset_5to4))

    plot_vr.setXRange(*current_xrange, padding=0)
    plot_vz.setXRange(*current_xrange, padding=0)

    toggle_buttons(show_left3=True)


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

    target_plot.getAxis('left').setRange(*new_target_range)
    target_plot.getAxis('left').update()

def export_plot_with_dialog(plot, suggested_name):
    options = QtWidgets.QFileDialog.Options()
    file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
        main_window,
        "Save Plot As...",
        os.path.join(os.path.expanduser("~"), "git-repos/MARTe2-WaterTank/DataVisualization/Outputs/pyqtCSV-plots/", suggested_name),
        "PNG Files (*.png);;All Files (*)",
        options=options
    )
    if file_path:
        exporter = pg.exporters.ImageExporter(plot)
        exporter.export(file_path)

def toggle_buttons(show_right1=False, show_right2=False, show_right3=False,
                   show_left1=False, show_left2=False, show_left3=False):
    right_arrow.setVisible(show_right1)
    right_arrow2.setVisible(has_rogowski and show_right2)
    right_arrow3.setVisible(pid_available and has_rogowski and show_right3)
    left_arrow.setVisible(show_left1)
    left_arrow2.setVisible(show_left2)
    left_arrow3.setVisible(pid_available and show_left3)

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
left_arrow.clicked.connect(show_main_plots)

right_arrow2 = QtWidgets.QPushButton("⊳", main_window)
right_arrow2.setToolTip("Show Comparison Plot")
right_arrow2.setFixedSize(40, 40)
right_arrow2.setStyleSheet(right_arrow.styleSheet())
right_arrow2.clicked.connect(show_rogowski_comparison_plot)

left_arrow2 = QtWidgets.QPushButton("⊲", main_window)
left_arrow2.setToolTip("Show MpR & MpZ Plots")
left_arrow2.setFixedSize(40, 40)
left_arrow2.setStyleSheet(right_arrow.styleSheet())
left_arrow2.clicked.connect(show_mprz_plots)

right_arrow3 = QtWidgets.QPushButton("⊳", main_window)
right_arrow3.setToolTip("Show PID Voltage Requests")
right_arrow3.setFixedSize(40, 40)
right_arrow3.setStyleSheet(right_arrow.styleSheet())
right_arrow3.clicked.connect(show_pid_request_plots)

left_arrow3 = QtWidgets.QPushButton("⊲", main_window)
left_arrow3.setToolTip("Show Comparison Plot")
left_arrow3.setFixedSize(40, 40)
left_arrow3.setStyleSheet(right_arrow.styleSheet())
left_arrow3.clicked.connect(show_rogowski_comparison_plot)

for btn in (right_arrow, left_arrow, right_arrow2, left_arrow2, right_arrow3, left_arrow3):
    btn.setParent(main_window)
    btn.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, False)

def reposition_arrows():
    h = main_window.height()
    # ====== Main Plots ===========
    if not has_chopper:
        right_arrow.move(main_window.width() - 60, h // 2 + 2)
    else:
        right_arrow.move(main_window.width() - 60, h // 2 - 48)
    # ====== Position Plots =======
    left_arrow.move(40, h // 2 + 2)
    right_arrow2.move(main_window.width() - 60, h // 2 + 2)
    # ====== Comparison Plot ======
    left_arrow2.move(40, h // 2 + 20)
    right_arrow3.move(main_window.width() - 60, h // 2 + 20)
    # ====== PID Plots ============
    left_arrow3.move(40, h // 2 + 2)

export1_btn.clicked.connect(lambda: export_plot_with_dialog(plot1, "mirnov_plot.png"))
export2_btn.clicked.connect(lambda: export_plot_with_dialog(plot2, "mpip_plot.png"))
export3_btn.clicked.connect(lambda: export_plot_with_dialog(plot_widget.getItem(0, 0), "mpr_plot.png"))
export4_btn.clicked.connect(lambda: export_plot_with_dialog(plot_widget.getItem(1, 0), "mpz_plot.png"))
export5_btn.clicked.connect(lambda: export_plot_with_dialog(plot_widget.getItem(0, 0), "rogowksi_m-reconstruction_comparison.png"))
export6_btn.clicked.connect(lambda: export_plot_with_dialog(plot_widget.getItem(0, 0), "pid_voltage_requests.png"))

main_window.showMaximized()

main_window.resizeEvent = lambda e: reposition_arrows()
reposition_arrows()
toggle_buttons(True)

main_window.keyPressEvent = lambda event: app.quit() if event.key() == QtCore.Qt.Key_Escape else None

show_main_plots()

sys.exit(app.exec_())

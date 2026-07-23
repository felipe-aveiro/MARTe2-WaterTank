import sys
import os
import re
import numpy as np
import pandas as pd
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets, QtCore, QtGui
from pyqtgraph.exporters import ImageExporter
from sdas.core.client.SDASClient import SDASClient


# === Start Qt app FIRST ===
app = QtWidgets.QApplication(sys.argv)
custom_legend_items_pos = []

# === SDAS configuration ===
HOST = "baco.ipfn.tecnico.ulisboa.pt"
PORT = 8888

RADIAL_DOMENICA_CHANNEL = "MARTE_NODE_IVO3.DataCollection.Channel_101"
VERTICAL_DOMENICA_CHANNEL = "MARTE_NODE_IVO3.DataCollection.Channel_102"

MAJOR_RADIUS = 0.46

# === Load SDAS data ===
def load_sdas_channel(client, channel_id, shot_number):
    data_struct = client.getData(channel_id, "0x0000", shot_number)

    data_array = np.array(data_struct[0].getData())
    length = len(data_array)

    t_start = data_struct[0].getTStart()
    t_end = data_struct[0].getTEnd()

    dt_us = (t_end.getTimeInMicros() - t_start.getTimeInMicros()) / (length - 1)
    time_vector = np.linspace(0, dt_us * (length - 1), length) * 1e-3  # ms

    return data_array, time_vector


# === Find column robustly ===
def find_column(df, signal_name):
    possible_columns = [
        f"{signal_name} (float64)[1]",
        f"{signal_name} (float32)[1]"
    ]

    for column in possible_columns:
        if column in df.columns:
            return column

    raise ValueError(f"Column not found: {signal_name}")


# === Copy current view from one plot to the other ===
def transfer_view(source_plot, target_plot, y_offset):
    source_x_range, source_y_range = source_plot.vb.viewRange()

    target_plot.setXRange(
        source_x_range[0],
        source_x_range[1],
        padding=0
    )

    target_plot.setYRange(
        source_y_range[0] + y_offset,
        source_y_range[1] + y_offset,
        padding=0
    )


# === Compute mean inside a selected time interval ===
def calculate_interval_mean(time_vector, signal_vector, start_ms, end_ms):
    time_array = np.asarray(time_vector)
    signal_array = np.asarray(signal_vector)

    mask = (time_array >= start_ms) & (time_array <= end_ms)

    if not np.any(mask):
        return np.nan

    return np.nanmean(signal_array[mask])


# === Add custom manual legend ===
def add_custom_legend(plot_item, legend_items, x_offset, y_offset, spacing=15):
    legend_font = QtGui.QFont("Arial", 10)

    for i, (curve, label) in enumerate(legend_items):
        legend_y = y_offset + i * spacing

        sample = pg.graphicsItems.LegendItem.ItemSample(curve)
        sample.setParentItem(plot_item.graphicsItem())
        sample.setPos(x_offset, legend_y - 3)
        custom_legend_items_pos.append(sample)

        text = pg.TextItem(label, anchor=(0, 0), color="gray")
        text.setFont(legend_font)
        text.setParentItem(plot_item.graphicsItem())
        text.setPos(x_offset + 25, legend_y)
        custom_legend_items_pos.append(text)

def add_dynamic_custom_legend(plot_item, legend_items, x_offset, y_offset, spacing=15):
    legend_font = QtGui.QFont("Arial", 10)
    created_items = []

    valid_items = [
        (curve, label)
        for curve, label in legend_items
        if curve is not None
    ]

    for i, (curve, label) in enumerate(valid_items):
        legend_y = y_offset + i * spacing

        sample = pg.graphicsItems.LegendItem.ItemSample(curve)
        sample.setParentItem(plot_item.graphicsItem())
        sample.setPos(x_offset, legend_y - 3)
        custom_legend_items_pos.append(sample)
        created_items.append(sample)

        text = pg.TextItem(label, anchor=(0, 0), color="gray")
        text.setFont(legend_font)
        text.setParentItem(plot_item.graphicsItem())
        text.setPos(x_offset + 25, legend_y)
        custom_legend_items_pos.append(text)
        created_items.append(text)

    return created_items

# === Add horizontal mean line segment ===
def add_mean_line(plot_item, mean_value, color, start_ms, end_ms):
    if np.isnan(mean_value):
        return None

    return plot_item.plot(
        [start_ms, end_ms],
        [mean_value, mean_value],
        pen=pg.mkPen(color, width=3, style=QtCore.Qt.DashLine)
    )

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
    with open(csv_path, "r") as f:
        header_line = f.readline()

    semicolon_count = header_line.count("]") - header_line.count("];")
    comma_count = header_line.count("]") - header_line.count("],")

    delimiter = ";" if semicolon_count < comma_count else ","
    df = pd.read_csv(csv_path, delimiter=delimiter)
    df.columns = df.columns.str.strip()

except Exception as e:
    QtWidgets.QMessageBox.critical(None, "Error loading CSV", f"An error occurred:\n{e}")
    sys.exit()


# === Extract shot number ===
csv_filename = os.path.basename(csv_path)
match = re.search(r"(\d{5})", csv_filename)
shot_number = int(match.group(1)) if match else None

if shot_number is None:
    QtWidgets.QMessageBox.critical(None, "Error", "Shot number not found in file name.")
    sys.exit()


# === Identify relevant columns ===
try:
    time_col = next((column for column in df.columns if column.startswith("#time")), None)

    if time_col is None:
        raise ValueError("Time column not found.")

    mpr_col = find_column(df, "outputMpR")
    mpz_col = find_column(df, "outputMpZ")
    epr_col = find_column(df, "outputEpR")
    epz_col = find_column(df, "outputEpZ")
    fusedr_col = find_column(df, "outputFusedR")
    fusedz_col = find_column(df, "outputFusedZ")

except Exception as e:
    QtWidgets.QMessageBox.critical(None, "Missing Columns", f"An error occurred:\n{e}")
    sys.exit()


# === Prepare time in ms ===
time = (df[time_col] - df[time_col].iloc[0]) * 1e3


# === Load Reference reconstruction from SDAS ===
try:
    client = SDASClient(HOST, PORT)

    radial_dom, sdas_time = load_sdas_channel(
        client,
        RADIAL_DOMENICA_CHANNEL,
        shot_number
    )

    vertical_dom, _ = load_sdas_channel(
        client,
        VERTICAL_DOMENICA_CHANNEL,
        shot_number
    )

except Exception as e:
    QtWidgets.QMessageBox.critical(
        None,
        "SDAS Error",
        f"An error occurred while loading the reference reconstruction from SDAS:\n{e}"
    )
    sys.exit()


# === Common time limits ===
time_min = max(time.min(), sdas_time.min())
time_max = min(time.max(), sdas_time.max())

initial_x_min = time_min
initial_x_max = time_max


# === Signals ===
magnetic_r = df[mpr_col].to_numpy()
electric_r = df[epr_col].to_numpy()
fused_r = df[fusedr_col].to_numpy()
reference_r = radial_dom + MAJOR_RADIUS

magnetic_z = df[mpz_col].to_numpy()
electric_z = df[epz_col].to_numpy()
fused_z = df[fusedz_col].to_numpy()
reference_z = vertical_dom


# === Main window and layout ===
main_window = QtWidgets.QMainWindow()
main_window.setWindowTitle("Plasma Position Estimation")
central_widget = QtWidgets.QWidget()
main_layout = QtWidgets.QVBoxLayout()
central_widget.setLayout(main_layout)
main_window.setCentralWidget(central_widget)

# === Stacked widget: one graph visible at a time ===
stacked_plot_widget = QtWidgets.QStackedWidget()
stacked_plot_widget.setSizePolicy(
    QtWidgets.QSizePolicy.Expanding,
    QtWidgets.QSizePolicy.Expanding
)

main_layout.addWidget(
    stacked_plot_widget,
    stretch=1
)
#stacked_plot_widget.setFixedSize(800, 500)
#main_layout.addWidget(stacked_plot_widget)

plot_widget_r = pg.GraphicsLayoutWidget()
plot_widget_z = pg.GraphicsLayoutWidget()
plot_widget_mean = pg.GraphicsLayoutWidget()

stacked_plot_widget.addWidget(plot_widget_r)
stacked_plot_widget.addWidget(plot_widget_z)
stacked_plot_widget.addWidget(plot_widget_mean)

bold_font = QtGui.QFont("Arial", 11, QtGui.QFont.Bold)


# ============================================================
# === Plot 1: Radial Position
# ============================================================
plot_r = plot_widget_r.addPlot(title="Estimated Plasma Radial Position")
plot_r.titleLabel.item.setFont(QtGui.QFont("Arial", 14, QtGui.QFont.Bold))
plot_r.setLabel("bottom", "Time [ms]")
plot_r.setLabel("left", "R [m]")
plot_r.getAxis("bottom").label.setFont(bold_font)
plot_r.getAxis("left").label.setFont(bold_font)

plot_r.setXRange(time_min, time_max, padding=0)
plot_r.setXRange(initial_x_min, initial_x_max, padding=0)
plot_r.setLimits(xMin=time_min, xMax=time_max)

plot_r.setYRange(0.46 - 0.1, 0.46 + 0.1)

plot_r.addItem(
    pg.InfiniteLine(
        pos=0.46,
        angle=0,
        pen=pg.mkPen("w", width=1, style=QtCore.Qt.DashLine)
    )
)

plot_r.addItem(
    pg.InfiniteLine(
        pos=0.46 + 0.085,
        angle=0,
        pen=pg.mkPen("r", width=2, style=QtCore.Qt.DotLine)
    )
)

plot_r.addItem(
    pg.InfiniteLine(
        pos=0.46 - 0.085,
        angle=0,
        pen=pg.mkPen("r", width=2, style=QtCore.Qt.DotLine)
    )
)

curve_m_r = plot_r.plot(
    time,
    magnetic_r,
    pen="m",
    name="Magnetic Coils"
)

curve_e_r = plot_r.plot(
    time,
    electric_r,
    pen="g",
    name="Electric Probes"
)

curve_f_r = plot_r.plot(
    time,
    fused_r,
    pen="b",
    name="Fused State"
)

curve_dom_r = plot_r.plot(
    sdas_time,
    reference_r,
    pen=pg.mkPen((220, 190, 60, 190), width=2),
    name="Reference Reconstruction"
)

legend_items_r = [
    (curve_m_r, "Magnetic Coils"),
    (curve_e_r, "Electric Probes"),
    (curve_f_r, "Fused State"),
    (curve_dom_r, "Reference Reconstruction")
]

add_custom_legend(plot_r, legend_items_r, x_offset=500, y_offset=60)


# ============================================================
# === Plot 2: Vertical Position
# ============================================================
plot_z = plot_widget_z.addPlot(title="Estimated Plasma Vertical Position")
plot_z.titleLabel.item.setFont(QtGui.QFont("Arial", 14, QtGui.QFont.Bold))
plot_z.setLabel("bottom", "Time [ms]")
plot_z.setLabel("left", "Z [m]")
plot_z.getAxis("bottom").label.setFont(bold_font)
plot_z.getAxis("left").label.setFont(bold_font)

plot_z.setXRange(time_min, time_max, padding=0)
plot_z.setXRange(initial_x_min, initial_x_max, padding=0)
plot_z.setLimits(xMin=time_min, xMax=time_max)

plot_z.setYRange(-0.1, 0.1)

plot_z.addItem(
    pg.InfiniteLine(
        pos=0,
        angle=0,
        pen=pg.mkPen("w", width=1, style=QtCore.Qt.DashLine)
    )
)

plot_z.addItem(
    pg.InfiniteLine(
        pos=0.085,
        angle=0,
        pen=pg.mkPen("r", width=2, style=QtCore.Qt.DotLine)
    )
)

plot_z.addItem(
    pg.InfiniteLine(
        pos=-0.085,
        angle=0,
        pen=pg.mkPen("r", width=2, style=QtCore.Qt.DotLine)
    )
)

curve_m_z = plot_z.plot(
    time,
    magnetic_z,
    pen="m",
    name="Magnetic Coils"
)

curve_e_z = plot_z.plot(
    time,
    electric_z,
    pen="g",
    name="Electric Probes"
)

curve_f_z = plot_z.plot(
    time,
    fused_z,
    pen="b",
    name="Fused State"
)

curve_dom_z = plot_z.plot(
    sdas_time,
    reference_z,
    pen=pg.mkPen((220, 190, 60, 190), width=2),
    name="Reference Reconstruction"
)

legend_items_z = [
    (curve_m_z, "Magnetic Coils"),
    (curve_e_z, "Electric Probes"),
    (curve_f_z, "Fused State"),
    (curve_dom_z, "Reference Reconstruction")
]

add_custom_legend(plot_z, legend_items_z, x_offset=500, y_offset=60)


# ============================================================
# === Plot 3: Mean Position Plot - Radial and Vertical
# ============================================================
plot_mean_r = plot_widget_mean.addPlot(
    title="Average Radial Position during flat top"
)

plot_mean_r.titleLabel.item.setFont(QtGui.QFont("Arial", 14, QtGui.QFont.Bold))
plot_mean_r.setLabel("bottom", "Time [ms]")
plot_mean_r.setLabel("left", "R [m]")
plot_mean_r.getAxis("bottom").label.setFont(bold_font)
plot_mean_r.getAxis("left").label.setFont(bold_font)

plot_mean_r.setXRange(initial_x_min, initial_x_max, padding=0)
plot_mean_r.setLimits(xMin=time_min, xMax=time_max)
plot_mean_r.setYRange(0.46 - 0.04, 0.46 + 0.04)

plot_mean_r.addItem(
    pg.InfiniteLine(
        pos=0.46,
        angle=0,
        pen=pg.mkPen("w", width=1, style=QtCore.Qt.DashLine)
    )
)

plot_mean_r.addItem(
    pg.InfiniteLine(
        pos=0.46 + 0.085,
        angle=0,
        pen=pg.mkPen("r", width=2, style=QtCore.Qt.DotLine)
    )
)

plot_mean_r.addItem(
    pg.InfiniteLine(
        pos=0.46 - 0.085,
        angle=0,
        pen=pg.mkPen("r", width=2, style=QtCore.Qt.DotLine)
    )
)


plot_widget_mean.nextRow()


plot_mean_z = plot_widget_mean.addPlot(
    title="Average Vertical Position during flat top"
)

plot_mean_z.titleLabel.item.setFont(QtGui.QFont("Arial", 14, QtGui.QFont.Bold))
plot_mean_z.setLabel("bottom", "Time [ms]")
plot_mean_z.setLabel("left", "Z [m]")
plot_mean_z.getAxis("bottom").label.setFont(bold_font)
plot_mean_z.getAxis("left").label.setFont(bold_font)

plot_mean_z.setXRange(initial_x_min, initial_x_max, padding=0)
plot_mean_z.setLimits(xMin=time_min, xMax=time_max)
plot_mean_z.setYRange(-0.04, 0.04)

plot_mean_z.addItem(
    pg.InfiniteLine(
        pos=0,
        angle=0,
        pen=pg.mkPen("w", width=1, style=QtCore.Qt.DashLine)
    )
)

plot_mean_z.addItem(
    pg.InfiniteLine(
        pos=0.085,
        angle=0,
        pen=pg.mkPen("r", width=2, style=QtCore.Qt.DotLine)
    )
)

plot_mean_z.addItem(
    pg.InfiniteLine(
        pos=-0.085,
        angle=0,
        pen=pg.mkPen("r", width=2, style=QtCore.Qt.DotLine)
    )
)

plot_mean_r.setXLink(plot_mean_z)

mean_dynamic_items = []
interval_preview_items = []
selected_interval = {
    "start_ms": None,
    "end_ms": None
}

# ============================================================
# === Dynamic graph switching
# ============================================================
current_plot = {"name": "Radial"}

stacked_plot_widget.setCurrentWidget(plot_widget_r)

def clear_items(items):
    for plot_item, item in items:
        if item is None:
            continue

        try:
            plot_item.removeItem(item)
        except Exception:
            pass

    items.clear()


def clear_mean_dynamic_items():
    clear_items(mean_dynamic_items)


def clear_interval_preview_items():
    clear_items(interval_preview_items)


def get_current_position_plot():
    if current_plot["name"] == "Radial":
        return plot_r

    if current_plot["name"] == "Vertical":
        return plot_z

    return None


def get_selected_interval_from_inputs(show_error=True):
    try:
        start_ms = int(start_interval_input.text())
        end_ms = int(end_interval_input.text())

    except ValueError:
        if show_error:
            QtWidgets.QMessageBox.warning(
                None,
                "Invalid interval",
                "Please insert integer values for the start and end times in ms."
            )
        return None, None

    if start_ms >= end_ms:
        if show_error:
            QtWidgets.QMessageBox.warning(
                None,
                "Invalid interval",
                "The start time must be lower than the end time."
            )
        return None, None

    if start_ms < time_min or end_ms > time_max:
        if show_error:
            QtWidgets.QMessageBox.warning(
                None,
                "Invalid interval",
                f"The selected interval must be inside the available time range:\n"
                f"{time_min:.2f} ms to {time_max:.2f} ms."
            )
        return None, None

    return start_ms, end_ms


def update_interval_preview():
    start_ms, end_ms = get_selected_interval_from_inputs(show_error=False)

    clear_interval_preview_items()

    if start_ms is None or end_ms is None:
        return

    current_position_plot = get_current_position_plot()

    if current_position_plot is None:
        return

    start_line = pg.InfiniteLine(
        pos=start_ms,
        angle=90,
        pen=pg.mkPen((180, 180, 180, 170), width=2, style=QtCore.Qt.DashLine)
    )

    end_line = pg.InfiniteLine(
        pos=end_ms,
        angle=90,
        pen=pg.mkPen((180, 180, 180, 170), width=2, style=QtCore.Qt.DashLine)
    )

    current_position_plot.addItem(start_line)
    current_position_plot.addItem(end_line)

    interval_preview_items.append((current_position_plot, start_line))
    interval_preview_items.append((current_position_plot, end_line))

    current_position_plot.setXRange(
        max(time_min, start_ms - 2),
        min(time_max, end_ms + 2),
        padding=0
    )


def calculate_selected_means(start_ms, end_ms):
    means = {
        "magnetic_r": calculate_interval_mean(time, magnetic_r, start_ms, end_ms),
        "electric_r": calculate_interval_mean(time, electric_r, start_ms, end_ms),
        "fused_r": calculate_interval_mean(time, fused_r, start_ms, end_ms),
        "reference_r": calculate_interval_mean(sdas_time, reference_r, start_ms, end_ms),

        "magnetic_z": calculate_interval_mean(time, magnetic_z, start_ms, end_ms),
        "electric_z": calculate_interval_mean(time, electric_z, start_ms, end_ms),
        "fused_z": calculate_interval_mean(time, fused_z, start_ms, end_ms),
        "reference_z": calculate_interval_mean(sdas_time, reference_z, start_ms, end_ms),
    }

    return means


def set_mean_y_range(plot_item, mean_values, default_center, default_half_range):
    valid_values = [
        value for value in mean_values
        if not np.isnan(value)
    ]

    if not valid_values:
        plot_item.setYRange(
            default_center - default_half_range,
            default_center + default_half_range,
            padding=0
        )
        return

    min_value = min(valid_values)
    max_value = max(valid_values)

    margin = max((max_value - min_value) * 0.25, 0.005)

    plot_item.setYRange(
        min_value - margin,
        max_value + margin,
        padding=0
    )

def show_mean_table_dialog(start_ms, end_ms, rows):
    dialog = QtWidgets.QDialog(main_window)
    dialog.setWindowTitle("Flat top mean position table")
    dialog.resize(850, 260)

    layout = QtWidgets.QVBoxLayout(dialog)

    title = QtWidgets.QLabel(
        f"Comparison between calculated mean plasma positions during "
        f"{start_ms} – {end_ms} ms flat top phase for shot {shot_number}"
    )
    title.setWordWrap(True)
    title.setFont(QtGui.QFont("Arial", 11, QtGui.QFont.Bold))
    layout.addWidget(title)

    table = QtWidgets.QTableWidget()
    table.setRowCount(len(rows))
    table.setColumnCount(5)

    table.setHorizontalHeaderLabels([
        "Estimator",
        "Mean R position [cm]",
        "∆R to Reference [cm]",
        "Mean Z position [cm]",
        "∆Z to Reference [cm]"
    ])

    for row_idx, row_data in enumerate(rows):
        for col_idx, value in enumerate(row_data):
            item = QtWidgets.QTableWidgetItem(value)
            item.setTextAlignment(QtCore.Qt.AlignCenter)
            table.setItem(row_idx, col_idx, item)

    table.horizontalHeader().setStretchLastSection(True)
    table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
    table.verticalHeader().setVisible(False)
    table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

    layout.addWidget(table)

    close_button = QtWidgets.QPushButton("OK")
    close_button.clicked.connect(dialog.accept)
    layout.addWidget(close_button)

    dialog.exec_()
    
def update_mean_position_plot(start_ms, end_ms):
    clear_mean_dynamic_items()

    means = calculate_selected_means(start_ms, end_ms)

    plot_mean_r.setTitle(
        f"Average Radial Position during flat top ({start_ms}-{end_ms} ms)"
    )

    plot_mean_z.setTitle(
        f"Average Vertical Position during flat top ({start_ms}-{end_ms} ms)"
    )

    plot_mean_r.titleLabel.item.setFont(QtGui.QFont("Arial", 14, QtGui.QFont.Bold))
    plot_mean_z.titleLabel.item.setFont(QtGui.QFont("Arial", 14, QtGui.QFont.Bold))

    plot_mean_r.setXRange(start_ms, end_ms, padding=0)
    plot_mean_z.setXRange(start_ms, end_ms, padding=0)

    plot_mean_r.setLimits(xMin=start_ms, xMax=end_ms)
    plot_mean_z.setLimits(xMin=start_ms, xMax=end_ms)

    set_mean_y_range(
        plot_mean_r,
        [
            means["magnetic_r"],
            means["electric_r"],
            means["fused_r"],
            means["reference_r"]
        ],
        default_center=MAJOR_RADIUS,
        default_half_range=0.04
    )

    set_mean_y_range(
        plot_mean_z,
        [
            means["magnetic_z"],
            means["electric_z"],
            means["fused_z"],
            means["reference_z"]
        ],
        default_center=0.0,
        default_half_range=0.04
    )

    mean_curve_m_r = add_mean_line(plot_mean_r, means["magnetic_r"], "m", start_ms, end_ms)
    mean_curve_e_r = add_mean_line(plot_mean_r, means["electric_r"], "g", start_ms, end_ms)
    mean_curve_f_r = add_mean_line(plot_mean_r, means["fused_r"], "b", start_ms, end_ms)
    mean_curve_dom_r = add_mean_line(
        plot_mean_r,
        means["reference_r"],
        (220, 190, 60, 190),
        start_ms,
        end_ms
    )

    mean_curve_m_z = add_mean_line(plot_mean_z, means["magnetic_z"], "m", start_ms, end_ms)
    mean_curve_e_z = add_mean_line(plot_mean_z, means["electric_z"], "g", start_ms, end_ms)
    mean_curve_f_z = add_mean_line(plot_mean_z, means["fused_z"], "b", start_ms, end_ms)
    mean_curve_dom_z = add_mean_line(
        plot_mean_z,
        means["reference_z"],
        (220, 190, 60, 190),
        start_ms,
        end_ms
    )

    mean_dynamic_items.extend([
        (plot_mean_r, mean_curve_m_r),
        (plot_mean_r, mean_curve_e_r),
        (plot_mean_r, mean_curve_f_r),
        (plot_mean_r, mean_curve_dom_r),
        (plot_mean_z, mean_curve_m_z),
        (plot_mean_z, mean_curve_e_z),
        (plot_mean_z, mean_curve_f_z),
        (plot_mean_z, mean_curve_dom_z),
    ])

    legend_items_mean_r = [
        (mean_curve_m_r, "Magnetic Coils"),
        (mean_curve_e_r, "Electric Probes"),
        (mean_curve_f_r, "Fused State"),
        (mean_curve_dom_r, "Reference Reconstruction")
    ]

    mean_r_legend_items = add_dynamic_custom_legend(
    plot_mean_r,
    legend_items_mean_r,
    x_offset=600,
    y_offset=30
    )

    for item in mean_r_legend_items:
        mean_dynamic_items.append((plot_mean_r, item))

        reference_r_cm = means["reference_r"] * 100
    reference_z_cm = means["reference_z"] * 100

    rows = [
        ("Reference", means["reference_r"] * 100, None, means["reference_z"] * 100, None),
        ("Magnetic", means["magnetic_r"] * 100, means["magnetic_r"] * 100 - reference_r_cm, means["magnetic_z"] * 100, means["magnetic_z"] * 100 - reference_z_cm),
        ("Electric", means["electric_r"] * 100, means["electric_r"] * 100 - reference_r_cm, means["electric_z"] * 100, means["electric_z"] * 100 - reference_z_cm),
        ("Fused", means["fused_r"] * 100, means["fused_r"] * 100 - reference_r_cm, means["fused_z"] * 100, means["fused_z"] * 100 - reference_z_cm),
    ]

    def format_value(value):
        if value is None or np.isnan(value):
            return "N/A"
        return f"{value:+.3f}"

    table_text = (
        f"Table: Comparison between calculated mean plasma positions during {start_ms} – {end_ms} ms flat top phase for shot {shot_number}\n"
        f"Estimator\tMean R position [cm]\t∆R to Reference [cm]\tMean Z position [cm]\t∆Z to Reference [cm]\n"
    )

    for estimator, mean_r, delta_r, mean_z, delta_z in rows:
        table_text += (
            f"{estimator}\t"
            f"{format_value(mean_r)}\t"
            f"{format_value(delta_r)}\t"
            f"{format_value(mean_z)}\t"
            f"{format_value(delta_z)}\n"
        )

    print("\n" + table_text)

    table_rows = []

    for estimator, mean_r, delta_r, mean_z, delta_z in rows:
        table_rows.append([
            estimator,
            format_value(mean_r),
            format_value(delta_r),
            format_value(mean_z),
            format_value(delta_z)
        ])

    show_mean_table_dialog(start_ms, end_ms, table_rows)


def reset_average_selection():
    clear_interval_preview_items()
    clear_mean_dynamic_items()

    selected_interval["start_ms"] = None
    selected_interval["end_ms"] = None

    start_interval_input.clear()
    end_interval_input.clear()

    plot_mean_r.setTitle("Average Radial Position during flat top")
    plot_mean_z.setTitle("Average Vertical Position during flat top")

    plot_mean_r.titleLabel.item.setFont(QtGui.QFont("Arial", 14, QtGui.QFont.Bold))
    plot_mean_z.titleLabel.item.setFont(QtGui.QFont("Arial", 14, QtGui.QFont.Bold))

def show_radial_plot():
    clear_interval_preview_items()

    if current_plot["name"] == "Mean":
        reset_average_selection()

    elif current_plot["name"] == "Vertical":
        transfer_view(
            source_plot=plot_z,
            target_plot=plot_r,
            y_offset=MAJOR_RADIUS
        )

    stacked_plot_widget.setCurrentWidget(plot_widget_r)
    current_plot["name"] = "Radial"
    main_window.setWindowTitle(f"Estimated Plasma Radial Position")


def show_vertical_plot():
    clear_interval_preview_items()

    if current_plot["name"] == "Mean":
        reset_average_selection()

    elif current_plot["name"] == "Radial":
        transfer_view(
            source_plot=plot_r,
            target_plot=plot_z,
            y_offset=-MAJOR_RADIUS
        )

    stacked_plot_widget.setCurrentWidget(plot_widget_z)
    current_plot["name"] = "Vertical"
    main_window.setWindowTitle(f"Estimated Plasma Vertical Position")


def show_mean_position_plot():
    start_ms, end_ms = get_selected_interval_from_inputs(show_error=True)

    if start_ms is None or end_ms is None:
        return

    selected_interval["start_ms"] = start_ms
    selected_interval["end_ms"] = end_ms

    clear_interval_preview_items()
    update_mean_position_plot(start_ms, end_ms)

    stacked_plot_widget.setCurrentWidget(plot_widget_mean)
    current_plot["name"] = "Mean"

    main_window.setWindowTitle(
        f"Mean Estimated Plasma Position - {start_ms}-{end_ms} ms"
    )


# ============================================================
# === Export buttons and switch buttons
# ============================================================
button_layout = QtWidgets.QHBoxLayout()
main_layout.addLayout(button_layout)

show_r_button = QtWidgets.QPushButton("Show Radial Plot")
show_z_button = QtWidgets.QPushButton("Show Vertical Plot")
show_mean_button = QtWidgets.QPushButton("Show Mean Position Plot")
export_current_button = QtWidgets.QPushButton("Export Plot")

button_layout.addWidget(show_r_button)
button_layout.addWidget(show_z_button)
button_layout.addWidget(show_mean_button)
button_layout.addWidget(export_current_button)

interval_layout = QtWidgets.QHBoxLayout()
main_layout.addLayout(interval_layout)

interval_label = QtWidgets.QLabel("Select flat top interval [ms]:")
start_interval_input = QtWidgets.QLineEdit()
end_interval_input = QtWidgets.QLineEdit()

start_interval_input.setPlaceholderText("Start")
end_interval_input.setPlaceholderText("End")

start_interval_input.setFixedWidth(80)
end_interval_input.setFixedWidth(80)

integer_validator = QtGui.QIntValidator(int(time_min), int(time_max))

start_interval_input.setValidator(integer_validator)
end_interval_input.setValidator(integer_validator)

interval_layout.addWidget(interval_label)
interval_layout.addWidget(start_interval_input)
interval_layout.addWidget(end_interval_input)
interval_layout.addStretch()

start_interval_input.editingFinished.connect(update_interval_preview)
end_interval_input.editingFinished.connect(update_interval_preview)


def export_plot(plot_item, default_name):
    default_dir = "/home/felipe/git-repos/MARTe2-WaterTank/DataVisualization/Outputs/PlasmaPositionPlots"
    os.makedirs(default_dir, exist_ok=True)

    default_path = os.path.join(default_dir, f"{default_name}.png")

    path, _ = QtWidgets.QFileDialog.getSaveFileName(
        None,
        "Save Plot as PNG",
        default_path,
        "PNG Files (*.png)"
    )

    if path:
        exporter = ImageExporter(plot_item.scene())
        exporter.parameters()["width"] = 1200
        exporter.export(path)
        print(f"\nPlot saved to {path}\n")


def export_plot_widget(graphics_widget, default_name):
    default_dir = "/home/felipe/git-repos/MARTe2-WaterTank/DataVisualization/Outputs/PlasmaPositionPlots"
    os.makedirs(default_dir, exist_ok=True)

    default_path = os.path.join(default_dir, f"{default_name}.png")

    path, _ = QtWidgets.QFileDialog.getSaveFileName(
        None,
        "Save Plot as PNG",
        default_path,
        "PNG Files (*.png)"
    )

    if path:
        exporter = ImageExporter(graphics_widget.scene())
        exporter.parameters()["width"] = 1200
        exporter.export(path)
        print(f"\nPlot saved to {path}\n")


def export_current_plot():
    if current_plot["name"] == "Radial":
        export_plot(
            plot_r,
            f"radial_position_four_trajectories_plot_shot_{shot_number}"
        )

    elif current_plot["name"] == "Vertical":
        export_plot(
            plot_z,
            f"vertical_position_four_trajectories_plot_shot_{shot_number}"
        )

    elif current_plot["name"] == "Mean":
        start_ms = selected_interval["start_ms"]
        end_ms = selected_interval["end_ms"]

        if start_ms is None or end_ms is None:
            QtWidgets.QMessageBox.warning(
                None,
                "Missing interval",
                "No flat top interval has been selected."
            )
            return

        export_plot_widget(
            plot_widget_mean,
            f"mean_position_four_trajectories_{start_ms}_{end_ms}_ms_shot_{shot_number}"
        )


show_r_button.clicked.connect(show_radial_plot)
show_z_button.clicked.connect(show_vertical_plot)
show_mean_button.clicked.connect(show_mean_position_plot)
export_current_button.clicked.connect(export_current_plot)


# === Keyboard shortcuts ===
def handle_key_press(event):
    if event.key() == QtCore.Qt.Key_Escape:
        app.quit()

main_window.keyPressEvent = handle_key_press


# === Show window and run ===
main_window.showMaximized()
main_window.setWindowTitle(f"Plasma Radial Position Estimation - Shot {shot_number}")
sys.exit(app.exec_())
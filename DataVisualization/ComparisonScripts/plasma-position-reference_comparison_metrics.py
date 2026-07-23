import os
import sys
import numpy as np
import pandas as pd
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets, QtGui, QtCore
from sdas.core.client.SDASClient import SDASClient


# ============================================================
# SDAS configuration
# ============================================================
HOST = "baco.ipfn.tecnico.ulisboa.pt"
PORT = 8888

RADIAL_REFERENCE_CHANNEL = "MARTE_NODE_IVO3.DataCollection.Channel_101"
VERTICAL_REFERENCE_CHANNEL = "MARTE_NODE_IVO3.DataCollection.Channel_102"

MAJOR_RADIUS = 0.46


# ============================================================
# Shot configuration
# ============================================================
SHOT_CONFIG = {
    53071: {
        "label": "Shot 53071",
        "start_ms": 272,
        "end_ms": 293,
        "csv_path": "/home/felipe/git-repos/MARTe2-WaterTank/DataVisualization/Outputs/IsttokOutput_DataFusion_53071.csv"
    },
    48555: {
        "label": "Shot 48555",
        "start_ms": 105,
        "end_ms": 130,
        "csv_path": "/home/felipe/git-repos/MARTe2-WaterTank/DataVisualization/Outputs/IsttokOutput_DataFusion_48555.csv"
    }
}


# ============================================================
# Output and figure configuration
# ============================================================
OUTPUT_DIR = "/home/felipe/git-repos/MARTe2-WaterTank/DataVisualization/Outputs/PlasmaPositionMetrics"

# Change these values to control the exported figure size.
FIGURE_WIDTH = 880
FIGURE_HEIGHT = 700
EXPORT_DELAY_MS = 700

# Font sizes following the histogram plot style.
AXIS_TICK_FONT_SIZE = 11
AXIS_LABEL_FONT_SIZE = 11
TITLE_FONT_SIZE = 18
VALUE_LABEL_FONT_SIZE = 10
SHOT_LABEL_FONT_SIZE = 12
LEGEND_FONT_SIZE = 11

# Shot label box size in scene pixels.
SHOT_BOX_WIDTH_PX = 52
SHOT_BOX_HEIGHT_PX = 18


# ============================================================
# Data loading helper functions
# ============================================================
def find_column(df, signal_name):
    """Find a signal column allowing float64 or float32 formats."""
    possible_columns = [
        f"{signal_name} (float64)[1]",
        f"{signal_name} (float32)[1]"
    ]

    for column in possible_columns:
        if column in df.columns:
            return column

    raise ValueError(f"Column not found for signal: {signal_name}")


def detect_delimiter(csv_path):
    """Detect whether the CSV file uses semicolon or comma delimiter."""
    with open(csv_path, "r") as file:
        header_line = file.readline()

    semicolon_count = header_line.count(";")
    comma_count = header_line.count(",")

    return ";" if semicolon_count >= comma_count else ","


def load_csv_data(csv_path):
    """Load CSV data and return the time vector and estimator signals."""
    delimiter = detect_delimiter(csv_path)

    df = pd.read_csv(csv_path, delimiter=delimiter)
    df.columns = df.columns.str.strip()

    time_col = next((column for column in df.columns if column.startswith("#time")), None)

    if time_col is None:
        raise ValueError("Time column not found.")

    columns = {
        "magnetic_r": find_column(df, "outputMpR"),
        "magnetic_z": find_column(df, "outputMpZ"),
        "electric_r": find_column(df, "outputEpR"),
        "electric_z": find_column(df, "outputEpZ"),
        "fused_r": find_column(df, "outputFusedR"),
        "fused_z": find_column(df, "outputFusedZ")
    }

    time_ms = (df[time_col] - df[time_col].iloc[0]).to_numpy() * 1e3

    signals = {
        key: df[column].to_numpy()
        for key, column in columns.items()
    }

    return time_ms, signals


def load_sdas_channel(client, channel_id, shot_number):
    """Load one SDAS channel and return the signal and time vector in ms."""
    data_struct = client.getData(channel_id, "0x0000", int(shot_number))

    data_array = np.asarray(data_struct[0].getData(), dtype=float)
    length = len(data_array)

    t_start = data_struct[0].getTStart()
    t_end = data_struct[0].getTEnd()

    dt_us = (t_end.getTimeInMicros() - t_start.getTimeInMicros()) / (length - 1)
    time_ms = np.linspace(0, dt_us * (length - 1), length) * 1e-3

    return data_array, time_ms


def load_reference_reconstruction(client, shot_number):
    """Load radial and vertical reference reconstructions from SDAS."""
    radial_reference, reference_time_ms = load_sdas_channel(
        client,
        RADIAL_REFERENCE_CHANNEL,
        shot_number
    )

    vertical_reference, _ = load_sdas_channel(
        client,
        VERTICAL_REFERENCE_CHANNEL,
        shot_number
    )

    reference = {
        "R": radial_reference + MAJOR_RADIUS,
        "Z": vertical_reference
    }

    return reference_time_ms, reference


# ============================================================
# Metrics computation
# ============================================================
def compute_metrics(time_est, estimated_signal, time_ref, reference_signal, start_ms, end_ms):
    """
    Compute MAE, RMSE, maximum absolute error, and Pearson correlation coefficient.

    Error metrics are returned in centimeters.
    """
    time_est = np.asarray(time_est)
    estimated_signal = np.asarray(estimated_signal)

    time_ref = np.asarray(time_ref)
    reference_signal = np.asarray(reference_signal)

    mask = (time_est >= start_ms) & (time_est <= end_ms)

    if not np.any(mask):
        raise ValueError(f"No samples found in interval {start_ms}-{end_ms} ms.")

    interval_time = time_est[mask]
    interval_estimated = estimated_signal[mask]

    # Interpolate the reference reconstruction into the estimator time base.
    interval_reference = np.interp(interval_time, time_ref, reference_signal)

    error_m = interval_estimated - interval_reference
    error_cm = error_m * 100.0

    mae_cm = np.mean(np.abs(error_cm))
    rmse_cm = np.sqrt(np.mean(error_cm ** 2))
    max_abs_error_cm = np.max(np.abs(error_cm))

    if np.std(interval_estimated) == 0 or np.std(interval_reference) == 0:
        pcc = np.nan
    else:
        pcc = np.corrcoef(interval_estimated, interval_reference)[0, 1]

    return {
        "MAE": mae_cm,
        "RMSE": rmse_cm,
        "MaxAE": max_abs_error_cm,
        "PCC": pcc
    }


def compute_all_metrics():
    """Compute metrics for all configured shots, estimators, and position components."""
    client = SDASClient(HOST, PORT)

    rows = []

    for shot_number, config in SHOT_CONFIG.items():
        csv_path = config["csv_path"]
        start_ms = config["start_ms"]
        end_ms = config["end_ms"]

        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"CSV file not found for shot {shot_number}: {csv_path}")

        time_csv, signals = load_csv_data(csv_path)
        time_ref, reference = load_reference_reconstruction(client, shot_number)

        estimator_map = {
            "Magnetic": {
                "R": signals["magnetic_r"],
                "Z": signals["magnetic_z"]
            },
            "Electric": {
                "R": signals["electric_r"],
                "Z": signals["electric_z"]
            },
            "Fused": {
                "R": signals["fused_r"],
                "Z": signals["fused_z"]
            }
        }

        for position in ["R", "Z"]:
            for estimator_name, estimator_signals in estimator_map.items():
                metrics = compute_metrics(
                    time_est=time_csv,
                    estimated_signal=estimator_signals[position],
                    time_ref=time_ref,
                    reference_signal=reference[position],
                    start_ms=start_ms,
                    end_ms=end_ms
                )

                rows.append({
                    "shot": shot_number,
                    "shot_label": config["label"],
                    "position": position,
                    "estimator": estimator_name,
                    "MAE": metrics["MAE"],
                    "RMSE": metrics["RMSE"],
                    "MaxAE": metrics["MaxAE"],
                    "PCC": metrics["PCC"]
                })

    return pd.DataFrame(rows)


# ============================================================
# Plot formatting helper functions
# ============================================================
def get_position_name(position):
    """Convert compact position labels into dissertation-style labels."""
    if position == "R":
        return "Radial"

    if position == "Z":
        return "Vertical"

    return position


def get_bar_colors():
    """Return the same colors used in the plasma position trajectory plots."""
    colors = {
        "Magnetic": pg.mkColor("m"),
        "Electric": pg.mkColor("g"),
        "Fused": pg.mkColor("b")
    }

    for color in colors.values():
        color.setAlpha(190)

    return colors


def configure_plot_style(plot, title, left_label):
    """Apply the common PyQtGraph style used for dissertation figures."""
    title_font = QtGui.QFont("Arial", TITLE_FONT_SIZE, QtGui.QFont.Bold)
    axis_label_font = QtGui.QFont("Arial", AXIS_LABEL_FONT_SIZE, QtGui.QFont.Bold)
    tick_font = QtGui.QFont("Arial", AXIS_TICK_FONT_SIZE)

    plot.setTitle(title)
    plot.titleLabel.item.setFont(title_font)

    plot.setLabel("left", left_label)
    plot.getAxis("left").label.setFont(axis_label_font)

    # No x-axis label is used to maximize useful plot area.
    plot.setLabel("bottom", "")

    plot.getAxis("left").setStyle(tickFont=tick_font)
    plot.getAxis("bottom").setStyle(tickFont=tick_font)

    try:
        plot.getAxis("bottom").setStyle(tickTextOffset=12)
    except TypeError:
        pass

    plot.getAxis("left").setTextPen("w")
    plot.getAxis("bottom").setTextPen("w")

    plot.getAxis("left").setWidth(56)
    plot.getAxis("bottom").setHeight(46)

    plot.showGrid(x=True, y=True)


def add_value_labels(plot, x_values, y_values, value_format, y_offset):
    """Add numeric labels above each bar."""
    value_font = QtGui.QFont("Arial", VALUE_LABEL_FONT_SIZE, QtGui.QFont.Bold, italic=True)

    for x_value, y_value in zip(x_values, y_values):
        if np.isnan(y_value):
            continue

        text = pg.TextItem(
            text=value_format.format(y_value),
            anchor=(0.5, 1.0),
            color="w"
        )

        text.setFont(value_font)
        text.setPos(x_value, y_value + y_offset)
        text.setZValue(100)
        plot.addItem(text)


def add_manual_legend(plot, legend_items, x_pos, y_pos, spacing):
    """Add a compact manual legend inside the upper plot."""
    legend_font = QtGui.QFont("Arial", LEGEND_FONT_SIZE)

    for index, (label, color) in enumerate(legend_items):
        y_value = y_pos - index * spacing

        sample = pg.PlotDataItem(
            [x_pos, x_pos + 0.16],
            [y_value, y_value],
            pen=pg.mkPen(color, width=5)
        )
        sample.setZValue(80)
        plot.addItem(sample)

        text = pg.TextItem(
            text=label,
            anchor=(0, 0.5),
            color="w"
        )

        text.setFont(legend_font)
        text.setPos(x_pos + 0.22, y_value)
        text.setZValue(80)
        plot.addItem(text)


def clear_overlay_items(win):
    """Remove previously created scene-overlay items."""
    if not hasattr(win, "overlay_items"):
        win.overlay_items = []
        return

    scene = win.scene()

    for item in win.overlay_items:
        try:
            scene.removeItem(item)
        except RuntimeError:
            pass

    win.overlay_items.clear()


def add_overlay_shot_label_boxes(win):
    """
    Add shot label boxes as scene-overlay items.

    These boxes are not added to the plot ViewBox, so they are not clipped by the plot area.
    """
    clear_overlay_items(win)

    if not hasattr(win, "shot_overlay_specs"):
        return

    scene = win.scene()
    shot_font = QtGui.QFont("Arial", SHOT_LABEL_FONT_SIZE, QtGui.QFont.Bold)

    for spec in win.shot_overlay_specs:
        plot = spec["plot"]
        x_values = spec["x_values"]
        labels = spec["labels"]
        y_data = spec["y_data"]

        for x_value, label in zip(x_values, labels):
            scene_pos = plot.vb.mapViewToScene(QtCore.QPointF(float(x_value), float(y_data)))
            scene_x = scene_pos.x()
            scene_y = scene_pos.y()

            box = QtWidgets.QGraphicsRectItem(
                scene_x - SHOT_BOX_WIDTH_PX / 2,
                scene_y - SHOT_BOX_HEIGHT_PX / 2,
                SHOT_BOX_WIDTH_PX,
                SHOT_BOX_HEIGHT_PX
            )
            box.setBrush(QtGui.QBrush(QtGui.QColor("white")))
            box.setPen(pg.mkPen("white"))
            box.setZValue(1000)
            scene.addItem(box)
            win.overlay_items.append(box)

            text = QtWidgets.QGraphicsSimpleTextItem(label)
            text.setFont(shot_font)
            text.setBrush(QtGui.QBrush(QtGui.QColor("black")))
            text.setZValue(1001)

            text_rect = text.boundingRect()
            text.setPos(
                scene_x - text_rect.width() / 2,
                scene_y - text_rect.height() / 2
            )

            scene.addItem(text)
            win.overlay_items.append(text)


def compute_common_error_y_max(metrics_df):
    """Compute a common Y range for radial and vertical error plots."""
    error_values = metrics_df[["MAE", "RMSE", "MaxAE"]].to_numpy(dtype=float)
    global_max_error = np.nanmax(error_values)

    return global_max_error * 1.32


# ============================================================
# Main plotting function
# ============================================================
def create_metrics_window(metrics_df, position, common_error_y_max):
    """Create one fixed-size PyQtGraph window with error metrics and PCC for one position component."""
    position_name = get_position_name(position)
    position_df = metrics_df[metrics_df["position"] == position].copy()

    estimators = ["Magnetic", "Electric", "Fused"]
    shots = [53071, 48555]
    error_metrics = ["MAE", "RMSE", "MaxAE"]

    colors = get_bar_colors()

    # Layout parameters for compact, readable exported figures.
    bar_width = 0.24
    shot_gap = 0.82
    metric_gap = 1.85

    win = pg.GraphicsLayoutWidget(
        title=f"{position_name} Position Metrics Comparison"
    )

    win.resize(FIGURE_WIDTH, FIGURE_HEIGHT)
    win.setFixedSize(FIGURE_WIDTH, FIGURE_HEIGHT)

    win.overlay_items = []
    win.shot_overlay_specs = []

    # ========================================================
    # Upper plot: Error metrics
    # ========================================================
    error_plot = win.addPlot(title="")
    error_plot.setMaximumHeight(370)

    configure_plot_style(
        error_plot,
        f"{position_name} Position Error Metrics Comparison",
        "Error [cm]"
    )

    metric_centers = []
    group_centers = []
    group_shot_labels = []

    current_x = 0.0

    for metric in error_metrics:
        first_shot_center = current_x
        second_shot_center = current_x + shot_gap

        metric_centers.append((first_shot_center + second_shot_center) / 2.0)

        group_centers.extend([first_shot_center, second_shot_center])
        group_shot_labels.extend([str(shots[0]), str(shots[1])])

        current_x += metric_gap

    metric_ticks = [
        (metric_centers[index], metric)
        for index, metric in enumerate(error_metrics)
    ]

    error_plot.getAxis("bottom").setTicks([metric_ticks])

    local_error_values = []

    for estimator_index, estimator in enumerate(estimators):
        x_values = []
        y_values = []

        for metric_index, metric in enumerate(error_metrics):
            for shot_index, shot in enumerate(shots):
                group_center = group_centers[2 * metric_index + shot_index]
                x_values.append(group_center + (estimator_index - 1) * bar_width)

                value = position_df[
                    (position_df["shot"] == shot) &
                    (position_df["estimator"] == estimator)
                ][metric].iloc[0]

                y_values.append(value)
                local_error_values.append(value)

        x_values = np.asarray(x_values)
        y_values = np.asarray(y_values)

        bars = pg.BarGraphItem(
            x=x_values,
            height=y_values,
            width=bar_width,
            brush=QtGui.QBrush(colors[estimator])
        )

        bars.setZValue(10)
        error_plot.addItem(bars)

    local_max_error = np.nanmax(local_error_values)

    # Use the same Y range for radial and vertical plots.
    error_plot.setYRange(0, common_error_y_max, padding=0)

    # Keep the first and last bar groups fully visible.
    error_plot.setXRange(
        group_centers[0] - 0.58,
        group_centers[-1] + 0.58,
        padding=0
    )

    for estimator_index, estimator in enumerate(estimators):
        x_values = []
        y_values = []

        for metric_index, metric in enumerate(error_metrics):
            for shot_index, shot in enumerate(shots):
                group_center = group_centers[2 * metric_index + shot_index]
                x_values.append(group_center + (estimator_index - 1) * bar_width)

                value = position_df[
                    (position_df["shot"] == shot) &
                    (position_df["estimator"] == estimator)
                ][metric].iloc[0]

                y_values.append(value)

        add_value_labels(
            error_plot,
            np.asarray(x_values),
            np.asarray(y_values),
            value_format="{:.2f}",
            y_offset=common_error_y_max * 0.018
        )

    # Store shot label positions and draw them later as scene overlays.
    win.shot_overlay_specs.append({
        "plot": error_plot,
        "x_values": group_centers,
        "labels": group_shot_labels,
        "y_data": common_error_y_max * 0.94
    })

    add_manual_legend(
        error_plot,
        [
            ("Magnetic", colors["Magnetic"]),
            ("Electric", colors["Electric"]),
            ("Fused", colors["Fused"])
        ],
        x_pos=group_centers[0] - 0.30,
        y_pos=4.5,
        spacing=0.5
    )

    # ========================================================
    # Lower plot: Pearson Correlation Coefficient
    # ========================================================
    win.nextRow()

    pcc_plot = win.addPlot(title="")
    pcc_plot.setMaximumHeight(330)

    configure_plot_style(
        pcc_plot,
        f"{position_name} Position Temporal Agreement",
        "Pearson Correlation Coefficient (PCC)"
    )

    pcc_group_centers = np.array([0.0, 1.25])

    pcc_ticks = [
        (pcc_group_centers[0], str(shots[0])),
        (pcc_group_centers[1], str(shots[1]))
    ]

    pcc_plot.getAxis("bottom").setTicks([pcc_ticks])

    for estimator_index, estimator in enumerate(estimators):
        x_values = pcc_group_centers + (estimator_index - 1) * bar_width
        y_values = []

        for shot in shots:
            value = position_df[
                (position_df["shot"] == shot) &
                (position_df["estimator"] == estimator)
            ]["PCC"].iloc[0]

            y_values.append(value)

        y_values = np.asarray(y_values)

        bars = pg.BarGraphItem(
            x=x_values,
            height=y_values,
            width=bar_width,
            brush=QtGui.QBrush(colors[estimator])
        )

        bars.setZValue(10)
        pcc_plot.addItem(bars)

        add_value_labels(
            pcc_plot,
            x_values,
            y_values,
            value_format="{:.3f}",
            y_offset=0.045
        )

    zero_line = pg.InfiniteLine(
        pos=0,
        angle=0,
        pen=pg.mkPen("w", width=1, style=QtCore.Qt.DashLine)
    )

    zero_line.setZValue(5)
    pcc_plot.addItem(zero_line)

    pcc_plot.setYRange(-0.5, 1.5, padding=0)

    pcc_plot.setXRange(
        pcc_group_centers[0] - 0.52,
        pcc_group_centers[-1] + 0.52,
        padding=0
    )

    return win


def save_window_image(win, output_path):
    """Save the rendered PyQtGraph window as a PNG image."""
    screenshot = win.grab()
    screenshot.save(output_path, "PNG")
    print(f"Image saved to {output_path}")


# ============================================================
# Main
# ============================================================
def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    app = QtWidgets.QApplication(sys.argv)

    metrics_df = compute_all_metrics()
    common_error_y_max = compute_common_error_y_max(metrics_df)

    print("\nComputed metrics:")
    print(metrics_df.to_string(index=False))

    metrics_csv_path = os.path.join(
        OUTPUT_DIR,
        "metrics_comparison_53071_48555.csv"
    )

    metrics_df.to_csv(metrics_csv_path, index=False)
    print(f"\nMetrics table saved to {metrics_csv_path}")

    radial_window = create_metrics_window(metrics_df, "R", common_error_y_max)
    vertical_window = create_metrics_window(metrics_df, "Z", common_error_y_max)

    radial_window.setWindowTitle("Radial Position Metrics Comparison")
    vertical_window.setWindowTitle("Vertical Position Metrics Comparison")

    radial_window.move(50, 80)
    vertical_window.move(950, 80)

    radial_window.show()
    vertical_window.show()

    def update_overlays():
        add_overlay_shot_label_boxes(radial_window)
        add_overlay_shot_label_boxes(vertical_window)

    def save_images():
        update_overlays()

        radial_path = os.path.join(
            OUTPUT_DIR,
            "radial_position_metrics_comparison_53071_48555.png"
        )

        vertical_path = os.path.join(
            OUTPUT_DIR,
            "vertical_position_metrics_comparison_53071_48555.png"
        )

        save_window_image(radial_window, radial_path)
        save_window_image(vertical_window, vertical_path)

    QtCore.QTimer.singleShot(250, update_overlays)
    QtCore.QTimer.singleShot(EXPORT_DELAY_MS, save_images)

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
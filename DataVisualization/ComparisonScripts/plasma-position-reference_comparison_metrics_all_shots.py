import os
import sys
import numpy as np
import pandas as pd
from pyqtgraph.Qt import QtWidgets, QtCore, QtGui
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
# Paths
# ============================================================
CSV_BASE_DIR = (
    "/home/felipe/git-repos/MARTe2-WaterTank/"
    "DataVisualization/Outputs"
)

OUTPUT_DIR = os.path.join(CSV_BASE_DIR, "PlasmaPositionMetrics")
OUTPUT_FILENAME = "plasma_position_metrics_all_selected_shots.csv"


# ============================================================
# FLAT-TOP INTERVALS
# ============================================================
# Define the flat-top interval used for each shot in milliseconds.
#
#
FLAT_TOP_INTERVALS_MS = {
    45967: (53, 77),
    46241: (35, 59),
    53058: (39, 64),
    53071: (272, 293),
    48555: (105, 130),
    48556: (105, 130),
    48561: (104, 128),
    48563: (103, 127),
}


# ============================================================
# Shot selection
# ============================================================
SHOT_GROUPS = {
    "Langmuir reconstruction selection": [
        45967,
        46241,
        53058,
        53071,
    ],
    "Reference reconstruction selection": [
        48555,
        48556,
        48561,
        48563,
    ],
}


def build_shot_config():
    """Build the complete shot configuration from the editable sections."""
    shot_config = {}

    for selection_group, shot_numbers in SHOT_GROUPS.items():
        for shot_number in shot_numbers:
            start_ms, end_ms = FLAT_TOP_INTERVALS_MS[shot_number]

            shot_config[shot_number] = {
                "selection_group": selection_group,
                "start_ms": start_ms,
                "end_ms": end_ms,
                "csv_path": os.path.join(
                    CSV_BASE_DIR,
                    f"IsttokOutput_DataFusion_{shot_number}.csv",
                ),
            }

    return shot_config


SHOT_CONFIG = build_shot_config()


# ============================================================
# Data loading helper functions
# ============================================================
def find_column(df, signal_name):
    """Find a signal column allowing float64 or float32 formats."""
    possible_columns = [
        f"{signal_name} (float64)[1]",
        f"{signal_name} (float32)[1]",
    ]

    for column in possible_columns:
        if column in df.columns:
            return column

    raise ValueError(f"Column not found for signal: {signal_name}")


def detect_delimiter(csv_path):
    """Detect whether the CSV file uses semicolon or comma delimiter."""
    with open(csv_path, "r", encoding="utf-8") as file:
        header_line = file.readline()

    semicolon_count = header_line.count(";")
    comma_count = header_line.count(",")

    return ";" if semicolon_count >= comma_count else ","


def load_csv_data(csv_path):
    """Load CSV data and return the time vector and estimator signals."""
    delimiter = detect_delimiter(csv_path)

    df = pd.read_csv(csv_path, delimiter=delimiter)
    df.columns = df.columns.str.strip()

    time_col = next(
        (column for column in df.columns if column.startswith("#time")),
        None,
    )

    if time_col is None:
        raise ValueError(f"Time column not found in: {csv_path}")

    columns = {
        "magnetic_r": find_column(df, "outputMpR"),
        "magnetic_z": find_column(df, "outputMpZ"),
        "electric_r": find_column(df, "outputEpR"),
        "electric_z": find_column(df, "outputEpZ"),
        "fused_r": find_column(df, "outputFusedR"),
        "fused_z": find_column(df, "outputFusedZ"),
    }

    time_s = df[time_col].to_numpy(dtype=float)
    time_ms = (time_s - time_s[0]) * 1e3

    signals = {
        key: df[column].to_numpy(dtype=float)
        for key, column in columns.items()
    }

    return time_ms, signals


def load_sdas_channel(client, channel_id, shot_number):
    """Load one SDAS channel and return the signal and time vector in ms."""
    data_struct = client.getData(
        channel_id,
        "0x0000",
        int(shot_number),
    )

    data_array = np.asarray(
        data_struct[0].getData(),
        dtype=float,
    )

    length = len(data_array)

    if length < 2:
        raise ValueError(
            f"SDAS channel {channel_id} contains fewer than two samples "
            f"for shot {shot_number}."
        )

    t_start = data_struct[0].getTStart()
    t_end = data_struct[0].getTEnd()

    duration_us = (
        t_end.getTimeInMicros()
        - t_start.getTimeInMicros()
    )

    time_ms = np.linspace(
        0.0,
        duration_us * 1e-3,
        length,
    )

    return data_array, time_ms


def load_reference_reconstruction(client, shot_number):
    """Load radial and vertical reference reconstructions from SDAS."""
    radial_reference, reference_time_ms = load_sdas_channel(
        client,
        RADIAL_REFERENCE_CHANNEL,
        shot_number,
    )

    vertical_reference, vertical_time_ms = load_sdas_channel(
        client,
        VERTICAL_REFERENCE_CHANNEL,
        shot_number,
    )

    if (
        len(vertical_time_ms) != len(reference_time_ms)
        or not np.allclose(
            vertical_time_ms,
            reference_time_ms,
        )
    ):
        vertical_reference = np.interp(
            reference_time_ms,
            vertical_time_ms,
            vertical_reference,
        )

    reference = {
        "R": radial_reference + MAJOR_RADIUS,
        "Z": vertical_reference,
    }

    return reference_time_ms, reference


# ============================================================
# Validation
# ============================================================
def validate_configuration():
    """Validate flat-top intervals and CSV paths before accessing SDAS."""
    errors = []

    for shot_number, config in SHOT_CONFIG.items():
        start_ms = config["start_ms"]
        end_ms = config["end_ms"]
        csv_path = config["csv_path"]

        if start_ms is None or end_ms is None:
            errors.append(
                f"Shot {shot_number}: flat-top interval is not defined."
            )

        elif start_ms >= end_ms:
            errors.append(
                f"Shot {shot_number}: start_ms must be smaller than end_ms "
                f"({start_ms} >= {end_ms})."
            )

        if not os.path.isfile(csv_path):
            errors.append(
                f"Shot {shot_number}: CSV file not found: {csv_path}"
            )

    if errors:
        formatted_errors = "\n".join(
            f"  - {error}"
            for error in errors
        )

        raise ValueError(
            "Configuration validation failed:\n"
            f"{formatted_errors}\n\n"
            "Update FLAT_TOP_INTERVALS_MS and verify the CSV paths."
        )


# ============================================================
# Metrics computation
# ============================================================
def compute_metrics(
    time_est,
    estimated_signal,
    time_ref,
    reference_signal,
    start_ms,
    end_ms,
):
    """
    Compute MAE, RMSE, MaxAE, and PCC over the selected flat top.

    Error metrics are returned in centimeters.
    """
    time_est = np.asarray(time_est, dtype=float)
    estimated_signal = np.asarray(
        estimated_signal,
        dtype=float,
    )

    time_ref = np.asarray(time_ref, dtype=float)
    reference_signal = np.asarray(
        reference_signal,
        dtype=float,
    )

    mask = (
        (time_est >= start_ms)
        & (time_est <= end_ms)
    )

    if not np.any(mask):
        raise ValueError(
            f"No estimator samples found in interval "
            f"{start_ms}-{end_ms} ms."
        )

    interval_time = time_est[mask]
    interval_estimated = estimated_signal[mask]

    if (
        interval_time[0] < time_ref[0]
        or interval_time[-1] > time_ref[-1]
    ):
        raise ValueError(
            "The selected estimator interval lies outside the reference "
            "reconstruction time range."
        )

    interval_reference = np.interp(
        interval_time,
        time_ref,
        reference_signal,
    )

    valid_mask = (
        np.isfinite(interval_estimated)
        & np.isfinite(interval_reference)
    )

    interval_estimated = interval_estimated[valid_mask]
    interval_reference = interval_reference[valid_mask]

    if interval_estimated.size < 2:
        raise ValueError(
            "Fewer than two valid samples remain after removing "
            "NaN/Inf values."
        )

    error_cm = (
        interval_estimated
        - interval_reference
    ) * 100.0

    mae_cm = np.mean(
        np.abs(error_cm)
    )

    rmse_cm = np.sqrt(
        np.mean(error_cm**2)
    )

    max_abs_error_cm = np.max(
        np.abs(error_cm)
    )

    if (
        np.isclose(
            np.std(interval_estimated),
            0.0,
        )
        or np.isclose(
            np.std(interval_reference),
            0.0,
        )
    ):
        pcc = np.nan

    else:
        pcc = np.corrcoef(
            interval_estimated,
            interval_reference,
        )[0, 1]

    return {
        "MAE_cm": mae_cm,
        "RMSE_cm": rmse_cm,
        "MaxAE_cm": max_abs_error_cm,
        "PCC": pcc,
        "sample_count": interval_estimated.size,
    }


def compute_all_metrics():
    """Compute all metrics for every configured shot."""
    client = SDASClient(HOST, PORT)
    rows = []

    for shot_number, config in SHOT_CONFIG.items():
        print(
            f"\nProcessing shot {shot_number} "
            f"from {config['start_ms']} to "
            f"{config['end_ms']} ms..."
        )

        time_csv, signals = load_csv_data(
            config["csv_path"]
        )

        time_ref, reference = load_reference_reconstruction(
            client,
            shot_number,
        )

        estimator_map = {
            "Magnetic": {
                "R": signals["magnetic_r"],
                "Z": signals["magnetic_z"],
            },
            "Electric": {
                "R": signals["electric_r"],
                "Z": signals["electric_z"],
            },
            "Fused": {
                "R": signals["fused_r"],
                "Z": signals["fused_z"],
            },
        }

        for position in ("R", "Z"):
            for estimator_name, estimator_signals in estimator_map.items():
                metrics = compute_metrics(
                    time_est=time_csv,
                    estimated_signal=estimator_signals[position],
                    time_ref=time_ref,
                    reference_signal=reference[position],
                    start_ms=config["start_ms"],
                    end_ms=config["end_ms"],
                )

                rows.append(
                    {
                        "selection_group": config["selection_group"],
                        "shot": shot_number,
                        "flat_top_start_ms": config["start_ms"],
                        "flat_top_end_ms": config["end_ms"],
                        "position": position,
                        "estimator": estimator_name,
                        **metrics,
                    }
                )

    return pd.DataFrame(rows)


# ============================================================
# Output formatting
# ============================================================
def create_dissertation_table(metrics_df):
    """Create a wide table suitable for transferring values to the thesis."""
    wide_df = metrics_df.pivot(
        index=[
            "selection_group",
            "shot",
            "flat_top_start_ms",
            "flat_top_end_ms",
        ],
        columns=[
            "position",
            "estimator",
        ],
        values=[
            "MAE_cm",
            "RMSE_cm",
            "MaxAE_cm",
            "PCC",
        ],
    )

    wide_df.columns = [
        f"{position}_{estimator}_{metric}"
        for metric, position, estimator in wide_df.columns
    ]

    return wide_df.reset_index()

# ============================================================
# Visual metrics table
# ============================================================
def format_metric_value(value, metric_name):
    """Format metric values for display in the visual table."""
    if pd.isna(value):
        return "N/A"

    if metric_name == "PCC":
        return f"{value:.3f}"

    return f"{value:.3f}"


def show_metrics_table_dialog(metrics_df):
    """Show MAE, RMSE, MaxAE, and PCC in a visual Qt table."""
    dialog = QtWidgets.QDialog()
    dialog.setWindowTitle("Plasma position estimation metrics")
    dialog.resize(1100, 700)

    layout = QtWidgets.QVBoxLayout(dialog)

    title = QtWidgets.QLabel(
        "Comparison of plasma position estimation metrics "
        "during the selected flat-top intervals"
    )

    title.setWordWrap(True)
    title.setFont(
        QtGui.QFont(
            "Arial",
            11,
            QtGui.QFont.Bold
        )
    )

    layout.addWidget(title)

    # Ensure rows are ordered consistently:
    # 6 rows per shot = 3 radial + 3 vertical.
    estimator_order = {
        "Magnetic": 0,
        "Electric": 1,
        "Fused": 2,
    }

    position_order = {
        "R": 0,
        "Z": 1,
    }

    metrics_df = metrics_df.copy()

    metrics_df["position_order"] = metrics_df["position"].map(
        position_order
    )

    metrics_df["estimator_order"] = metrics_df["estimator"].map(
        estimator_order
    )

    metrics_df = metrics_df.sort_values(
        by=[
            "shot",
            "position_order",
            "estimator_order",
        ],
        ascending=[
            True,
            True,
            True,
        ]
    ).reset_index(drop=True)

    table = QtWidgets.QTableWidget()
    table.setRowCount(len(metrics_df))
    table.setColumnCount(8)

    table.setHorizontalHeaderLabels([
        "Shot",
        "Analyzed interval [ms]",
        "Position",
        "Estimator",
        "MAE [cm]",
        "RMSE [cm]",
        "MaxAE [cm]",
        "PCC",
    ])

    for row_index, (_, row) in enumerate(metrics_df.iterrows()):
        interval_text = (
            f"{int(row['flat_top_start_ms'])} – "
            f"{int(row['flat_top_end_ms'])}"
        )

        row_values = [
            str(int(row["shot"])),
            interval_text,
            "Radial" if row["position"] == "R" else "Vertical",
            row["estimator"],
            format_metric_value(row["MAE_cm"], "MAE"),
            format_metric_value(row["RMSE_cm"], "RMSE"),
            format_metric_value(row["MaxAE_cm"], "MaxAE"),
            format_metric_value(row["PCC"], "PCC"),
        ]

        for column_index, value in enumerate(row_values):
            item = QtWidgets.QTableWidgetItem(value)

            item.setTextAlignment(
                QtCore.Qt.AlignCenter
            )

            if row["position"] == "R":
                item.setBackground(
                    QtGui.QColor(230, 238, 248)
                )
            else:
                item.setBackground(
                    QtGui.QColor(242, 242, 242)
                )

            table.setItem(
                row_index,
                column_index,
                item
            )

    # ========================================================
    # Merge cells
    # ========================================================
    rows_per_shot = 6
    rows_per_position = 3

    for shot_start_row in range(
        0,
        len(metrics_df),
        rows_per_shot
    ):
        # Merge Shot column across all six rows.
        table.setSpan(
            shot_start_row,
            0,
            rows_per_shot,
            1
        )

        # Merge analyzed interval column across all six rows.
        table.setSpan(
            shot_start_row,
            1,
            rows_per_shot,
            1
        )

        # Merge Radial position across three estimators.
        table.setSpan(
            shot_start_row,
            2,
            rows_per_position,
            1
        )

        # Merge Vertical position across three estimators.
        table.setSpan(
            shot_start_row + rows_per_position,
            2,
            rows_per_position,
            1
        )

    table.setEditTriggers(
        QtWidgets.QAbstractItemView.NoEditTriggers
    )

    table.setSelectionBehavior(
        QtWidgets.QAbstractItemView.SelectRows
    )

    table.setAlternatingRowColors(False)
    table.verticalHeader().setVisible(False)
    table.setSortingEnabled(False)

    header = table.horizontalHeader()

    header.setSectionResizeMode(
        QtWidgets.QHeaderView.Stretch
    )

    header.setStretchLastSection(True)

    # Improve row height for merged cells.
    table.verticalHeader().setDefaultSectionSize(30)

    layout.addWidget(table)

    close_button = QtWidgets.QPushButton("OK")
    close_button.clicked.connect(dialog.accept)

    layout.addWidget(close_button)

    dialog.exec_()

# ============================================================
# Main
# ============================================================
def main():
    validate_configuration()

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True,
    )

    metrics_df = compute_all_metrics()

    detailed_output_path = os.path.join(
        OUTPUT_DIR,
        OUTPUT_FILENAME,
    )

    metrics_df.to_csv(
        detailed_output_path,
        index=False,
    )

    wide_df = create_dissertation_table(
        metrics_df
    )

    wide_output_path = os.path.join(
        OUTPUT_DIR,
        "plasma_position_metrics_all_selected_shots_wide.csv",
    )

    wide_df.to_csv(
        wide_output_path,
        index=False,
    )

    print("\nDetailed metrics:")

    print(
        metrics_df.to_string(
            index=False,
            float_format=lambda value: f"{value:.6f}",
        )
    )

    print(
        f"\nDetailed CSV saved to: "
        f"{detailed_output_path}"
    )

    print(
        f"Wide CSV saved to: "
        f"{wide_output_path}"
    )

    app = QtWidgets.QApplication(sys.argv)

    show_metrics_table_dialog(
        metrics_df
    )

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
import argparse
from sdas.core.client.SDASClient import SDASClient
from sdas.core.SDAStime import TimeStamp
import numpy as np
import pandas as pd
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets, QtCore, QtGui
from pyqtgraph.exporters import ImageExporter
import sys
import os
import re


app = QtWidgets.QApplication(sys.argv)

HOST = 'baco.ipfn.tecnico.ulisboa.pt'
PORT = 8888

def align_signals(csv_signal, sdas_signal):
    correlation = np.correlate(csv_signal - np.mean(csv_signal), sdas_signal - np.mean(sdas_signal), mode='full')
    delay_index = np.argmax(correlation) - (len(sdas_signal) - 1)
    return delay_index

def load_csv_current(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"CSV file not found at: {path}")
    
    df = pd.read_csv(path, delimiter=';')
    df.columns = df.columns.str.strip()
    print("\nSuccessfully loaded", path, "\n")

    time_col = next((col for col in df.columns if col.startswith("#time")), None)
    current_col = next((col for col in df.columns if "outputMpIp (float64)[1]" in col), None)

    if not time_col or not current_col:
        raise ValueError("Time or plasma current column not found in CSV.")

    chopper_col = next((col for col in df.columns if "chopper_trigger" in col), None)

    if chopper_col and df[chopper_col].eq(3).any():
        start_index = df[df[chopper_col] == 3].index.min()
        df_filtered = df.loc[start_index:].reset_index(drop=True)
        print(f"\nChopper trigger found at index {start_index}. Data aligned.\n")
    else:
        df_filtered = df.copy()
        print("\nNo chopper trigger == 3 found. Using full signal.\n")

    time = (df_filtered[time_col] - df_filtered[time_col].iloc[0]) * 1e3  # convert to milliseconds
    current = df_filtered[current_col].values

    return time.to_numpy(), current

def load_sdas_data(client, channel_id, shot_number):
    data_struct = client.getData(channel_id, '0x0000', shot_number)
    data_array = np.array(data_struct[0].getData())
    length = len(data_array)
    t_start = data_struct[0].getTStart()
    t_end = data_struct[0].getTEnd()
    delta_t = (t_end.getTimeInMicros() - t_start.getTimeInMicros()) / length
    time_vector = np.linspace(0, delta_t * (length - 1), length)
    return data_array, time_vector * 1e-3  # convert to milliseconds

def plot_currents(csv_time, csv_current, sdas_time, sdas_current):
    delay_index = align_signals(csv_current, sdas_current)
    dt = np.mean(np.diff(csv_time))
    shift_ms = delay_index * dt
    csv_time_aligned = csv_time - shift_ms

    # Main window
    win = QtWidgets.QMainWindow()
    win.setWindowTitle("Magnetic Reconstruction vs Rogowski Coil Measurement")

    central_widget = QtWidgets.QWidget()
    win.setCentralWidget(central_widget)
    layout = QtWidgets.QVBoxLayout(central_widget)

    # Plot widget
    plot_widget = pg.GraphicsLayoutWidget()
    layout.addWidget(plot_widget)

    plot = plot_widget.addPlot(title="Plasma Current")
    plot.setLabel('bottom', 'Time (ms)')
    plot.setLabel('left', 'Current [A]')
    legend = plot.addLegend()
    legend.setLabelTextSize("11pt")
    plot.setXRange(160, 400, padding=0)
    plot.setYRange(-5000, 5000, padding=0)
    plot.setLimits(xMin=csv_time_aligned.min(), xMax=csv_time_aligned.max(), yMin=-5000, yMax=5000)
    plot.showGrid(x=True, y=True)
    
    # === Adjust fonts  ===
    title_font = QtGui.QFont("Arial", 14, QtGui.QFont.Bold)
    axis_font = QtGui.QFont("Arial", 11, QtGui.QFont.Bold)
    
    plot.titleLabel.item.setFont(title_font)
    plot.getAxis("bottom").label.setFont(axis_font)
    plot.getAxis("left").label.setFont(axis_font)

    plot.plot(csv_time_aligned, csv_current, pen=pg.mkPen('b', width=2), name="Magnetic Reconstruction")
    plot.plot(sdas_time, sdas_current, pen=pg.mkPen('r', width=2, style=QtCore.Qt.DashLine), name="Rogowski Coil Measurement")

    # Export button
    export_btn = QtWidgets.QPushButton("Export Plot")
    layout.addWidget(export_btn)

    def export_plot():
        default_dir = "/home/felipe/git-repos/MARTe2-WaterTank/DataVisualization/Outputs/PlasmaCurrentPlots"
        os.makedirs(default_dir, exist_ok=True)
        default_path = os.path.join(default_dir, f"plasma_current_plot_shot_{pulse_no}.png")
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            None,
            "Save Plot as PNG",
            default_path,
            "PNG Files (*.png)"
        )
        if path:
            exporter = ImageExporter(plot.scene())
            exporter.parameters()['width'] = 1200
            exporter.export(path)
            print(f"\nPlot saved to {path}\n")

    export_btn.clicked.connect(export_plot)

    win.showMaximized()
    win.keyPressEvent = lambda event: app.quit() if event.key() == QtCore.Qt.Key_Escape else None
    sys.exit(app.exec_())

def get_arguments():
    parser = argparse.ArgumentParser(description='Compare plasma current from Magnetic Reconstruction data in CSV and Rogowski Coil data in SDAS')
    parser.add_argument('-s', help='Shot number', default='46241', type=str)
    return parser.parse_args()

if __name__ == '__main__':
    args = get_arguments()
    csv_path, _ = QtWidgets.QFileDialog.getOpenFileName(
        None,
        "Open CSV File",
        "/home/felipe/git-repos/MARTe2-WaterTank/DataVisualization/Outputs/",
        "CSV Files (*.csv);;All Files (*)"
    )

    csv_time, csv_current = load_csv_current(csv_path)

    # Determine the shot number
    pulse_no = args.s
    csv_filename = os.path.basename(csv_path)
    match = re.search(r'(\d{5})', csv_filename)
    if match:
        pulse_no = match.group(1)

    # Channel 228 corresponds to Rogowski coil
    client = SDASClient(HOST, PORT)
    sdas_current, sdas_time = load_sdas_data(client, 'MARTE_NODE_IVO3.DataCollection.Channel_228', int(pulse_no))

    plot_currents(csv_time, csv_current, sdas_time, sdas_current)

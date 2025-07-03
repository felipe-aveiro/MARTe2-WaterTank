import argparse
from sdas.core.client.SDASClient import SDASClient
from sdas.core.SDAStime import TimeStamp
import numpy as np
import pandas as pd
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets, QtCore
import sys
import os

app = QtWidgets.QApplication(sys.argv)

HOST = 'baco.ipfn.tecnico.ulisboa.pt'
PORT = 8888

# csv_path = "/home/felipe/git-repos/MARTe2-WaterTank/Startup/Outputs/IsttokOutput.csv" ## default

def align_signals(csv_signal, sdas_signal):
    correlation = np.correlate(csv_signal - np.mean(csv_signal), sdas_signal - np.mean(sdas_signal), mode='full')
    delay_index = np.argmax(correlation) - (len(sdas_signal) - 1)
    return delay_index

def load_csv_data(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"CSV not found in: {path}")
    
    df = pd.read_csv(path, delimiter=';')
    df.columns = df.columns.str.strip()
    print("\nSuccessfully loaded ", csv_path, "\n")

    time_col = next((col for col in df.columns if col.startswith("#time")), None)
    if time_col is None:
        raise ValueError("No time column found in CSV.")

    chopper_col = next((col for col in df.columns if "chopper_trigger" in col), None)

    if chopper_col and df[chopper_col].eq(3).any():
        start_index = df[df[chopper_col] == 3].index.min()
        df_filtered = df.loc[start_index:].reset_index(drop=True)
        time = (df_filtered[time_col] - df_filtered[time_col].iloc[0]) * 1e3
        print(f"\nChopper trigger found at index {start_index}. Data aligned.\n")
    else:
        df_filtered = df.copy()
        time = (df_filtered[time_col] - df_filtered[time_col].iloc[0]) * 1e3
        print("\nNo chopper_trigger == 3 found or column missing. Using full signal and aligning via correlation.\n")

    mirnov_data = {}
    for i in range(12):
        col = f"inputMirnov{i} (float64)[1]"
        if col in df_filtered.columns:
            mirnov_data[i] = df_filtered[col].values
        else:
            raise ValueError(f"Missing expected column: {col}")

    return time.to_numpy(), time.min(), time.max(), mirnov_data


def LoadSdasData(client, channelID, shotnr):
    dataStruct = client.getData(channelID, '0x0000', shotnr)
    dataArray = np.array(dataStruct[0].getData())
    len_d = len(dataArray)
    tstart = dataStruct[0].getTStart()
    tend = dataStruct[0].getTEnd()
    tbs = (tend.getTimeInMicros() - tstart.getTimeInMicros()) * 1.0 / len_d
    timeVector = np.linspace(0, tbs * (len_d - 1), len_d)
    return dataArray, timeVector * 1e-3

def get_arguments():
    parser = argparse.ArgumentParser(description='Plot Mirnov coils data')
    parser.add_argument('-s', help='shot number', default='46241', type=str)
    return parser.parse_args()

eff_areas = [
    2.793, 2.814, 2.839, 2.635, 2.579, 2.202,
    2.183, 2.218, 2.305, 1.686, 2.705, 2.442
]

cte_mirnov = [(-1.0 / (area * 0.1**3)) for area in eff_areas]

def get_sdas_data(pulseNo):
    client = SDASClient(HOST, PORT)
    data = {}
    for n in range(12):
        ch_id = f'MARTE_NODE_IVO3.DataCollection.Channel_{str(166 + n).zfill(3)}'
        raw_data, time_vector = LoadSdasData(client, ch_id, int(pulseNo))
        data[n] = (raw_data * cte_mirnov[n], time_vector)
    return data

def plot_comparison(csv_time, csv_data, sdas_data):
    dt = np.mean(np.diff(csv_time))
    delay_index = align_signals(csv_data[0], sdas_data[0][0])
    shift_ms = delay_index * dt
    csv_time_aligned = csv_time - shift_ms

    win = pg.GraphicsLayoutWidget(title="Mirnov Coils Comparison")
    win.resize(1200, 800)
    win.setWindowTitle("Mirnov Coils: CSV vs SDAS")

    plot = win.addPlot(title="Click to highlight a Mirnov coil")
    plot.setLabel('bottom', 'Time (ms)')
    plot.setLabel('left', 'Magnetic Field [T]')
    plot.addLegend()
    plot.setXRange(0, 514, padding=0)
    plot.setLimits(xMin=csv_time_aligned.min(), xMax=csv_time_aligned.max())
    plot.showGrid(x=True, y=True)

    csv_color = 'blue'
    sdas_color = 'red'
    highlight_colors = [
        'magenta', 'cyan', 'orange', 'yellow', 'lime', 'purple',
        (255, 128, 0), (0, 255, 128), (255, 0, 128),
        (0, 128, 255), (128, 128, 0), (128, 0, 255)
    ]

    curves = []

    for i in range(12):
        if csv_path == "/home/felipe/git-repos/MARTe2-WaterTank/Startup/Outputs/IsttokOutput.csv": csv_curve = plot.plot(csv_time_aligned, csv_data[i]*1e-9, pen=pg.mkPen(color=csv_color, width=1.2), name=f"Mirnov {i+1} CSV")
        else: csv_curve = plot.plot(csv_time_aligned, csv_data[i], pen=pg.mkPen(color=csv_color, width=1.2), name=f"Mirnov {i+1} CSV")
        sdas_curve = plot.plot(sdas_data[i][1], sdas_data[i][0], pen=pg.mkPen(color=sdas_color, width=1.2, style=QtCore.Qt.DashLine), name=f"Mirnov {i+1} SDAS")
        curves.append((csv_curve, sdas_curve))

    def on_click(event):
        pos = event.scenePos()
        if not plot.sceneBoundingRect().contains(pos):
            return
        mouse_point = plot.vb.mapSceneToView(pos)
        x, y = mouse_point.x(), mouse_point.y()

        min_dist = float('inf')
        closest = None
        for i, (csv_curve, sdas_curve) in enumerate(curves):
            csv_x, csv_y = csv_curve.getData()
            sdas_x, sdas_y = sdas_curve.getData()
            dist_csv = np.min((csv_x - x)**2 + (csv_y - y)**2)
            dist_sdas = np.min((sdas_x - x)**2 + (sdas_y - y)**2)
            if dist_csv < min_dist:
                min_dist = dist_csv
                closest = i
            if dist_sdas < min_dist:
                min_dist = dist_sdas
                closest = i

        if closest is not None:
            for i, (csv_curve, sdas_curve) in enumerate(curves):
                csv_curve.setVisible(i == closest)
                sdas_curve.setVisible(i == closest)

            csv_curve, sdas_curve = curves[closest]
            csv_curve.setPen(pg.mkPen(color=highlight_colors[closest % len(highlight_colors)], width=2.5))
            sdas_curve.setPen(pg.mkPen(color=highlight_colors[(closest+3) % len(highlight_colors)], width=2.5, style=QtCore.Qt.DashLine))

    def reset_view():
        for i, (csv_curve, sdas_curve) in enumerate(curves):
            csv_curve.setVisible(True)
            sdas_curve.setVisible(True)
            csv_curve.setPen(pg.mkPen(color=csv_color, width=1.2))
            sdas_curve.setPen(pg.mkPen(color=sdas_color, width=1.2, style=QtCore.Qt.DashLine))

    win.keyPressEvent = lambda event: (app.quit() if event.key() == QtCore.Qt.Key_Escape else reset_view() if event.key() == QtCore.Qt.Key_R else None)

    plot.scene().sigMouseClicked.connect(on_click)

    win.showMaximized()
    sys.exit(app.exec_())

if __name__ == '__main__':
    args = get_arguments()
    csv_path, _ = QtWidgets.QFileDialog.getOpenFileName(
        None,
        "Open CSV File",
        "/home/felipe/git-repos/MARTe2-WaterTank/Startup/Outputs/",
        "CSV Files (*.csv);;All Files (*)"
    )
    csv_time, _, _, csv_mirnov = load_csv_data(csv_path)
    unique_csv_filenames = {
        "IsttokOutput_Tesla_horario.csv": "53071",
        "IsttokOutput_Tesla.csv": "53071",
        "IsttokOutput_Tesla_PID.csv": "53071"
        # Adicione aqui outros casos específicos
    }
    csv_filename = os.path.basename(csv_path)
    if csv_filename in unique_csv_filenames:
        pulse_no = unique_csv_filenames[csv_filename]
        print(f"Using hardcoded pulse number '{pulse_no}' for file '{csv_filename}'")
    elif csv_filename.lower().startswith("isttokoutput_tesla_") and csv_filename[19:24].isdigit():
        # example: "IsttokOutput_Tesla_46241.csv"
        pulse_no = int(csv_filename[19:24])
        print(f"Inferred pulse number '{pulse_no}' from filename")
    else:
        pulse_no = args.s
        print(f"Using pulse number from arguments: '{pulse_no}'")
    sdas_mirnov = get_sdas_data(pulse_no)
    plot_comparison(csv_time, csv_mirnov, sdas_mirnov)

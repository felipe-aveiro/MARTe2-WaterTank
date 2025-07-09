import argparse
import os
import numpy as np
import csv
from sdas.core.client.SDASClient import SDASClient
from sdas.core.SDAStime import TimeStamp

HOST = 'baco.ipfn.tecnico.ulisboa.pt'
PORT = 8888
DEFAULT_OUTPUT_DIR = '/home/felipe/git-repos/MARTe2-WaterTank/DataVisualization/ISTTOK_shots_CSV_files/csv'

def get_arguments():
    parser = argparse.ArgumentParser(description='Export Mirnov coil data from SDAS to CSV.')
    parser.add_argument('-p', help='Pulse (shot) number', default='46241')
    parser.add_argument('-o', help='Output CSV file path (optional)')
    return parser.parse_args()

def signal_name_dict():
    signal_dict = {
        # Add Mirnov probe channels (166–178)
        f'Mirnov coil no. {n+1}': f'MARTE_NODE_IVO3.DataCollection.Channel_{str(166+n).zfill(3)}'
        for n in range(12)
    }

    # Add Langmuir probe channels (024–027)
    for i in range(4):
        signal_dict[f'Langmuir probe no. {i+1}'] = f'MARTE_NODE_IVO3.DataCollection.Channel_{str(24+i).zfill(3)}'

    return signal_dict


def LoadSdasData(client, channelID, shotnr):
    dataStruct = client.getData(channelID, '0x0000', shotnr)
    dataArray = dataStruct[0].getData()
    len_d = len(dataArray)
    tstart = dataStruct[0].getTStart()
    tend = dataStruct[0].getTEnd()
    tbs = (tend.getTimeInMicros() - tstart.getTimeInMicros()) / (len_d - 1)
    
    print(f"\nSampling period: {tbs} µs")
    print(f"\nExpected: {1e6/10000:.1f} µs\n")  # 100 µs

    events = dataStruct[0].get('events')[0]
    tevent = TimeStamp(tstamp=events.get('tstamp'))
    delay = tstart.getTimeInMicros() - tevent.getTimeInMicros()
    timeVector = np.linspace(delay / 1000.0, (delay + tbs * (len_d - 1)) / 1000.0, len_d)  # ms

    return np.array(dataArray), timeVector

def get_all_data(pulseNo, client=None):
    if client is None:
        client = SDASClient(HOST, PORT)
    signalNames = signal_name_dict()

    signals = {}
    time_vector = None

    for idx, (key, channel) in enumerate(signalNames.items()):
        print(f"Downloading {key}...")
        signal_data, time = LoadSdasData(client, channel, int(pulseNo))
        signals[idx] = signal_data
        if time_vector is None:
            time_vector = time

    return signals, time_vector

def save_to_csv(signals: dict, time_vector: np.ndarray, output_path: str):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')

        # Header
        header = ['#timeI (float64)[1]'] + [f'integ_ch{idx} (float64)[1]' for idx in sorted(signals.keys())]
        writer.writerow(header)

        # Write data
        n_samples = len(time_vector)
        for i in range(n_samples):
            row = ['%.16f' % (time_vector[i]/1000.0)]
            for idx in sorted(signals.keys()):
                row.append('%.16f' % signals[idx][i])
            writer.writerow(row)

    
    print(f"\nData saved to: {output_path}\n")

if __name__ == '__main__':
    args = get_arguments()
    shot = args.p

    if args.o:
        output_file = args.o
    else:
        output_file = os.path.join(DEFAULT_OUTPUT_DIR, f"SDAS_shot_{shot}.csv")

    print(f"\nFetching data for shot #{shot}...\n")
    signals, time_vector = get_all_data(shot)
    save_to_csv(signals, time_vector, output_file)

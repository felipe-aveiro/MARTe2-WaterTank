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
    parser.add_argument('-s', help='Shot number', default='46241')
    parser.add_argument('-o', help='Output CSV file path (optional)')
    parser.add_argument('--dtype', help='Floating point type: float32 or float64', default='float64', choices=['float32', 'float64'])
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
    
    # Rogowski coil channel (228)
    signal_dict['Rogowski coil'] = 'MARTE_NODE_IVO3.DataCollection.Channel_228'

    return signal_dict


def LoadSdasData(client, channelID, shotnr, dtype):
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
    timeVector = np.linspace(delay / 1000.0, (delay + tbs * (len_d - 1)) / 1000.0, len_d, dtype=dtype)  # ms

    return np.array(dataArray, dtype=dtype), timeVector

def get_all_data(pulseNo, dtype, client=None):
    if client is None:
        client = SDASClient(HOST, PORT)
    signalNames = signal_name_dict()

    signals = {}
    time_vector = None

    for idx, (key, channel) in enumerate(signalNames.items()):
        print(f"Downloading {key}...")
        signal_data, time = LoadSdasData(client, channel, int(pulseNo), dtype)
        signals[idx] = signal_data
        if time_vector is None:
            time_vector = time

    return signals, time_vector

def save_to_csv(signals: dict, time_vector: np.ndarray, output_path: str, dtype: str):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')

        # Header
        header = [f'#timeI ({dtype})[1]']
        for idx in sorted(signals.keys()):
            if idx < 12:
                header.append(f'integ_ch{idx} ({dtype})[1]') # Mirnovs
            elif 12 <= idx < 16:
                header.append(f'integ_ch{idx} ({dtype})[1]') # Langmuirs
            else:
                header.append(f'rogowski_ch ({dtype})[1]') # Rogowski
        writer.writerow(header)
        
        if dtype == 'float32':
            precision = 8
        else:  # float64
            precision = 16
            
        # Write data
        n_samples = len(time_vector)
        for i in range(n_samples):
            row = [f'{time_vector[i]/1000.0:.{precision}f}']  # Convert to ms
            for key in signals.keys():
                row.append(f'{signals[key][i]:.{precision}f}')
            writer.writerow(row)
    
    print(f"\nData saved to: {output_path}\n")

if __name__ == '__main__':
    args = get_arguments()
    shot = args.s
    dtype = args.dtype

    if args.o:
        output_file = args.o
    else:
        if dtype == 'float32':
            output_file = os.path.join(DEFAULT_OUTPUT_DIR, f"SDAS_shot_{shot}_float32.csv")
        else:  # float64
            output_file = os.path.join(DEFAULT_OUTPUT_DIR, f"SDAS_shot_{shot}.csv")

    print(f"\nFetching data for shot #{shot} with dtype {dtype}...\n")
    signals, time_vector = get_all_data(shot, dtype)
    save_to_csv(signals, time_vector, output_file, dtype)

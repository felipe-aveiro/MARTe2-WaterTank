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
    parser = argparse.ArgumentParser(description='Export Domenica Position R/Z from SDAS to CSV.')
    parser.add_argument('-s', help='Shot number', default='46241')
    parser.add_argument('-o', help='Output CSV file path (optional)')
    parser.add_argument(
        '--dtype',
        help='Floating point type: float32 or float64',
        default='float64',
        choices=['float32', 'float64']
    )
    return parser.parse_args()

def signal_name_dict():
    # Only Domenica positions
    return {
        'PositionR': 'MARTE_NODE_IVO3.DataCollection.Channel_101',
        'PositionZ': 'MARTE_NODE_IVO3.DataCollection.Channel_102'
    }

def LoadSdasData(client, channelID, shotnr, dtype):
    dataStruct = client.getData(channelID, '0x0000', shotnr)
    dataArray = dataStruct[0].getData()
    len_d = len(dataArray)

    tstart = dataStruct[0].getTStart()
    tend = dataStruct[0].getTEnd()
    tbs = (tend.getTimeInMicros() - tstart.getTimeInMicros()) / (len_d - 1)

    # Debug prints to confirm sampling period
    print(f"\nSampling period: {tbs} µs")
    print(f"\nExpected: {1e6/10000:.1f} µs\n")  # 100 µs

    # Build time vector aligned to the shot event timestamp
    events = dataStruct[0].get('events')[0]
    tevent = TimeStamp(tstamp=events.get('tstamp'))
    delay = tstart.getTimeInMicros() - tevent.getTimeInMicros()

    # Time in ms (kept consistent with your existing convention)
    timeVector = np.linspace(
        delay / 1000.0,
        (delay + tbs * (len_d - 1)) / 1000.0,
        len_d,
        dtype=dtype
    )

    return np.array(dataArray, dtype=dtype), timeVector

def get_all_data(pulseNo, dtype, client=None):
    if client is None:
        client = SDASClient(HOST, PORT)

    signalNames = signal_name_dict()
    signals = {}
    time_vector = None

    for idx, (key, channel) in enumerate(signalNames.items()):
        print(f"Downloading {key} ({channel})...")
        signal_data, time = LoadSdasData(client, channel, int(pulseNo), dtype)
        signals[idx] = signal_data

        # Use the first channel time vector as reference
        if time_vector is None:
            time_vector = time

    return signals, time_vector

def _header_name_for_index(idx: int, dtype: str) -> str:
    # Explicit naming to avoid ambiguity in downstream scripts
    if idx == 0:
        return f'PositionR ({dtype})[1]'
    if idx == 1:
        return f'PositionZ ({dtype})[1]'
    return f'ch{idx} ({dtype})[1]'

def save_to_csv(signals: dict, time_vector: np.ndarray, output_path: str, dtype: str):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')

        # Header
        header = [f'#timeI ({dtype})[1]']
        for idx in sorted(signals.keys()):
            header.append(_header_name_for_index(idx, dtype))
        writer.writerow(header)

        # Match your formatting precision policy
        precision = 8 if dtype == 'float32' else 16

        # Write data
        n_samples = len(time_vector)
        for i in range(n_samples):
            # Keep your original convention: store time in seconds (ms / 1000)
            row = [f'{time_vector[i]/1000.0:.{precision}f}']
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
        # Keep the same naming convention you already use
        if dtype == 'float32':
            output_file = os.path.join(DEFAULT_OUTPUT_DIR, f"SDAS_shot_{shot}_domenica_float32.csv")
        else:
            output_file = os.path.join(DEFAULT_OUTPUT_DIR, f"SDAS_shot_{shot}_domenica.csv")

    print(f"\nFetching Domenica Position R/Z for shot #{shot} with dtype {dtype}...\n")
    signals, time_vector = get_all_data(shot, dtype)
    save_to_csv(signals, time_vector, output_file, dtype)

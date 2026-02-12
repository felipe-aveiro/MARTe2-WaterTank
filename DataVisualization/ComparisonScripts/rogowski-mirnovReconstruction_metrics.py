import argparse
import os
import re
import numpy as np
import pandas as pd
from sdas.core.client.SDASClient import SDASClient

# === SDAS connection details ===
HOST = 'baco.ipfn.tecnico.ulisboa.pt'
PORT = 8888

def align_signals(csv_signal, sdas_signal):
    """Align two signals using cross-correlation and return delay index."""
    correlation = np.correlate(csv_signal - np.mean(csv_signal), sdas_signal - np.mean(sdas_signal), mode='full')
    delay_index = np.argmax(correlation) - (len(sdas_signal) - 1)
    return delay_index

def load_csv_current(path):
    """Load plasma current from CSV and return time (ms) and current (A)."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"CSV file not found at: {path}")
    
    df = pd.read_csv(path, delimiter=';')
    df.columns = df.columns.str.strip()

    time_col = next((col for col in df.columns if col.startswith("#time")), None)
    current_col = next((col for col in df.columns if "outputMpIp (float64)[1]" in col), None)

    if not time_col or not current_col:
        raise ValueError("Time or plasma current column not found in CSV.")

    chopper_col = next((col for col in df.columns if "chopper_trigger" in col), None)

    # Align start based on chopper trigger
    if chopper_col and df[chopper_col].eq(3).any():
        start_index = df[df[chopper_col] == 3].index.min()
        df_filtered = df.loc[start_index:].reset_index(drop=True)
    else:
        df_filtered = df.copy()

    time = (df_filtered[time_col] - df_filtered[time_col].iloc[0]) * 1e3  # ms
    current = df_filtered[current_col].values

    return time.to_numpy(), current

def load_sdas_data(client, channel_id, shot_number):
    """Load data from SDAS and return array and time vector in ms."""
    data_struct = client.getData(channel_id, '0x0000', shot_number)
    data_array = np.array(data_struct[0].getData())
    length = len(data_array)
    t_start = data_struct[0].getTStart()
    t_end = data_struct[0].getTEnd()
    delta_t = (t_end.getTimeInMicros() - t_start.getTimeInMicros()) / length
    time_vector = np.linspace(0, delta_t * (length - 1), length)
    return data_array, time_vector * 1e-3  # ms

def compute_metrics(signal1, signal2):
    """Compute MAE, RMSE, Max Diff."""
    abs_diffs = np.abs(signal1 - signal2)
    squared_diffs = (signal1 - signal2) ** 2
    mae = np.mean(abs_diffs)
    rmse = np.sqrt(np.mean(squared_diffs))
    max_diff = np.max(abs_diffs)
    return mae, rmse, max_diff

def main():
    parser = argparse.ArgumentParser(description='Compare plasma current signals: Magnetic Reconstruction vs Rogowski Coil')
    parser.add_argument('-s', help='Shot number', default='46241', type=str)
    parser.add_argument('--csv', help='Path to CSV file', required=True)
    args = parser.parse_args()

    # === Load CSV ===
    csv_time, csv_current = load_csv_current(args.csv)

    # === Determine shot number ===
    pulse_no = args.s
    csv_filename = os.path.basename(args.csv)
    match = re.search(r'(\d{5})', csv_filename)
    if match:
        pulse_no = match.group(1)

    # === Load SDAS data ===
    client = SDASClient(HOST, PORT)
    sdas_current, sdas_time = load_sdas_data(client, 'MARTE_NODE_IVO3.DataCollection.Channel_088', int(pulse_no))

    # === Align signals ===
    delay_index = align_signals(csv_current, sdas_current)
    dt = np.mean(np.diff(csv_time))
    shift_ms = delay_index * dt
    csv_time_aligned = csv_time - shift_ms

    # === Match lengths for comparison ===
    min_len = min(len(csv_current), len(sdas_current))
    csv_current_trimmed = csv_current[:min_len]
    sdas_current_trimmed = sdas_current[:min_len]

    # === Compute metrics ===
    mae, rmse, max_diff = compute_metrics(csv_current_trimmed, sdas_current_trimmed)

    # === Print results ===
    print("\nPlasma Current Comparison Metrics:")
    print(f"  ➤ Mean Absolute Error (MAE): {mae:.3f} A")
    print(f"  ➤ Root Mean Square Error (RMSE): {rmse:.3f} A")
    print(f"  ➤ Max Difference: {max_diff:.3f} A")

if __name__ == '__main__':
    main()

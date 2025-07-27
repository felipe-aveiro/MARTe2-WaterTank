#!/usr/bin/env python3
"""
This script exports MARTe2 ATCAIop samples stored in MDSplus to a single CSV file.
CSV file can be compressed or uncompressed based on user flag.
"""
import numpy as np
import argparse
import os
import csv
import gzip
import time
from tqdm import tqdm
from ClientMdsThin import ClientMdsThin as cltMds

ADC_CHANNELS = 16  # channels stored in ISTTOK MDS
ADC_BIT_LSHIFT = 2**14
MDS_URL = "oper@atca-marte2"

def save_combined_csv(filename, timeR, raw_data, timeI, integ_data, chopper_data, channel_range, maxpoints, compress):
    """Save all data to a CSV file (compressed or uncompressed)."""
    num_samples_raw = min(len(timeR), maxpoints)
    num_samples_integ = min(len(timeI), maxpoints)
    num_samples_chopper = min(len(chopper_data), maxpoints)
    
    max_rows = max(num_samples_raw, num_samples_integ, num_samples_chopper)

    open_func = gzip.open if compress else open
    mode = 'wt' if compress else 'w'

    with open_func(filename, mode=mode, newline='') as file:
        writer = csv.writer(file)
        
        # Header
        header = ["timeR (float64)[1]"] + [f"raw_ch{ch} (float64)[1]" for ch in channel_range]
        header += ["timeI (float64)[1]"] + [f"integ_ch{ch} (float64)[1]" for ch in channel_range]
        header += ["chopper_trigger (float64)[1]"]
        writer.writerow(header)

        for i in tqdm(range(max_rows), desc="Writing CSV"):
            row = []
            # Raw
            if i < num_samples_raw:
                row.append(str(timeR[i]))
                row += [str(raw_data[ch][i]) for ch in channel_range]
            else:
                row += ["" for _ in range(1 + len(channel_range))]

            # Integrated
            if i < num_samples_integ:
                row.append(str(timeI[i]))
                row += [str(integ_data[ch][i]) for ch in channel_range]
            else:
                row += ["" for _ in range(1 + len(channel_range))]

            # Chopper Trigger
            if i < num_samples_chopper:
                row.append(str(chopper_data[i]))
            else:
                row.append("")

            writer.writerow(row)

def main():
    parser = argparse.ArgumentParser(description="Export ATCAIop MDSplus data to CSV (compressed or uncompressed)")
    parser.add_argument('-s', '--shot', type=int, required=True, help='MDSplus pulse number')
    parser.add_argument('-c', '--crange', nargs='+', type=int, default=[1, 16], help='Channel range to export (e.g. 1 16)')
    parser.add_argument('-u', '--url', default=MDS_URL, help='MDSplus host URL')
    parser.add_argument('-m', '--maxpoints', type=int, default=500000, help='Maximum number of points to export')
    parser.add_argument('--gz', action='store_true', help='Export compressed CSV (.csv.gz)')
    args = parser.parse_args()
    print(f"\nArgs.shot {args.shot}\n")

    start_ch = args.crange[0] - 1
    end_ch = args.crange[1]
    channel_range = list(range(start_ch, end_ch))

    print(f"Connecting to MDSplus at {args.url} for shot {args.shot}")
    mclient = cltMds(url=args.url, num_channels=ADC_CHANNELS)
    mclient.getTreeData(shot=args.shot)

    # Decide file name based on compression
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    if args.gz:
        output_file = os.path.join(BASE_DIR, "ISTTOK_shots_CSV_files", "gz", f"MDS_shot_{args.shot}.csv.gz")
    else:
        output_file = os.path.join(BASE_DIR, "ISTTOK_shots_CSV_files", "csv", f"MDS_shot_{args.shot}.csv")

    # Ensure full directory tree exists (create parent folders if needed)
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    print(f"Exporting data to {output_file}\n")

    start_time = time.perf_counter()

    save_combined_csv(
        output_file,
        mclient.timeR,
        mclient.adcRawData,
        mclient.timeI,
        mclient.adcIntegData,
        mclient.choppTrigg,
        channel_range,
        args.maxpoints,
        compress=args.gz
    )

    end_time = time.perf_counter()
    elapsed = end_time - start_time
    print(f"\nExport completed successfully in {elapsed:.2f} seconds!\n")

if __name__ == '__main__':
    main()

import pandas as pd
import numpy as np
import sys

# Load and parse data
def parse_hist_string(s):
    return list(map(int, s.strip("{} ").split()))

file_path = "/home/felipe/git-repos/MARTe2-WaterTank/DataVisualization/Outputs/WTM-Simulink-histogram.csv"
df = pd.read_csv(file_path)
raw_strings = df.iloc[:, 0]
parsed_data = raw_strings.apply(parse_hist_string)

# Get last row
last_row = parsed_data.iloc[59999]

# Load second CSV for comparison
file_path_2 = "/home/felipe/git-repos/MARTe2-WaterTank/DataVisualization/Outputs/WTM-GAM-histogram.csv"
df_2 = pd.read_csv(file_path_2)
raw_strings_2 = df_2.iloc[:, 0]
parsed_data_2 = raw_strings_2.apply(parse_hist_string)
last_row_2 = parsed_data_2.iloc[59999]

# Ensure both histograms have same length
if len(last_row) != len(last_row_2):
    raise ValueError("Histograms have different bin counts.")


# Compute percentages for both
total_counts_1 = sum(last_row)
total_counts_2 = sum(last_row_2)

# Ensure both histograms have same cycle count
if total_counts_1 != total_counts_2:
    raise ValueError("Histograms have different cycle count.")

percentages_1 = np.array(last_row) / total_counts_1 * 100
percentages_2 = np.array(last_row_2) / total_counts_2 * 100
abs_diffs = np.abs(percentages_1 - percentages_2)
squared_diffs = (percentages_1 - percentages_2) ** 2

# Compute metrics
mae = sum(abs_diffs) / len(abs_diffs)
rmse = (sum(squared_diffs) / len(squared_diffs)) ** 0.5
max_diff = max(abs_diffs)

print("\nHistogram Comparison Metrics:")
print(f"  ➤\tMean Absolute Error (MAE): {mae:.3f}%")
print(f"  ➤\tRoot Mean Square Error (RMSE): {rmse:.3f}%")
print(f"  ➤\tMax Difference: {max_diff:.3f}%\n")

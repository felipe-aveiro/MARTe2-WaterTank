import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt

# === Configuration ===
shots_weights = {
    45754: 1.0,  # Multiple AC pulses, but irregular shape and premature endings
    45967: 2.0,  # Several perfect positive pulses, all nominal current
    46241: 3.0,  # Best overall, perfect regular AC pulses, ideal case
    53071: 1.5,  # One positive + two negatives, good regularity but slight current drop on negatives
    53099: 0.5,  # Poor quality pulses, irregular current, below nominal
    53105: 1.5   # Single AC cycle, regular behavior but slightly under nominal current
}

base_path = "/home/felipe/git-repos/MARTe2-WaterTank/DataVisualization/Outputs/"
csv_template = "IsttokOutput_Tesla_{}.csv"

all_Rp_MP = []
all_Zp_MP = []
all_weights_MP = []

# === Parameters ===
zscore_thresh = 2.0   # For outlier filtering

# === Process each shot ===
for shot, weight in shots_weights.items():
    filepath = os.path.join(base_path, csv_template.format(shot))
    try:
        df = pd.read_csv(filepath, delimiter=';')
        Rp = df["outputMpR (float64)[1]"].values
        Zp = df["outputMpZ (float64)[1]"].values
        
        # Remove NaNs
        valid_mask = ~np.isnan(Rp) & ~np.isnan(Zp)
        Rp = Rp[valid_mask]
        Zp = Zp[valid_mask]

        # === Cutoff based on physical constraints
        a = 0.085
        R0 = 0.46
        rp_min, rp_max = R0 - a, R0 + a
        zp_min, zp_max = -a, a

        range_mask = (Rp > rp_min) & (Rp < rp_max) & (Zp > zp_min) & (Zp < zp_max)
        Rp = Rp[range_mask]
        Zp = Zp[range_mask]

        # Remove outliers using z-score
        z_rp = np.abs((Rp - np.mean(Rp)) / np.std(Rp))
        z_zp = np.abs((Zp - np.mean(Zp)) / np.std(Zp))
        combined_mask = (z_rp < zscore_thresh) & (z_zp < zscore_thresh)
        Rp = Rp[combined_mask]
        Zp = Zp[combined_mask]

        # Append
        all_Rp_MP.extend(Rp)
        all_Zp_MP.extend(Zp)
        all_weights_MP.extend([weight] * len(Rp))

    except Exception as e:
        print(f"Failed to process shot {shot}: {e}")

# === Convert to arrays
all_Rp_MP = np.array(all_Rp_MP)
all_Zp_MP = np.array(all_Zp_MP)
all_weights_MP = np.array(all_weights_MP)

# === Weighted statistics
mean_Rp = np.average(all_Rp_MP, weights=all_weights_MP)
mean_Zp = np.average(all_Zp_MP, weights=all_weights_MP)

cov_num = np.sum(all_weights_MP * (all_Rp_MP - mean_Rp) * (all_Zp_MP - mean_Zp))
cov_den = np.sum(all_weights_MP)
weighted_cov = cov_num / cov_den

std_Rp = np.sqrt(np.sum(all_weights_MP * (all_Rp_MP - mean_Rp)**2) / cov_den)
std_Zp = np.sqrt(np.sum(all_weights_MP * (all_Zp_MP - mean_Zp)**2) / cov_den)
weighted_corr = weighted_cov / (std_Rp * std_Zp)

# === Results ===
print(f"\nFiltered & weighted correlation (Rp vs Zp): {weighted_corr:.16f}\n")
print(f"Filtered & weighted covariance (Rp vs Zp): {weighted_cov:.6e}\n")

# === Visual correlation
fig, ax = plt.subplots(figsize=(10, 6), constrained_layout=True)
ax.scatter(all_Rp_MP, all_Zp_MP, s=3.5, alpha=1.0)
# Font dictionary for customization
title_font = {'fontsize': 20, 'fontweight': 'bold'}
label_font = {'fontsize': 18}
ax.set_xlabel("Radial position [m]", fontdict=label_font, labelpad=15)
ax.set_ylabel("Vertical position [m]", fontdict=label_font, labelpad=15)
ax.set_title("Mirnov Coils Scatter Plot", fontdict=title_font, pad=20)
ax.tick_params(axis='both', labelsize=14)
ax.grid(True)
plt.show()

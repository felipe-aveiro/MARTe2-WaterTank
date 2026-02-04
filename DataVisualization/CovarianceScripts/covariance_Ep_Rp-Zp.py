import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt

# === Define weights based on plasma behavior quality (AC pulse stability, symmetry, etc.) ===
# Higher weights represent better performance and relevance for defining global coefficients
shot_weights = {
    45754: 1.35, # Multiple AC pulses, but irregular shape and premature endings
    45967: 3.0, # Several perfect positive pulses, all nominal current
    46241: 3.0, # Best overall, perfect regular AC pulses, ideal case
    52856: 1.0, # Two AC pulses, below nominal and irregular
    52857: 1.35, # Six AC pulses, below nominal and irregular
    53058: 2.06, # One positive + three negatives, nominal current, some irregularity
    53071: 2.41, # One positive + two negatives, good regularity but slight current drop on negatives
    53099: 1.82, # Poor quality pulses, irregular current, below nominal
    53105: 2.06, # Single AC cycle, regular behavior but slightly under nominal current
    53197: 1.35, # Three AC pulses, well below nominal and irregular
}

base_path = "/home/felipe/git-repos/MARTe2-WaterTank/DataVisualization/Outputs/"
csv_template = "IsttokOutput_Tesla_{}.csv"

all_Rp_LP = []
all_Zp_LP = []
all_weights_LP = []

# === Process each shot ===
for shot, weight in shot_weights.items():
    filepath = os.path.join(base_path, csv_template.format(shot))
    try:
        df = pd.read_csv(filepath, delimiter=';')
        Rp = df["outputEpR (float64)[1]"].values
        Zp = df["outputEpZ (float64)[1]"].values

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

        # Append
        all_Rp_LP.extend(Rp)
        all_Zp_LP.extend(Zp)
        all_weights_LP.extend([weight] * len(Rp))

    except Exception as e:
        print(f"Failed to process shot {shot}: {e}")

# === Convert to arrays
all_Rp_LP = np.array(all_Rp_LP)
all_Zp_LP = np.array(all_Zp_LP)
all_weights_LP = np.array(all_weights_LP)

# === Weighted statistics
mean_Rp_LP = np.average(all_Rp_LP, weights=all_weights_LP)
mean_Zp_LP = np.average(all_Zp_LP, weights=all_weights_LP)

cov_num_LP = np.sum(all_weights_LP * (all_Rp_LP - mean_Rp_LP) * (all_Zp_LP - mean_Zp_LP))
cov_den_LP = np.sum(all_weights_LP)
weighted_cov_LP = cov_num_LP / cov_den_LP

std_Rp_LP = np.sqrt(np.sum(all_weights_LP * (all_Rp_LP - mean_Rp_LP)**2) / cov_den_LP)
std_Zp_LP = np.sqrt(np.sum(all_weights_LP * (all_Zp_LP - mean_Zp_LP)**2) / cov_den_LP)
weighted_corr_LP = weighted_cov_LP / (std_Rp_LP * std_Zp_LP)

# === Results ===
print(f"\nFiltered & weighted correlation (EpR vs EpZ): {weighted_corr_LP:.16f}\n")
print(f"Filtered & weighted covariance (EpR vs EpZ): {weighted_cov_LP:.6e}\n")
print(f"Off-diagonal elements (EpR vs EpZ): {(0.025**2)*weighted_corr_LP:.6e}\n")

# === Visual correlation
fig, ax = plt.subplots(figsize=(10, 6), constrained_layout=True)
ax.scatter(all_Rp_LP, all_Zp_LP, s=3.5, alpha=1.0, color="darkorange")
# Font dictionary for customization
title_font = {'fontsize': 20, 'fontweight': 'bold'}
label_font = {'fontsize': 18}
ax.set_xlabel("Radial position [m]", fontdict=label_font, labelpad=15)
ax.set_ylabel("Vertical position [m]", fontdict=label_font, labelpad=15)
ax.set_title("Langmuir Probes Scatter Plot", fontdict=title_font, pad=20)
ax.tick_params(axis='both', labelsize=14)
ax.grid(True)
plt.show()

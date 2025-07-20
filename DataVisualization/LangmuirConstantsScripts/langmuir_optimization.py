import pandas as pd

# === 1. Load CSV with coefficients per shot ===
csv_path = '/home/felipe/git-repos/MARTe2-WaterTank/DataVisualization/Outputs/langmuir_coeficients.csv'
df = pd.read_csv(csv_path)

# === 2. Define weights based on plasma behavior quality (AC pulse stability, symmetry, etc.) ===
# Higher weights represent better performance and relevance for defining global coefficients
shot_weights = {
    45754: 1.0,  # Multiple AC pulses, but irregular shape and premature endings
    45967: 2.0,  # Several perfect positive pulses, all nominal current
    46241: 3.0,  # Best overall, perfect regular AC pulses, ideal case
    53071: 1.5,  # One positive + two negatives, good regularity but slight current drop on negatives
    53099: 0.5,  # Poor quality pulses, irregular current, below nominal
    53105: 1.5   # Single AC cycle, regular behavior but slightly under nominal current
}

# === 3. Map weights to the DataFrame ===
df['Weight'] = df['Shot'].astype(int).map(shot_weights)

# === 4. Filter only valid shots with defined weights ===
df_filtered = df.dropna(subset=['Weight']).copy()

# === 5. Compute weighted average of calibration coefficients ===
coeff_names = ['C1', 'C2', 'C3', 'C4']
total_weight = df_filtered['Weight'].sum()

# Dictionary to store the final weighted coefficients
weighted_coeffs = {
    name: (df_filtered[name] * df_filtered['Weight']).sum() / total_weight
    for name in coeff_names
}

# === 6. Print results ===
print("\nFinal weighted coefficients (based on shot behavior quality):\n")
for name, value in weighted_coeffs.items():
    print(f"{name} = (double) {value:.16e}")
print()
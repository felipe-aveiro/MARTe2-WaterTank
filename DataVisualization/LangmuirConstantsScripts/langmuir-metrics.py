import pandas as pd
import numpy as np
from sklearn.linear_model import HuberRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error
import sys
import os

shot_numbers = [45754, 45967, 46241, 53071, 53099, 53105]
shot_weights = {
    45754: 1.0,  # Multiple AC pulses, but irregular shape and premature endings
    45967: 2.0,  # Several perfect positive pulses, all nominal current
    46241: 3.0,  # Best overall, perfect regular AC pulses, ideal case
    53071: 1.5,  # One positive + two negatives, good regularity but slight current drop on negatives
    53099: 0.5,  # Poor quality pulses, irregular current, below nominal
    53105: 1.5   # Single AC cycle, regular behavior but slightly under nominal current
}

base_dir = "/home/felipe/git-repos/MARTe2-WaterTank/DataVisualization/Outputs/"

results = []

for identifier in shot_numbers:
    
    file_path = os.path.join(base_dir, f"IsttokOutput_Tesla_{identifier}.csv")

    df = pd.read_csv(file_path, sep=';')

    # === 2. Clean data ===
    if '#timeI (float64)[1]' in df.columns:
        df = df[df['#timeI (float64)[1]'] >= 0]

    required_cols = [
        'langmuir_outer (float64)[1]',
        'langmuir_inner (float64)[1]',
        'langmuir_top (float64)[1]',
        'langmuir_bottom (float64)[1]',
        'outputMpR (float64)[1]',
        'outputMpZ (float64)[1]'
    ]
    
    df.dropna(subset=required_cols, inplace=True)

    # Physical limits filtering
    a = 0.085
    R_center, Z_center = 0.46, 0.0
    R_lower, R_upper = R_center - a, R_center + a
    Z_lower, Z_upper = Z_center - a, Z_center + a
    df = df[
        (df['outputMpR (float64)[1]'] >= R_lower) & (df['outputMpR (float64)[1]'] <= R_upper) &
        (df['outputMpZ (float64)[1]'] >= Z_lower) & (df['outputMpZ (float64)[1]'] <= Z_upper)
    ]

    time = df['#timeI (float64)[1]'].values * 1e3 if '#timeI (float64)[1]' in df.columns else np.arange(len(df))

    # === 3. Voltage differences ===
    df['deltaR'] = df['langmuir_outer (float64)[1]'] - df['langmuir_inner (float64)[1]']
    df['deltaZ'] = df['langmuir_top (float64)[1]'] - df['langmuir_bottom (float64)[1]']

    # === 4. Fit HuberRegressor ===
    X_R, y_R = df[['deltaR']], df['outputMpR (float64)[1]']
    X_Z, y_Z = df[['deltaZ']], df['outputMpZ (float64)[1]']

    model_R = HuberRegressor(epsilon=1.3).fit(X_R, y_R)
    model_Z = HuberRegressor(epsilon=1.3).fit(X_Z, y_Z)

    C1, C2 = model_R.coef_[0], model_R.intercept_
    C3, C4 = model_Z.coef_[0], model_Z.intercept_

    # === 5. Predictions and error metrics ===
    y_R_pred, y_Z_pred = model_R.predict(X_R), model_Z.predict(X_Z)

    # Errors
    errors_R = y_R.values - y_R_pred
    errors_Z = y_Z.values - y_Z_pred

    # Metrics
    rmse_R = np.sqrt(mean_squared_error(y_R, y_R_pred))
    rmse_Z = np.sqrt(mean_squared_error(y_Z, y_Z_pred))
    
    mae_R = mean_absolute_error(y_R, y_R_pred)
    mae_Z = mean_absolute_error(y_Z, y_Z_pred)

    median_err_R = np.median(np.abs(errors_R))
    median_err_Z = np.median(np.abs(errors_Z))
    
    IQR_R = np.percentile(errors_R, 75) - np.percentile(errors_R, 25)
    IQR_Z = np.percentile(errors_Z, 75) - np.percentile(errors_Z, 25)
    
    results.append({
        'Shot': identifier,
        'Weight': shot_weights[identifier],
        'C1': C1, 'C2': C2, 'C3': C3, 'C4': C4,
        'RMSE_R': rmse_R, 'RMSE_Z': rmse_Z,
        'MAE_R': mae_R, 'MAE_Z': mae_Z,
        'Median_R': median_err_R, 'Median_Z': median_err_Z,
        'IQR_R': IQR_R, 'IQR_Z': IQR_Z,
    })
    
# === Compute weighted global metrics ===
df_results = pd.DataFrame(results)
total_weight = df_results['Weight'].sum()

metrics = ['RMSE_R', 'RMSE_Z', 'MAE_R', 'MAE_Z', 'Median_R', 'Median_Z', 'IQR_R', 'IQR_Z']
weighted_metrics = {metric: (df_results[metric] * df_results['Weight']).sum() / total_weight for metric in metrics}

print("\n========== Weighted Global Metrics ==========")
for metric, value in weighted_metrics.items():
    print(f"{metric}: {value*100:.3f} cm")
print("=============================================\n")

for values in results:
    print(f"Shot {values['Shot']}:\n")
    print(f"Median_R: {values['Median_R']*100:.3f} cm")
    print(f"Median_Z: {values['Median_Z']*100:.3f} cm")
    print('-----------------------------')
     


import pandas as pd
import numpy as np
from sklearn.linear_model import HuberRegressor
from sklearn.metrics import mean_squared_error, r2_score
from pyqtgraph.Qt import QtWidgets, QtCore
import pyqtgraph as pg
import sys
import os

app = QtWidgets.QApplication(sys.argv)

# === 1. Select CSV ===
file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
    None,
    "Open CSV File",
    "/home/felipe/git-repos/MARTe2-WaterTank/DataVisualization/Outputs/",
    "CSV Files (*.csv);;All Files (*)"
)
if not file_path:
    print("No file selected.")
    sys.exit()

df = pd.read_csv(file_path, sep=';')

# === 2. Clean: remove t < 0 and NaNs ===
if '#timeI (float64)[1]' in df.columns:
    df = df[df['#timeI (float64)[1]'] >= 0]

# Remove rows with NaNs in any critical column
required_cols = [
    'langmuir_outer (float64)[1]',
    'langmuir_inner (float64)[1]',
    'langmuir_top (float64)[1]',
    'langmuir_bottom (float64)[1]',
    'outputMpR (float64)[1]',
    'outputMpZ (float64)[1]'
]
df.dropna(subset=required_cols, inplace=True)

# Remove outliers by standard deviation limit
z_thresh = 2.5  # Tolerance (in standard deviations)
for col in ['outputMpR (float64)[1]', 'outputMpZ (float64)[1]']:
    mean = df[col].mean()
    std = df[col].std()
    df = df[np.abs(df[col] - mean) < z_thresh * std]

# Extract time (if available)
time = df['#timeI (float64)[1]'].values * 1e3 if '#timeI (float64)[1]' in df.columns else np.arange(len(df))
time_min, time_max = time.min(), time.max()

# === 3. Compute voltage differences ===
df['deltaR'] = df['langmuir_outer (float64)[1]'] - df['langmuir_inner (float64)[1]']
df['deltaZ'] = df['langmuir_top (float64)[1]'] - df['langmuir_bottom (float64)[1]']

# === 4. Prepare input (X) and output (y) ===
X_R = df[['deltaR']]
y_R = df['outputMpR (float64)[1]']

X_Z = df[['deltaZ']]
y_Z = df['outputMpZ (float64)[1]']

# === 5. Fit robust linear models with HuberRegressor ===
model_R = HuberRegressor(epsilon=1.35).fit(X_R.values.reshape(-1, 1), y_R.values)
model_Z = HuberRegressor(epsilon=1.35).fit(X_Z.values.reshape(-1, 1), y_Z.values)

# === 6. Coefficients ===
C1, C2 = model_R.coef_[0], model_R.intercept_
C3, C4 = model_Z.coef_[0], model_Z.intercept_

print(f'\nR_p = {C1:.5f} * (V_outer - V_inner) + {C2:.5f}')
print(f'Z_p = {C3:.5f} * (V_top - V_bottom) + {C4:.5f}\n')

# === 7. Predictions and metrics ===
y_R_pred = model_R.predict(X_R.values.reshape(-1, 1))
y_Z_pred = model_Z.predict(X_Z.values.reshape(-1, 1))

rmse_R = np.sqrt(mean_squared_error(y_R, y_R_pred))
r2_R = r2_score(y_R, y_R_pred)

rmse_Z = np.sqrt(mean_squared_error(y_Z, y_Z_pred))
r2_Z = r2_score(y_Z, y_Z_pred)

print(f'\nRadial RMSE: {rmse_R:.5f}, R²: {r2_R:.5f}')
print(f'Vertical RMSE: {rmse_Z:.5f}, R²: {r2_Z:.5f}\n')

# === 8. Plot with PyQtGraph ===
win = pg.GraphicsLayoutWidget(title="Langmuir vs Mirnov Position Estimation")
win.resize(1000, 600)
win.showMaximized()
win.keyPressEvent = lambda event: app.quit() if event.key() == QtCore.Qt.Key_Escape else None

# Radial plot
p1 = win.addPlot(title="Radial Position Comparison")
curve1 = p1.plot(time, y_R.values, pen='b', name='Mirnov Coils')
curve2 = p1.plot(time, y_R_pred, pen=pg.mkPen('g', style=pg.QtCore.Qt.DashLine), name='Langmuir Probes')
legend1 = pg.LegendItem(offset=(60, 10))
legend1.setParentItem(p1.graphicsItem())
legend1.addItem(curve1, 'Mirnov Coils')
legend1.addItem(curve2, 'Langmuir Probes')
p1.setLabel('left', 'Radial Position')
p1.setLabel('bottom', 'Time (ms)')
p1.setXRange(time_min, time_max, padding=0)
p1.setLimits(xMin=time_min, xMax=time_max)
p1.setYRange(0.46-0.1, 0.46+0.1)
zero_lineR_center = pg.InfiniteLine(pos=0.46, angle=0, pen=pg.mkPen('w', width=1, style=QtCore.Qt.DashLine))
zero_lineR_upper = pg.InfiniteLine(pos=0.46+0.085, angle=0, pen=pg.mkPen('r', width=2, style=QtCore.Qt.DotLine))
zero_lineR_lower = pg.InfiniteLine(pos=0.46-0.085, angle=0, pen=pg.mkPen('r', width=2, style=QtCore.Qt.DotLine))
p1.addItem(zero_lineR_center)
p1.addItem(zero_lineR_upper)
p1.addItem(zero_lineR_lower)

# Vertical plot
win.nextRow()
p2 = win.addPlot(title="Vertical Position Comparison")
curve3 = p2.plot(time, y_Z.values, pen='b', name='Mirnov Coils')
curve4 = p2.plot(time, y_Z_pred, pen=pg.mkPen('g', style=pg.QtCore.Qt.DashLine), name='Langmuir Probes')
legend2 = pg.LegendItem(offset=(60, 10))
legend2.setParentItem(p2.graphicsItem())
legend2.addItem(curve3, 'Mirnov Coils')
legend2.addItem(curve4, 'Langmuir Probes')
p2.setLabel('left', 'Vertical Position')
p2.setLabel('bottom', 'Time (ms)')
p2.setXRange(time_min, time_max, padding=0)
p2.setLimits(xMin=time_min, xMax=time_max)
p2.setYRange(-0.1, 0.1)
zero_lineZ_center = pg.InfiniteLine(pos=0, angle=0, pen=pg.mkPen('w', width=1, style=QtCore.Qt.DashLine))
zero_lineZ_upper = pg.InfiniteLine(pos=0.085, angle=0, pen=pg.mkPen('r', width=2, style=QtCore.Qt.DotLine))
zero_lineZ_lower = pg.InfiniteLine(pos=-0.085, angle=0, pen=pg.mkPen('r', width=2, style=QtCore.Qt.DotLine))
p2.addItem(zero_lineZ_center)
p2.addItem(zero_lineZ_upper)
p2.addItem(zero_lineZ_lower)

output_file = '/home/felipe/git-repos/MARTe2-WaterTank/DataVisualization/Outputs/langmuir_coeficients.csv'

shot_name = os.path.basename(file_path)
shot_number = ''.join(filter(str.isdigit, os.path.splitext(shot_name)[0]))

row_data = {
    'Shot': shot_number,
    'C1': f"{C1:.16e}",
    'C2': f"{C2:.16e}",
    'C3': f"{C3:.16e}",
    'C4': f"{C4:.16e}",
    'RMSE_R': f"{rmse_R:.6e}",
    'R2_R': f"{r2_R:.6f}",
    'RMSE_Z': f"{rmse_Z:.6e}",
    'R2_Z': f"{r2_Z:.6f}"
}

# Update or create coefficients file
if os.path.exists(output_file):
    df_log = pd.read_csv(output_file)
    # Remove old entries for the same shot
    df_log['Shot'] = df_log['Shot'].astype(str)
    df_log = df_log[df_log['Shot'] != str(shot_number)]

    # Add new entry
    df_log = pd.concat([df_log, pd.DataFrame([row_data])], ignore_index=True)
else:
    df_log = pd.DataFrame([row_data])

# Save updated file
df_log.to_csv(output_file, index=False)

print(f"\nExported coefficients to: {output_file}\n")

if __name__ == '__main__':
    QtWidgets.QApplication.instance().exec_()

#!/usr/bin/env python3
"""
This script loads a CSV file containing Langmuir probe data and Mirnov coil position estimates.
It applies physical constraints, visualizes the positions, and fits robust regressions (HuberRegressor)
to estimate plasma positions from Langmuir voltages.
UPDATED: Adds interactive time-range selection (via a slider) before applying regression.
"""

import pandas as pd
import numpy as np
from sklearn.linear_model import HuberRegressor
from sklearn.metrics import mean_squared_error, r2_score
from pyqtgraph.Qt import QtWidgets, QtCore, QtGui
import pyqtgraph as pg
import sys
import os

# === Initialize PyQt App ===
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

# Remove outliers based on physical constraints
a = 0.085
R_center = 0.46
R_lower, R_upper = R_center - a, R_center + a
Z_center = 0.0
Z_lower, Z_upper = Z_center - a, Z_center + a

before_count = len(df)
df = df[
    (df['outputMpR (float64)[1]'] >= R_lower) & (df['outputMpR (float64)[1]'] <= R_upper) &
    (df['outputMpZ (float64)[1]'] >= Z_lower) & (df['outputMpZ (float64)[1]'] <= Z_upper)
]
after_count = len(df)
print(f"[INFO] Removed {before_count - after_count} rows outside physical limits.")

# Extract time (if available)
time = df['#timeI (float64)[1]'].values * 1e3 if '#timeI (float64)[1]' in df.columns else np.arange(len(df))
time_min, time_max = time.min(), time.max()

# === 3. Compute voltage differences ===
df['deltaR'] = df['langmuir_outer (float64)[1]'] - df['langmuir_inner (float64)[1]']
df['deltaZ'] = df['langmuir_top (float64)[1]'] - df['langmuir_bottom (float64)[1]']

# === Prepare window layout ===
main_window = QtWidgets.QWidget()
layout = QtWidgets.QVBoxLayout(main_window)

# === Graphics layout for plots ===
plots_widget = pg.GraphicsLayoutWidget(title="Langmuir vs Mirnov Position Estimation")
plots_widget.resize(1000, 600)
plots_widget.show()
plots_widget.keyPressEvent = lambda event: app.quit() if event.key() == QtCore.Qt.Key_Escape else None

# === Add to main layout ===
layout.addWidget(plots_widget)

# === Plot 1: Radial Position ===
plot_r = plots_widget.addPlot(title="Radial Position Comparison")
plot_r.setLabel('bottom', 'Time [ms]')
plot_r.setLabel('left', 'R [m]')
plot_r.setXRange(time_min, time_max, padding=0)
plot_r.setLimits(xMin=time_min, xMax=time_max)
plot_r.setYRange(0.46 - 0.1, 0.46 + 0.1)

# Physical constraint lines
plot_r.addItem(pg.InfiniteLine(pos=0.46, angle=0, pen=pg.mkPen('w', width=1, style=QtCore.Qt.DashLine)))
plot_r.addItem(pg.InfiniteLine(pos=0.46 + 0.085, angle=0, pen=pg.mkPen('r', width=2, style=QtCore.Qt.DotLine)))
plot_r.addItem(pg.InfiniteLine(pos=0.46 - 0.085, angle=0, pen=pg.mkPen('r', width=2, style=QtCore.Qt.DotLine)))

# === Plot 2: Vertical Position ===
plots_widget.nextRow()
plot_z = plots_widget.addPlot(title="Vertical Position Comparison")
plot_z.setLabel('bottom', 'Time [ms]')
plot_z.setLabel('left', 'Z [m]')
plot_z.setXRange(time_min, time_max, padding=0)
plot_z.setLimits(xMin=time_min, xMax=time_max)
plot_z.setYRange(-0.1, 0.1)

plot_z.addItem(pg.InfiniteLine(pos=0, angle=0, pen=pg.mkPen('w', width=1, style=QtCore.Qt.DashLine)))
plot_z.addItem(pg.InfiniteLine(pos=0.085, angle=0, pen=pg.mkPen('r', width=2, style=QtCore.Qt.DotLine)))
plot_z.addItem(pg.InfiniteLine(pos=-0.085, angle=0, pen=pg.mkPen('r', width=2, style=QtCore.Qt.DotLine)))

# === Add curves for original data (Mirnov) ===
curve_r_data = plot_r.plot(time, df['outputMpR (float64)[1]'].values, pen=pg.mkPen('c', width=2), name='Mirnov Coils')
curve_r_fit = plot_r.plot([], [], pen=pg.mkPen('y', width=2, style=QtCore.Qt.DashLine), name='Langmuir Fit')

curve_z_data = plot_z.plot(time, df['outputMpZ (float64)[1]'].values, pen=pg.mkPen('m', width=2), name='Mirnov Coils')
curve_z_fit = plot_z.plot([], [], pen=pg.mkPen('g', width=2, style=QtCore.Qt.DashLine), name='Langmuir Fit')

# Add LinearRegionItem for selecting time range
region = pg.LinearRegionItem([time_min + 100, time_max - 100])
region.setZValue(10)
plot_r.addItem(region)

# === Button to apply regression after range selection ===
apply_button = QtWidgets.QPushButton("Apply Regression for Selected Range")
layout.addWidget(apply_button)

# === Function to compute regression and update plots ===
def apply_regression():
    # Get selected time interval
    bounds = region.getRegion()
    mask = (time >= bounds[0]) & (time <= bounds[1])

    # Extract data within selection
    X_R_sel = df['deltaR'].values[mask].reshape(-1, 1)
    y_R_sel = df['outputMpR (float64)[1]'].values[mask]
    X_Z_sel = df['deltaZ'].values[mask].reshape(-1, 1)
    y_Z_sel = df['outputMpZ (float64)[1]'].values[mask]

    # Fit robust regressors
    model_R = HuberRegressor(epsilon=1.3).fit(X_R_sel, y_R_sel)
    model_Z = HuberRegressor(epsilon=1.3).fit(X_Z_sel, y_Z_sel)

    # Predict values in selected range
    y_R_pred_sel = model_R.predict(X_R_sel)
    y_Z_pred_sel = model_Z.predict(X_Z_sel)

    # Update fit curves
    curve_r_fit.setData(time[mask], y_R_pred_sel)
    curve_z_fit.setData(time[mask], y_Z_pred_sel)

    # Print coefficients and metrics
    C1, C2 = model_R.coef_[0], model_R.intercept_
    C3, C4 = model_Z.coef_[0], model_Z.intercept_

    rmse_R = np.sqrt(mean_squared_error(y_R_sel, y_R_pred_sel))
    r2_R = r2_score(y_R_sel, y_R_pred_sel)

    rmse_Z = np.sqrt(mean_squared_error(y_Z_sel, y_Z_pred_sel))
    r2_Z = r2_score(y_Z_sel, y_Z_pred_sel)

    print(f"\n=== Regression Results for Selected Range ===")
    print(f'R_p = {C1:.5f} * (V_outer - V_inner) + {C2:.5f}')
    print(f'Z_p = {C3:.5f} * (V_top - V_bottom) + {C4:.5f}')
    print(f'Radial RMSE: {rmse_R:.5f}, R²: {r2_R:.5f}')
    print(f'Vertical RMSE: {rmse_Z:.5f}, R²: {r2_Z:.5f}\n')

    # === Save Coefficients ===
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


# Connect button click to function
apply_button.clicked.connect(apply_regression)

# Show main window
main_window.showMaximized()
main_window.keyPressEvent = lambda event: app.quit() if event.key() == QtCore.Qt.Key_Escape else None

if __name__ == '__main__':
    QtWidgets.QApplication.instance().exec_()

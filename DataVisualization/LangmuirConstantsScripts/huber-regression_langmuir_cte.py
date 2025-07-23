import pandas as pd
import numpy as np
from sklearn.linear_model import HuberRegressor
from sklearn.metrics import mean_squared_error, r2_score
from pyqtgraph.Qt import QtWidgets, QtCore, QtGui
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
    
# Remove outliers based on physical constraints

a = 0.085
R_center = 0.46
R_lower, R_upper = R_center - a, R_center + a

Z_center = 0.0
Z_lower, Z_upper = Z_center - a, Z_center + a

# === Apply filtering based on z-threshold derived from physical constraints ===
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

# === 4. Prepare input (X) and output (y) ===
X_R = df[['deltaR']]
y_R = df['outputMpR (float64)[1]']

X_Z = df[['deltaZ']]
y_Z = df['outputMpZ (float64)[1]']

# === 5. Fit robust linear models with HuberRegressor (NO alpha) ===
model_R = HuberRegressor(epsilon=1.3).fit(X_R.values.reshape(-1, 1), y_R.values)
model_Z = HuberRegressor(epsilon=1.3).fit(X_Z.values.reshape(-1, 1), y_Z.values)

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

# === Plot 1: Radial ===
plot_r = win.addPlot(title="Radial Position Comparison")
plot_r.setLabel('bottom', 'Time [ms]')
plot_r.setLabel('left', 'R [m]')
plot_r.setXRange(time_min, time_max, padding=0)
plot_r.setLimits(xMin=time_min, xMax=time_max)
plot_r.setYRange(0.46-0.1, 0.46+0.1)

zero_lineR_center = pg.InfiniteLine(pos=0.46, angle=0, pen=pg.mkPen('w', width=1, style=QtCore.Qt.DashLine))
zero_lineR_upper = pg.InfiniteLine(pos=0.46+0.085, angle=0, pen=pg.mkPen('r', width=2, style=QtCore.Qt.DotLine))
zero_lineR_lower = pg.InfiniteLine(pos=0.46-0.085, angle=0, pen=pg.mkPen('r', width=2, style=QtCore.Qt.DotLine))
plot_r.addItem(zero_lineR_center)
plot_r.addItem(zero_lineR_upper)
plot_r.addItem(zero_lineR_lower)

curves_r = [
    (plot_r.plot(time, y_R.values, pen=pg.mkPen('c', width=2), name='Mirnov Coils'), "Mirnov Coils"),
    (plot_r.plot(time, y_R_pred, pen=pg.mkPen('y', width=2, style=QtCore.Qt.DashLine), name='Langmuir Probes'), "Langmuir Fit")
]

# === Plot 2: Vertical ===
win.nextRow()
plot_z = win.addPlot(title="Vertical Position Comparison")
plot_z.setLabel('bottom', 'Time [ms]')
plot_z.setLabel('left', 'Z [m]')
plot_z.setXRange(time_min, time_max, padding=0)
plot_z.setLimits(xMin=time_min, xMax=time_max)
plot_z.setYRange(-0.1, 0.1)

zero_lineZ_center = pg.InfiniteLine(pos=0, angle=0, pen=pg.mkPen('w', width=1, style=QtCore.Qt.DashLine))
zero_lineZ_upper = pg.InfiniteLine(pos=0.085, angle=0, pen=pg.mkPen('r', width=2, style=QtCore.Qt.DotLine))
zero_lineZ_lower = pg.InfiniteLine(pos=-0.085, angle=0, pen=pg.mkPen('r', width=2, style=QtCore.Qt.DotLine))
plot_z.addItem(zero_lineZ_center)
plot_z.addItem(zero_lineZ_upper)
plot_z.addItem(zero_lineZ_lower)

curves_z = [
    (plot_z.plot(time, y_Z.values, pen=pg.mkPen('m', width=2), name='Mirnov Coils'), "Mirnov Coils"),
    (plot_z.plot(time, y_Z_pred, pen=pg.mkPen('g', width=2, style=QtCore.Qt.DashLine), name='Langmuir Probes'), "Langmuir Fit")
]

# === Custom Legends ===
custom_legend_items = []
x_offset = 100
y_offset = 30
spacing = 150
legend_font = QtGui.QFont("Arial", 10)

for i, (curve, label) in enumerate(curves_r):
    sample = pg.graphicsItems.LegendItem.ItemSample(curve)
    sample.setParentItem(plot_r.graphicsItem())
    legend_x = x_offset + i * spacing
    sample.setPos(legend_x, y_offset)
    custom_legend_items.append(sample)

    text = pg.TextItem(label, anchor=(0, 0), color='w')
    text.setFont(legend_font)
    text.setParentItem(plot_r.graphicsItem())
    text.setPos(legend_x + 25, y_offset)
    custom_legend_items.append(text)

for i, (curve, label) in enumerate(curves_z):
    sample = pg.graphicsItems.LegendItem.ItemSample(curve)
    sample.setParentItem(plot_z.graphicsItem())
    legend_x = x_offset + i * spacing
    sample.setPos(legend_x, y_offset)
    custom_legend_items.append(sample)

    text = pg.TextItem(label, anchor=(0, 0), color='w')
    text.setFont(legend_font)
    text.setParentItem(plot_z.graphicsItem())
    text.setPos(legend_x + 25, y_offset)
    custom_legend_items.append(text)

# === Link X-axis and Sync Y ===
plot_r.setXLink(plot_z)
def sync_y_range(source_plot, target_plot, offset):
    if not target_plot.vb:
        return
    source_ymin, source_ymax = source_plot.vb.viewRange()[1]
    source_center = (source_ymin + source_ymax) / 2
    source_size = source_ymax - source_ymin
    target_center = source_center + offset
    new_target_range = (
        target_center - source_size / 2,
        target_center + source_size / 2
    )
    target_plot.vb.blockSignals(True)
    target_plot.vb.setYRange(*new_target_range, padding=0)
    target_plot.vb.blockSignals(False)

r_center = (plot_r.vb.viewRange()[1][0] + plot_r.vb.viewRange()[1][1]) / 2
z_center = (plot_z.vb.viewRange()[1][0] + plot_z.vb.viewRange()[1][1]) / 2
offset_r_to_z = z_center - r_center
offset_z_to_r = r_center - z_center

plot_r.vb.sigYRangeChanged.connect(lambda: sync_y_range(plot_r, plot_z, offset_r_to_z))
plot_z.vb.sigYRangeChanged.connect(lambda: sync_y_range(plot_z, plot_r, offset_z_to_r))

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

if __name__ == '__main__':
    QtWidgets.QApplication.instance().exec_()

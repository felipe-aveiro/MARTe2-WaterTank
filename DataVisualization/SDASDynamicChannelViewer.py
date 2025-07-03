import sys
import numpy as np
from pyqtgraph.Qt import QtWidgets, QtCore
import pyqtgraph as pg
from sdas.core.client.SDASClient import SDASClient

HOST = 'baco.ipfn.tecnico.ulisboa.pt'
PORT = 8888
DEFAULT_SHOT = 46241
START_CHANNEL = 228  # initial channel -> Rogowski channel
MAX_CHANNEL = 254
MIN_CHANNEL = 0

class SDASPlotter(QtWidgets.QMainWindow):
    def __init__(self):
        self.shot_number = DEFAULT_SHOT
        super().__init__()
        self.client = SDASClient(HOST, PORT)
        self.channel_number = START_CHANNEL

        self.setWindowTitle("SDAS Dynamic Channel Viewer")
        self.setGeometry(100, 100, 1000, 600)

        self.central_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QtWidgets.QVBoxLayout(self.central_widget)

        # Plot area
        self.plot_widget = pg.PlotWidget(title="SDAS Channel Data")
        self.plot_widget.setLabel('left', 'Signal')
        self.plot_widget.setLabel('bottom', 'Time (ms)')
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_widget.setXRange(100, 400, padding=0)
        self.plot_widget.setLimits(xMin=0, xMax=500)
        self.layout.addWidget(self.plot_widget)

        # Button row
        self.button_layout = QtWidgets.QHBoxLayout()
        self.layout.addLayout(self.button_layout)

        self.prev_button = QtWidgets.QPushButton("← Previous Channel")
        self.prev_button.clicked.connect(self.load_previous_channel)
        self.button_layout.addWidget(self.prev_button)

        self.next_button = QtWidgets.QPushButton("Next Channel →")
        self.next_button.clicked.connect(self.load_next_channel)
        self.button_layout.addWidget(self.next_button)

        # Input field to type channel
        self.channel_input = QtWidgets.QLineEdit()
        self.channel_input.setPlaceholderText("Enter channel number (0–254)")
        self.channel_input.setFixedWidth(250)
        self.channel_input.returnPressed.connect(self.go_to_channel)
        self.button_layout.addWidget(self.channel_input)

        # Input field to type shot
        self.shot_input = QtWidgets.QLineEdit()
        self.shot_input.setPlaceholderText("Enter shot number")
        self.shot_input.setFixedWidth(250)
        self.shot_input.returnPressed.connect(self.go_to_shot)
        self.button_layout.addWidget(self.shot_input)

        # Status label
        self.status_label = QtWidgets.QLabel("Ready.")
        self.layout.addWidget(self.status_label)

        # Initial plot
        self.load_and_plot_channel(self.channel_number)

    def load_and_plot_channel(self, channel_number):
        channel_id = f"MARTE_NODE_IVO3.DataCollection.Channel_{channel_number:03d}"
        try:
            self.status_label.setText(f"Loading {channel_id}...")
            QtWidgets.QApplication.processEvents()

            data_struct = self.client.getData(channel_id, '0x0000', self.shot_number)
            if not data_struct or len(data_struct[0].getData()) == 0:
                self.status_label.setText(f"No data in {channel_id}.")
                return

            signal = np.array(data_struct[0].getData())
            tstart = data_struct[0].getTStart()
            tend = data_struct[0].getTEnd()
            total_time_us = tend.getTimeInMicros() - tstart.getTimeInMicros()
            time_vector = np.linspace(0, total_time_us, len(signal)) * 1e-3  # ms

            self.plot_widget.clear()
            zero_line = pg.InfiniteLine(pos=0, angle=0, pen=pg.mkPen('w', width=1, style=QtCore.Qt.DashLine))
            self.plot_widget.addItem(zero_line)
            self.plot_widget.plot(time_vector, signal, pen=pg.mkPen('green', width=2))
            self.plot_widget.setTitle(f"Channel: {channel_id}")
            self.status_label.setText(f"Loaded {channel_id} with {len(signal)} points.")

            self.channel_number = channel_number  # Update current channel

        except Exception as e:
            self.status_label.setText(f"Error loading {channel_id}: {e}")

    def load_next_channel(self):
        if self.channel_number >= MAX_CHANNEL:
            self.status_label.setText(f"Reached Channel_{MAX_CHANNEL:03d} — no further channels available.")
            self.next_button.setEnabled(False)
            return
        self.channel_number += 1
        self.load_and_plot_channel(self.channel_number)
        self.next_button.setEnabled(self.channel_number < MAX_CHANNEL)

    def load_previous_channel(self):
        if self.channel_number > MIN_CHANNEL:
            self.channel_number -= 1
            self.load_and_plot_channel(self.channel_number)
            if not self.next_button.isEnabled() and self.channel_number < MAX_CHANNEL:
                self.next_button.setEnabled(True)
        else:
            self.status_label.setText("Already at Channel_{MIN_CHANNEL:03d} — cannot go back further.")

    def go_to_channel(self):
        text = self.channel_input.text().strip()
        if not text.isdigit():
            self.status_label.setText("Invalid input: please enter a valid integer for channel.")
            return

        entered = int(text)
        if MIN_CHANNEL <= entered <= MAX_CHANNEL:
            self.load_and_plot_channel(entered)
            self.channel_input.clear()
        else:
            self.status_label.setText(f"Invalid channel: must be between {MIN_CHANNEL} and {MAX_CHANNEL}.")

    def go_to_shot(self):
        text = self.shot_input.text().strip()
        if not text.isdigit():
            self.status_label.setText("Invalid input: please enter a valid integer for shot.")
            return

        entered = int(text)
        if entered <= 0:
            self.status_label.setText("Invalid shot number: must be positive.")
            return

        test_channel_id = f"MARTE_NODE_IVO3.DataCollection.Channel_{self.channel_number:03d}"
        try:
            test_data = self.client.getData(test_channel_id, '0x0000', entered)
            if not test_data or len(test_data[0].getData()) == 0:
                self.status_label.setText(f"Shot {entered} exists, but has no data in current channel.")
                self.plot_widget.clear()
                return

            self.shot_number = entered
            self.status_label.setText(f"Shot set to {self.shot_number}. Updating plot...")
            QtWidgets.QApplication.processEvents()
            self.load_and_plot_channel(self.channel_number)
            self.shot_input.clear()

        except Exception as e:
            self.status_label.setText(f"Error accessing shot {entered}: {e}")




if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = SDASPlotter()
    window.showMaximized()
    window.keyPressEvent = lambda event: app.quit() if event.key() == QtCore.Qt.Key_Escape else None
    sys.exit(app.exec_())

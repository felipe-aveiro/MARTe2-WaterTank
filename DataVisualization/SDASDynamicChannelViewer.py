import sys
import os
import numpy as np
from pyqtgraph.Qt import QtWidgets, QtCore
import pyqtgraph as pg
from sdas.core.client.SDASClient import SDASClient

HOST = 'baco.ipfn.tecnico.ulisboa.pt'
PORT = 8888
DEFAULT_SHOT = 46241
START_CHANNEL = 49  # initial channel -> Rogowski channel
MAX_CHANNEL = 254
MIN_CHANNEL = 0


class SDASPlotter(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        self.shot_number = DEFAULT_SHOT
        self.client = SDASClient(HOST, PORT)
        self.channel_number = START_CHANNEL

        # Cache: uniqueID -> name and name_query -> list of matches
        self.uid_to_name_cache = {}
        self.name_to_uid_cache = {}

        # Last plotted data (for saving)
        self.last_time_ms = None
        self.last_signal = None
        self.last_channel_id = None
        self.last_param_name = None

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

        self.save_button = QtWidgets.QToolButton()
        self.save_button.setToolTip("Save current channel data")
        self.save_button.setIcon(self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_DialogSaveButton))
        self.save_button.clicked.connect(self.save_current_plot_data)
        self.button_layout.addWidget(self.save_button)
        
        # Input field to type channel
        self.channel_input = QtWidgets.QLineEdit()
        self.channel_input.setPlaceholderText("Enter channel number (0–254)")
        self.channel_input.setFixedWidth(220)
        self.channel_input.returnPressed.connect(self.go_to_channel)
        self.button_layout.addWidget(self.channel_input)

        # Input field to type shot
        self.shot_input = QtWidgets.QLineEdit()
        self.shot_input.setPlaceholderText("Enter shot number")
        self.shot_input.setFixedWidth(220)
        self.shot_input.returnPressed.connect(self.go_to_shot)
        self.button_layout.addWidget(self.shot_input)

        # Input field to search parameter name
        self.name_input = QtWidgets.QLineEdit()
        self.name_input.setPlaceholderText("Search parameter name (e.g., 'vertical', 'rogowski'...)")
        self.name_input.setFixedWidth(320)
        self.name_input.returnPressed.connect(self.search_by_name)
        self.button_layout.addWidget(self.name_input)

        # Status label
        self.status_label = QtWidgets.QLabel("Ready.")
        self.layout.addWidget(self.status_label)

        # Initial plot
        self.load_and_plot_channel(self.channel_number)

    def channel_id_from_number(self, channel_number: int) -> str:
        return f"MARTE_NODE_IVO3.DataCollection.Channel_{channel_number:03d}"

    def resolve_parameter_name(self, unique_id: str) -> str:
        """
        Returns the parameter name (descriptorUID.name) for a given uniqueID.
        """
        if unique_id in self.uid_to_name_cache:
            return self.uid_to_name_cache[unique_id]

        name = "Unknown (not found in descriptor DB)"
        try:
            results = self.client.searchParametersByUniqueID(unique_id)
            if results and len(results) > 0:
                name = results[0].get('descriptorUID', {}).get('name', name)
        except Exception:
            pass

        self.uid_to_name_cache[unique_id] = name
        return name

    def search_uniqueids_by_name(self, name_query: str, limit: int = 10):
        if name_query in self.name_to_uid_cache:
            return self.name_to_uid_cache[name_query]

        matches = []
        try:
            results = self.client.searchParametersByName(name_query)
            for p in (results or [])[:limit]:
                d = p.get('descriptorUID', {})
                matches.append((d.get('name', ''), d.get('uniqueID', '')))
        except Exception:
            pass

        self.name_to_uid_cache[name_query] = matches
        return matches

    def extract_channel_number_from_uniqueid(self, unique_id: str):
        """
        If uniqueID matches "...DataCollection.Channel_XXX", returns int(XXX). Otherwise None.
        """
        marker = ".DataCollection.Channel_"
        if marker not in unique_id:
            return None
        try:
            suffix = unique_id.split(marker, 1)[1]
            return int(suffix)
        except Exception:
            return None

    def load_and_plot_channel(self, channel_number: int):
        channel_id = self.channel_id_from_number(channel_number)

        try:
            resolved_name = self.resolve_parameter_name(channel_id)

            self.status_label.setText(f"Loading {channel_id} | {resolved_name} (shot {self.shot_number})...")
            QtWidgets.QApplication.processEvents()

            data_struct = self.client.getData(channel_id, '0x0000', self.shot_number)
            if not data_struct or len(data_struct[0].getData()) == 0:
                self.plot_widget.clear()
                self.plot_widget.setTitle(f"{channel_id} | {resolved_name} | Shot {self.shot_number}")
                self.status_label.setText(f"No data in {channel_id} | {resolved_name} (shot {self.shot_number}).")
                self.last_time_ms = None
                self.last_signal = None
                self.last_channel_id = channel_id
                self.last_param_name = resolved_name
                return

            signal = np.array(data_struct[0].getData())
            tstart = data_struct[0].getTStart()
            tend = data_struct[0].getTEnd()
            total_time_us = tend.getTimeInMicros() - tstart.getTimeInMicros()
            time_vector = np.linspace(0, total_time_us, len(signal)) * 1e-3  # ms
            
            # Store last plotted data for saving
            self.last_time_ms = time_vector
            self.last_signal = signal
            self.last_channel_id = channel_id
            self.last_param_name = resolved_name

            self.plot_widget.clear()
            zero_line = pg.InfiniteLine(
                pos=0,
                angle=0,
                pen=pg.mkPen('w', width=1, style=QtCore.Qt.DashLine)
            )
            self.plot_widget.addItem(zero_line)

            self.plot_widget.plot(time_vector, signal, pen=pg.mkPen('green', width=2))
            self.plot_widget.setTitle(f"{channel_id} | {resolved_name} | shot {self.shot_number}")
            self.status_label.setText(
                f"Loaded {channel_id} | {resolved_name} | shot {self.shot_number} | {len(signal)} points."
            )

            self.channel_number = channel_number

        except Exception as e:
            resolved_name = self.resolve_parameter_name(channel_id)
            self.status_label.setText(f"Error loading {channel_id} | {resolved_name}: {e}")

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
            self.status_label.setText(f"Already at Channel_{MIN_CHANNEL:03d} — cannot go back further.")

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

        test_channel_id = self.channel_id_from_number(self.channel_number)
        try:
            test_data = self.client.getData(test_channel_id, '0x0000', entered)
            if not test_data or len(test_data[0].getData()) == 0:
                resolved_name = self.resolve_parameter_name(test_channel_id)
                self.status_label.setText(
                    f"Shot {entered} exists, but has no data in {test_channel_id} | {resolved_name}."
                )
                self.plot_widget.clear()
                return

            self.shot_number = entered
            self.status_label.setText(f"Shot set to {self.shot_number}. Updating plot...")
            QtWidgets.QApplication.processEvents()
            self.load_and_plot_channel(self.channel_number)
            self.shot_input.clear()

        except Exception as e:
            self.status_label.setText(f"Error accessing shot {entered}: {e}")

    def show_search_results_dialog(self, matches):
        """
        Shows a modal dialog with a selectable list of (name, uniqueID) matches.
        Returns the selected uniqueID (str) or None.
        """
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("SDAS Search Results")
        dialog.setModal(True)
        dialog.resize(900, 450)

        layout = QtWidgets.QVBoxLayout(dialog)

        info = QtWidgets.QLabel("Select one item to load. Double-click also loads.")
        layout.addWidget(info)

        list_widget = QtWidgets.QListWidget()
        list_widget.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        list_widget.setUniformItemSizes(True)
        layout.addWidget(list_widget)

        # Populate list
        for (name, uid) in matches:
            ch_num = self.extract_channel_number_from_uniqueid(uid)
            if ch_num is not None:
                text = f"[Channel_{ch_num:03d}] {name}    |    {uid}"
            else:
                text = f"[N/A] {name}    |    {uid}"

            item = QtWidgets.QListWidgetItem(text)
            item.setData(QtCore.Qt.UserRole, uid)

            # Grey out items that are not Channel_XXX (still shown, but not loadable)
            if ch_num is None:
                item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEnabled)
            list_widget.addItem(item)

        # Buttons
        btn_row = QtWidgets.QHBoxLayout()
        layout.addLayout(btn_row)

        load_btn = QtWidgets.QPushButton("Load Selected")
        cancel_btn = QtWidgets.QPushButton("Cancel")
        btn_row.addStretch(1)
        btn_row.addWidget(load_btn)
        btn_row.addWidget(cancel_btn)

        def accept_selected():
            item = list_widget.currentItem()
            if item is None:
                QtWidgets.QMessageBox.warning(dialog, "No selection", "Select an item first.")
                return
            dialog.selected_uid = item.data(QtCore.Qt.UserRole)
            dialog.accept()

        load_btn.clicked.connect(accept_selected)
        cancel_btn.clicked.connect(dialog.reject)
        list_widget.itemDoubleClicked.connect(lambda _: accept_selected())

        dialog.selected_uid = None
        dialog.exec_()
        return dialog.selected_uid

    
    def search_by_name(self):
        query = self.name_input.text().strip()
        if not query:
            self.status_label.setText("Type a name fragment to search (e.g., 'vertical').")
            return

        matches = self.search_uniqueids_by_name(query, limit=50)
        if not matches:
            self.status_label.setText(f"No parameter matches found for '{query}'.")
            return

        selected_uid = self.show_search_results_dialog(matches)
        if not selected_uid:
            self.status_label.setText("Search cancelled.")
            return

        ch_num = self.extract_channel_number_from_uniqueid(selected_uid)
        if ch_num is None:
            self.status_label.setText(f"Selected item is not a Channel_XXX: {selected_uid}")
            return

        if not (MIN_CHANNEL <= ch_num <= MAX_CHANNEL):
            self.status_label.setText(f"Selected Channel_{ch_num:03d} is outside [0..254].")
            return

        self.load_and_plot_channel(ch_num)
        self.name_input.clear()

    """
    def make_signal_header(self, channel_id: str, param_name: str) -> str:
        ""
        Returns a CSV-friendly header like: 'MARTE...Channel_049 | ADC_horizontal_current'
        ""
        name = (param_name or "Unknown").strip()
        # Keep it friendly for CSV/Excel: remove tabs/newlines
        name = name.replace("\t", " ").replace("\n", " ").replace("\r", " ")
        return f"{channel_id} | {name}"
    """
    
    def make_marte_headers(self, channel_id: str, param_name: str):
        """
        Returns MARTe-like headers compatible with the data reader.
        """
        dtype = "float64"  # SDAS getData returns Python floats; keep it float64 for compatibility
        time_col = f"#timeI ({dtype})[1]"

        name = (param_name or "Unknown").strip()
        name = name.replace("\t", " ").replace("\n", " ").replace("\r", " ")

        # Keeps reader compatible AND keeps the ID visible:
        # ID comes after the name using a safe separator.
        # Example: "rogowski_ch__MARTE_NODE_IVO3.DataCollection.Channel_049 (float64)[1]"
        safe_id = channel_id.replace(" ", "_")
        signal_col = f"{name}__{safe_id} ({dtype})[1]"
        return time_col, signal_col

    def sanitize_filename(self, text: str) -> str:
        """
        Makes a string safe for filenames.
        """
        if text is None:
            return "unknown"
        allowed = []
        for ch in text:
            if ch.isalnum() or ch in ("-", "_", "."):
                allowed.append(ch)
            else:
                allowed.append("_")
        return "".join(allowed).strip("_")


    def save_current_plot_data(self):
        """
        Saves the currently plotted data to a tab-delimited text file:
        two columns [time_ms, signal].
        Naming style similar to the base code: "<shot>.<channel_id>.csv" (tab-separated).
        """
        if self.last_time_ms is None or self.last_signal is None or self.last_channel_id is None:
            QtWidgets.QMessageBox.warning(self, "Nothing to save", "No plotted data available to save.")
            return

        shot = self.shot_number
        channel_id = self.last_channel_id
        param_name = self.last_param_name or "Unknown"

        # Default filename similar to the base code
        # Using .csv extension but tab-separated, like your base script.
        safe_param = self.sanitize_filename(param_name)
        default_name = f"{shot}.{channel_id}.{safe_param}.csv"

        # Ask user where to save
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Save channel data",
            default_name,
            "CSV (*.csv);;All files (*)"
        )

        if not path:
            self.status_label.setText("Save cancelled.")
            return

        try:
            time_col, signal_col = self.make_marte_headers(channel_id, param_name)
            data_out = np.column_stack((self.last_time_ms * 1e-3, self.last_signal))
            header_line = f"{time_col},{signal_col}"
            np.savetxt(path, data_out, delimiter=",", header=header_line, comments="")

            self.status_label.setText(f"Saved: {os.path.basename(path)}  ({len(self.last_signal)} points)")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Save failed", f"Could not save file:\n{e}")
            self.status_label.setText(f"Save failed: {e}")


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = SDASPlotter()
    window.showMaximized()
    window.keyPressEvent = lambda event: app.quit() if event.key() == QtCore.Qt.Key_Escape else None
    sys.exit(app.exec_())

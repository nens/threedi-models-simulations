import csv
import json
import os
import tempfile

import numpy as np
from qgis.core import Qgis, QgsMessageLog
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QDoubleValidator
from qgis.PyQt.QtWidgets import (
    QAction,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QMenu,
    QPushButton,
    QRadioButton,
    QSizePolicy,
    QSpacerItem,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from threedi_models_simulations.communication import UICommunication
from threedi_models_simulations.utils.general import (
    IntDelegate,
    ScientificDoubleDelegate,
    get_download_file,
)
from threedi_models_simulations.utils.msgpack import loadb
from threedi_models_simulations.utils.threedi_api import (
    fetch_3di_model_initial_concentrations,
    fetch_model_initial_concentrations_download,
    fetch_model_initial_waterlevels,
    fetch_model_initial_waterlevels_download,
)
from threedi_models_simulations.widgets.new_simulation_wizard_pages.utils.duplicate_node_dialog import (
    DuplicateNodeDialog,
)
from threedi_models_simulations.widgets.new_simulation_wizard_pages.wizard_page import (
    WizardPage,
)


class InitialConditions1DPage(WizardPage):
    def __init__(self, parent, new_sim, threedi_api, communication):
        super().__init__(parent, show_steps=True)
        self.setTitle("Initial conditions 1D")
        self.setSubTitle(
            r'Bla <a href="https://docs.3di.live/i_running_a_simulation.html#starting-a-simulation/">documentation</a>.'
        )
        self.new_sim = new_sim
        self.threedi_api = threedi_api
        self.communication = communication
        main_widget = self.get_page_widget()
        self.first_load = True

        layout = QGridLayout()
        main_widget.setLayout(layout)

        self.constant_value_cb = QCheckBox("Global value", main_widget)
        self.constant_value_cb.toggled.connect(self.constant_checked)
        self.constant_value_le = QLineEdit(main_widget)
        double_validator = QDoubleValidator(0, 100000000, 3, main_widget)
        self.constant_value_le.setValidator(double_validator)
        constant_label_lb = QLabel("Label", main_widget)
        self.constant_label_le = QLineEdit(main_widget)
        layout.addWidget(self.constant_value_cb, 0, 0)
        layout.addWidget(self.constant_value_le, 0, 1)
        layout.addWidget(constant_label_lb, 0, 2)
        layout.addWidget(self.constant_label_le, 0, 3)

        self.online_value_cb = QCheckBox("Select online file", main_widget)
        self.online_value_cb.toggled.connect(self.online_checked)
        self.online_value_cob = QComboBox(main_widget)
        self.online_value_cob.activated.connect(self.online_file_changed)

        layout.addWidget(self.online_value_cb, 1, 0)
        layout.addWidget(self.online_value_cob, 1, 1, 1, 3)

        self.table = QTableWidget(main_widget)
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Node ID", "Value", "Label"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.ExtendedSelection)
        self.table.customContextMenuRequested.connect(self.menu_requested_level)
        self.table.cellChanged.connect(self.cell_changed)
        float_delegate = ScientificDoubleDelegate(self.table, bottom=0.0, decimals=2)
        int_delegate = IntDelegate(self.table, bottom=0)
        self.table.setItemDelegateForColumn(1, float_delegate)
        self.table.setItemDelegateForColumn(0, int_delegate)
        self.table.setEnabled(True)
        layout.addWidget(self.table, 2, 0, 4, 4)

        add_node_row_pb = QPushButton("+ Add node", main_widget)
        add_node_from_file_pb = QPushButton("+ Add from local file", main_widget)
        add_node_row_pb.clicked.connect(self.add_node)
        add_node_from_file_pb.clicked.connect(self.add_node_from_file)
        layout.addWidget(add_node_row_pb, 6, 2)
        layout.addWidget(add_node_from_file_pb, 6, 3)

        self.substance_table = QTableWidget(main_widget)
        self.substance_table.setColumnCount(1)
        self.substance_table.setHorizontalHeaderLabels(["Node ID"])
        self.substance_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.substance_table, 7, 0, 4, 4)

        self.add_substance_row_pb = QPushButton("+ Add concentration", main_widget)
        self.add_substance_from_file_pb = QPushButton(
            "+ Add from local file", main_widget
        )
        layout.addWidget(self.add_substance_row_pb, 11, 2)
        layout.addWidget(self.add_substance_from_file_pb, 11, 3)

        vertical_spacer = QSpacerItem(
            20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding
        )

        layout.addItem(vertical_spacer, 12, 0)

        # Already fetch some data
        initial_waterlevels = fetch_model_initial_waterlevels(
            self.threedi_api, self.new_sim.simulation.threedimodel_id
        )
        self.initial_waterlevels_1d = [
            iw for iw in initial_waterlevels if (iw.dimension == "one_d" and iw.file)
        ]

        initial_concentrations = fetch_3di_model_initial_concentrations(
            self.threedi_api, self.new_sim.simulation.threedimodel_id
        )
        self.initial_concentrations_1d = [
            ic for ic in initial_concentrations if (ic.dimension == "one_d" and ic.file)
        ]
        if self.initial_concentrations_1d:
            self.load_online_concentration_in_table(self.initial_concentrations_1d[0])

    def load_model(self):
        if self.first_load:
            # Constant
            if self.new_sim.initial_1d_water_level:
                self.constant_value_cb.setChecked(True)
                self.constant_value_le.setText(
                    str(self.new_sim.initial_1d_water_level.value)
                )
            else:
                self.constant_value_cb.setChecked(False)
                self.constant_value_le.clear()

            # File
            self.online_value_cb.setChecked(False)
            self.online_value_cob.clear()
            for level in self.initial_waterlevels_1d:
                self.online_value_cob.addItem(
                    str(level.id) + ":" + level.file.filename, level
                )

            if not self.initial_waterlevels_1d:
                self.online_value_cb.setEnabled(False)

            for level in self.initial_waterlevels_1d:
                if (
                    level.id
                    == self.new_sim.initial_1d_water_level_file.initial_waterlevel_id
                ):
                    self.online_value_cb.setChecked(True)
                    self.online_value_cob.setCurrentText(
                        str(level.id) + ":" + level.file.filename
                    )
                    break

        # Update substances table
        substance_names = [substance.name for substance in self.new_sim.substances]
        if substance_names:
            # TODO: take into account new substances (possible addition and removal)
            self.substance_table.setColumnCount(1 + len(substance_names))
            self.substance_table.setHorizontalHeaderLabels(
                ["Node ID"] + substance_names
            )
            self.substance_table.setVisible(True)
        else:
            self.substance_table.setVisible(False)

        self.first_load = False

    def menu_requested_level(self, pos):
        index = self.table.indexAt(pos)
        menu = QMenu(self)
        action_stop = QAction("Delete", self)
        action_stop.triggered.connect(lambda _, sel_index=index: self.delete())
        menu.addAction(action_stop)
        menu.popup(self.table.viewport().mapToGlobal(pos))

    def constant_checked(self, toggled):
        if not toggled:
            self.constant_value_le.clear()
            self.constant_label_le.clear()
            self.constant_value_le.setEnabled(False)
            self.constant_label_le.setEnabled(False)
        else:
            self.constant_value_le.setEnabled(True)
            self.constant_label_le.setEnabled(True)

    def online_checked(self, toggled):
        if not toggled:
            self.online_value_cob.clear()
            self.online_value_cob.setEnabled(False)
        else:
            self.online_value_cob.setEnabled(True)
            self.online_value_cob.clear()
            for level in self.initial_waterlevels_1d:
                self.online_value_cob.addItem(
                    str(level.id) + ":" + level.file.filename, level
                )

            # Set it to the right initial values
            for level in self.initial_waterlevels_1d:
                if (
                    level.id
                    == self.new_sim.initial_1d_water_level_file.initial_waterlevel_id
                ):
                    self.online_value_cob.setCurrentText(
                        str(level.id) + ":" + level.file.filename
                    )

                    # Retrieve the data and add the values
                    if self.table.rowCount() != 0:
                        if UICommunication.ask(
                            self,
                            "Online file changed",
                            "Selecting another online waterlevel instance will clear the table, continue?",
                        ):
                            self.table.setRowCount(0)
                            self.load_online_waterlevel_in_table(level)
                        else:
                            self.online_value_cb.setChecked(False)
                    else:
                        self.load_online_waterlevel_in_table(level)
                    break

    def load_online_waterlevel_in_table(self, level):
        download = fetch_model_initial_waterlevels_download(
            self.threedi_api,
            level.id,
            self.new_sim.simulation.threedimodel_id,
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, str(level.id) + ":" + level.file.filename)
            get_download_file(download, file_path)
            with open(file_path, "rb") as data_file:
                byte_data = data_file.read()
                result = loadb(byte_data)
                data = np.column_stack((result["node_ids"], result["value"]))
                for pair in data:
                    row_position = self.table.rowCount()
                    self.table.blockSignals(True)
                    self.table.insertRow(row_position)
                    self.table.setItem(
                        row_position, 0, QTableWidgetItem(str(int(pair[0])))
                    )
                    self.table.setItem(row_position, 1, QTableWidgetItem(str(pair[1])))
                    self.table.blockSignals(False)

            # Retrieve possible labels, a substance is a label when
            # - The unit is percent
            # - The concentration lasts for the whole forcing
            # - Concentration is always 100%

    def load_online_concentration_in_table(self, conc):
        download = fetch_model_initial_concentrations_download(
            self.threedi_api,
            conc.id,
            self.new_sim.simulation.threedimodel_id,
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, str(conc.id) + ":" + conc.file.filename)
            get_download_file(download, file_path)
            with open(file_path, "rb") as data_file:
                data_str = data_file.read().decode("utf-8")
                result = json.loads(data_str)
                data = np.column_stack((result["node_ids"], result["values"]))
                QgsMessageLog.logMessage(str(data))

    def online_file_changed(self, idx):
        if self.table.rowCount() != 0:
            if UICommunication.ask(
                self,
                "Online file changed",
                "Selecting another online waterlevel instance will clear the table, continue?",
            ):
                self.table.setRowCount(0)
                current_level = self.online_value_cob.currentData()
                self.load_online_waterlevel_in_table(current_level)

    def cell_changed(self, row, column):
        # When entered, check for duplicates
        if column == 0:
            node_id_str = self.table.item(row, column).text()
            if node_id_str:
                node_id = int(self.table.item(row, 0).text())
                for check_row in range(self.table.rowCount()):
                    if check_row != row:
                        if int(self.table.item(check_row, 0).text()) == node_id:
                            self.communication.show_warn(
                                f"Node {node_id} already present at row {check_row + 1}.",
                                self,
                                "Warning",
                            )
                            self.table.blockSignals(True)
                            self.table.item(row, 0).setText("")
                            self.table.blockSignals(False)
                            return

    def add_node(self):
        row = self.table.rowCount()
        self.table.insertRow(row)
        item = QTableWidgetItem("")
        self.table.setItem(row, 0, item)
        self.table.setItem(row, 1, QTableWidgetItem(""))
        self.table.scrollToItem(item, QTableWidget.PositionAtBottom)

    def add_node_from_file(self):
        # First retrieve the current values from the table
        try:
            current_node_ids, current_values = self._retrieve_current_nodes()
        except Exception as e:
            self.communication.show_warn(str(e), self, "Warning")
            return

        file_name, __ = QFileDialog.getOpenFileName(
            self,
            "Open 1D initial waterlevel file",
            "",
            "Comma-separated values (*.csv *.txt)",
        )

        new_node_ids = []
        new_values = []

        # load the csv
        with open(file_name, encoding="utf-8-sig") as csvfile:
            reader = csv.DictReader(csvfile)
            header = reader.fieldnames
            if not header:
                self.communication.show_warn("CSV file is empty!", self, "Warning")
                return
            if "id" not in header:
                self.communication.show_warn(
                    "Missing 'id' column in CSV file!", self, "Warning"
                )
                return
            if "value" not in header:
                self.communication.show_warn(
                    "Missing 'value' column in CSV file!", self, "Warning"
                )
                return

            waterlevels_list = list(reader)

            for row in waterlevels_list:
                node_id_str = row.get("id").strip()
                value_str = row.get("value").strip()
                if not node_id_str or not value_str:
                    self.communication.show_warn(
                        "Missing values in CSV file. Please remove these lines or fill in a value and try again.",
                        self,
                        "Warning",
                    )
                    return
                try:
                    node_id = int(node_id_str)
                    value = float(value_str)
                    new_node_ids.append(node_id)
                    new_values.append(value)
                except ValueError:
                    self.communication.show_warn(
                        f"Invalid data format in CSV: id='{node_id_str}', value='{value_str}'",
                        self,
                        "Warning",
                    )
                    return

        # Show duplicate node dialog with new data and currently loaded data
        d_dialog = DuplicateNodeDialog(
            current_node_ids, current_values, new_node_ids, new_values, self
        )
        last_added_item = None
        if d_dialog.exec() == QDialog.DialogCode.Accepted:
            self.table.blockSignals(True)
            # Replace values that have to be overwritten
            overwrite_data = d_dialog.get_overwrite_data()
            for id, value in overwrite_data:
                for row in range(self.table.rowCount()):
                    node_id = int(self.table.item(row, 0).text())
                    if node_id == id:
                        self.table.item(row, 1).setText(str(value))

            # Append new values in UI,
            new_data = d_dialog.get_new_data()

            for pair in new_data:
                row_position = self.table.rowCount()
                self.table.insertRow(row_position)
                self.table.setItem(row_position, 0, QTableWidgetItem(str(int(pair[0]))))
                last_added_item = QTableWidgetItem(str(float(pair[1])))
                self.table.setItem(row_position, 1, last_added_item)
            self.table.blockSignals(False)

            if last_added_item:
                self.table.scrollToItem(last_added_item, QTableWidget.PositionAtBottom)

    def _retrieve_current_nodes(self):
        current_node_ids = []
        current_values = []

        for row in range(self.table.rowCount()):
            node_id_str = self.table.item(row, 0).text()
            if not node_id_str:
                raise Exception(f"Node at row {row + 1} not properly set.")
            node_id = int(node_id_str)
            value_str = self.table.item(row, 1).text()
            if not value_str:
                raise Exception(f"Value at row {row + 1} not properly set.")
            value = float(value_str)
            current_node_ids.append(node_id)
            current_values.append(value)

        return current_node_ids, current_values

    def delete(self):
        selected_rows = list(set(index.row() for index in self.table.selectedIndexes()))
        selected_rows.sort(reverse=True)
        for row in selected_rows:
            self.table.removeRow(row)

    def save_model(self):
        # store model
        # dont forget to store waterlevel ids etc if required
        return True

    def validate_page(self):
        return self.is_complete()

    def is_complete(self):
        # validate level

        # validate concentration
        # does node exist, value ok

        return True

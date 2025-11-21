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
from threedi_api_client.openapi import OneDWaterLevel, OneDWaterLevelFile

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

        layout = QGridLayout()
        main_widget.setLayout(layout)

        self.no_value_rb = QRadioButton("No initial 1D water level", main_widget)
        layout.addWidget(self.no_value_rb, 0, 0)

        self.constant_value_rb = QRadioButton("Global value", main_widget)
        self.constant_value_rb.toggled.connect(self.constant_checked)
        self.constant_value_le = QLineEdit(main_widget)
        self.constant_value_le.setEnabled(False)
        self.constant_value_le.textEdited.connect(self.completeChanged)
        double_validator = QDoubleValidator(0, 100000000, 3, main_widget)
        self.constant_value_le.setValidator(double_validator)
        constant_label_lb = QLabel("Label", main_widget)
        self.constant_label_le = QLineEdit(main_widget)
        self.constant_label_le.setEnabled(False)
        layout.addWidget(self.constant_value_rb, 1, 0)
        layout.addWidget(self.constant_value_le, 1, 1)
        layout.addWidget(constant_label_lb, 1, 2)
        layout.addWidget(self.constant_label_le, 1, 3)

        self.table_value_rb = QRadioButton("Define 1D waterlevel in table", main_widget)
        self.table_value_rb.toggled.connect(self.table_checked)

        layout.addWidget(self.table_value_rb, 2, 0)

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
        self.table.setEnabled(False)
        layout.addWidget(self.table, 3, 0, 4, 4)

        self.add_node_row_pb = QPushButton("+ Add node", main_widget)
        self.add_node_from_file_pb = QPushButton("+ Add from local file", main_widget)
        self.add_node_from_online_file_pb = QPushButton(
            "+ Add from online file", main_widget
        )
        self.add_node_row_pb.clicked.connect(self.add_node)
        self.add_node_from_file_pb.clicked.connect(self.add_node_from_file)
        self.add_node_from_online_file_pb.clicked.connect(
            self.add_node_from_online_file
        )
        self.add_node_row_pb.setEnabled(False)
        self.add_node_from_file_pb.setEnabled(False)
        self.add_node_from_online_file_pb.setEnabled(False)
        layout.addWidget(self.add_node_row_pb, 7, 1)
        layout.addWidget(self.add_node_from_file_pb, 7, 2)
        layout.addWidget(self.add_node_from_online_file_pb, 7, 3)

        self.substance_table = QTableWidget(main_widget)
        self.substance_table.setColumnCount(1)
        self.substance_table.setHorizontalHeaderLabels(["Node ID"])
        self.substance_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.substance_table, 8, 0, 4, 4)

        self.add_substance_row_pb = QPushButton("+ Add concentration", main_widget)
        self.add_substance_from_file_pb = QPushButton(
            "+ Add from local file", main_widget
        )
        layout.addWidget(self.add_substance_row_pb, 12, 2)
        layout.addWidget(self.add_substance_from_file_pb, 12, 3)

        vertical_spacer = QSpacerItem(
            20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding
        )

        layout.addItem(vertical_spacer, 13, 0)

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
        # Constant
        if self.new_sim.initial_1d_water_level:
            self.constant_value_rb.setChecked(True)
            self.constant_value_le.setText(
                str(self.new_sim.initial_1d_water_level.value)
            )
        elif self.new_sim.initial_1d_water_level_data:
            self.table.setRowCount(0)
            for node, value in self.new_sim.initial_1d_water_level_data.items():
                row_position = self.table.rowCount()
                self.table.blockSignals(True)
                self.table.insertRow(row_position)
                self.table.setItem(row_position, 0, QTableWidgetItem(str(int(node))))
                self.table.setItem(row_position, 1, QTableWidgetItem(str(value)))
                self.table.blockSignals(False)
            self.table_value_rb.setChecked(True)
        elif self.new_sim.initial_1d_water_level_file:
            self.table.setRowCount(0)
            for level in self.initial_waterlevels_1d:
                if (
                    level.id
                    == self.new_sim.initial_1d_water_level_file.initial_waterlevel_id
                ):
                    # Retrieve from online file
                    self.load_online_waterlevel_in_table(level)
                    self.table_value_rb.setChecked(True)
                    break
        else:
            # Nothing
            self.no_value_rb.setChecked(True)

        # Update substances table (TODO)
        substance_names = [substance.name for substance in self.new_sim.substances]
        if substance_names:
            # TODO: take into account new substances (possible addition and removal?)
            self.substance_table.setColumnCount(1 + len(substance_names))
            self.substance_table.setHorizontalHeaderLabels(
                ["Node ID"] + substance_names
            )
            self.substance_table.setVisible(True)
            self.add_substance_from_file_pb.setVisible(True)
            self.add_substance_row_pb.setVisible(True)
        else:
            self.substance_table.setVisible(False)
            self.add_substance_from_file_pb.setVisible(False)
            self.add_substance_row_pb.setVisible(False)

    def menu_requested_level(self, pos):
        index = self.table.indexAt(pos)
        menu = QMenu(self)
        action_stop = QAction("Delete", self)
        action_stop.triggered.connect(lambda _, sel_index=index: self.delete())
        menu.addAction(action_stop)
        menu.popup(self.table.viewport().mapToGlobal(pos))

    def table_checked(self, toggled):
        if not toggled:
            self.table.setEnabled(False)
            self.add_node_row_pb.setEnabled(False)
            self.add_node_from_file_pb.setEnabled(False)
            self.add_node_from_online_file_pb.setEnabled(False)
            self.table.setRowCount(0)
        else:
            self.table.setEnabled(True)
            self.add_node_row_pb.setEnabled(True)
            self.add_node_from_file_pb.setEnabled(True)
            self.add_node_from_online_file_pb.setEnabled(True)

        self.completeChanged.emit()

    def constant_checked(self, toggled):
        if not toggled:
            self.constant_value_le.clear()
            self.constant_label_le.clear()
            self.constant_value_le.setEnabled(False)
            self.constant_label_le.setEnabled(False)
        else:
            self.constant_value_le.setEnabled(True)
            self.constant_label_le.setEnabled(True)

        self.completeChanged.emit()

    def load_online_waterlevel_in_table(self, level):
        data = self.fetch_level_data_from_api(level)
        for pair in data:
            row_position = self.table.rowCount()
            self.table.blockSignals(True)
            self.table.insertRow(row_position)
            self.table.setItem(row_position, 0, QTableWidgetItem(str(int(pair[0]))))
            self.table.setItem(row_position, 1, QTableWidgetItem(str(pair[1])))
            self.table.blockSignals(False)

            # Retrieve possible labels, a substance is a label when
            # - The unit is percent
            # - The concentration lasts for the whole forcing
            # - Concentration is always 100%

        self.completeChanged.emit()

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
                            break

        self.completeChanged.emit()

    def add_node(self):
        row = self.table.rowCount()
        self.table.insertRow(row)
        item = QTableWidgetItem("")
        self.table.setItem(row, 0, item)
        self.table.setItem(row, 1, QTableWidgetItem(""))
        self.table.scrollToItem(item, QTableWidget.PositionAtBottom)
        self.completeChanged.emit()

    def add_node_from_online_file(self):
        # Create dialog and download file
        online_file_dialog = QDialog(self)

        online_file_dialog.setWindowTitle("Select online file")
        dialog_layout = QGridLayout(online_file_dialog)
        online_file_dialog.setLayout(dialog_layout)

        online_file_cb = QComboBox(online_file_dialog)
        dialog_layout.addWidget(online_file_cb, 0, 0, 1, 3)

        for level in self.initial_waterlevels_1d:
            online_file_cb.addItem(str(level.id) + ":" + level.file.filename, level)
        cancel_pb = QPushButton("Cancel", self)
        ok_pb = QPushButton("Ok", self)
        cancel_pb.clicked.connect(online_file_dialog.reject)
        ok_pb.clicked.connect(online_file_dialog.accept)
        dialog_layout.addWidget(cancel_pb, 1, 0)
        dialog_layout.addWidget(ok_pb, 1, 2)

        if online_file_dialog.exec() == QDialog.DialogCode.Accepted:
            # Download data
            data = self.fetch_level_data_from_api(online_file_cb.currentData())
            new_node_ids = []
            new_values = []
            for pair in data:
                new_node_ids.append(int(pair[0]))
                new_values.append(float(pair[1]))

            # Retrieve the current nodes
            try:
                current_node_ids, current_values = self._retrieve_current_nodes()
            except Exception as e:
                self.communication.show_warn(str(e), self, "Warning")
                return

            # Show duplicate node dialog with new data and currently loaded data
            d_dialog = DuplicateNodeDialog(
                current_node_ids, current_values, new_node_ids, new_values, self
            )
            if d_dialog.exec() == QDialog.DialogCode.Accepted:
                last_added_item = None
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
                    self.table.setItem(
                        row_position, 0, QTableWidgetItem(str(int(pair[0])))
                    )
                    last_added_item = QTableWidgetItem(str(float(pair[1])))
                    self.table.setItem(row_position, 1, last_added_item)
                self.table.blockSignals(False)

                if last_added_item:
                    self.table.scrollToItem(
                        last_added_item, QTableWidget.PositionAtBottom
                    )

                self.completeChanged.emit()

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
        if not file_name:
            return

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

        if d_dialog.exec() == QDialog.DialogCode.Accepted:
            last_added_item = None
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

        self.completeChanged.emit()

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

        self.completeChanged.emit()

    def save_model(self):
        # constant
        if self.constant_value_rb.isChecked():
            value = float(self.constant_value_le.text())
            self.new_sim.initial_1d_water_level = OneDWaterLevel(value=value)
            self.new_sim.initial_1d_water_level_file = None
            self.new_sim.initial_1d_water_level_data = None
        elif self.table_value_rb.isChecked():
            # first check whether an online file is used, we'll reuse that
            table_data = {}
            for row in range(self.table.rowCount()):
                node_id = int(self.table.item(row, 0).text())
                value = float(self.table.item(row, 1).text())
                table_data[node_id] = value

            for level in self.initial_waterlevels_1d:
                try:
                    # skips this file when not able to retrieve
                    data = self.fetch_level_data_from_api(level)
                except Exception:
                    continue

                file_data = {}
                for pair in data:
                    file_data[int(pair[0])] = float(pair[1])

                # if the data in the table is the same as the selected file, we only need to store the file reference
                # == operator takes order into account (same dicts with different order are equal)
                if table_data == file_data:
                    QgsMessageLog.logMessage(
                        f"1D water level {level.id} reused",
                        level=Qgis.Info,
                    )

                    # store the selected waterlevel
                    self.new_sim.initial_1d_water_level_file = OneDWaterLevelFile(
                        initial_waterlevel=level.url,
                        initial_waterlevel_id=level.id,
                    )
                    self.new_sim.initial_1d_water_level_data = None
                    self.new_sim.initial_1d_water_level = None
                    return True

            # Otherwise we store the table itself as well, a new waterlevel file needs to be created
            self.new_sim.initial_1d_water_level_file = None
            self.new_sim.initial_1d_water_level_data = dict(table_data)
            # Remove constant data
            self.new_sim.initial_1d_water_level = None
        else:
            self.new_sim.initial_1d_water_level_file = None
            self.new_sim.initial_1d_water_level_data = None
            self.new_sim.initial_1d_water_level = None

        return True

    def fetch_level_data_from_api(self, current_level):
        download = fetch_model_initial_waterlevels_download(
            self.threedi_api,
            current_level.id,
            self.new_sim.simulation.threedimodel_id,
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(
                tmpdir, str(current_level.id) + ":" + current_level.file.filename
            )
            get_download_file(download, file_path)
            with open(file_path, "rb") as data_file:
                byte_data = data_file.read()
                result = loadb(byte_data)
                data = np.column_stack((result["node_ids"], result["value"]))
                return data

    def validate_page(self):
        return self.is_complete()

    def is_complete(self):
        # Validate constant level
        if self.constant_value_rb.isChecked():
            if not self.constant_value_le.text():
                QgsMessageLog.logMessage("No constant value entered")
                return False

        # Does node already exist?
        if self.table_value_rb.isChecked():
            try:
                node_ids, values = self._retrieve_current_nodes()
                if len(set(node_ids)) != len(node_ids):
                    QgsMessageLog.logMessage("Duplicates")
                    return False
            except Exception as e:
                QgsMessageLog.logMessage(str(e))
                return False

        # Validate concentration (TODO)

        return True

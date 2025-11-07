import csv
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

from threedi_models_simulations.utils.general import get_download_file
from threedi_models_simulations.utils.msgpack import loadb
from threedi_models_simulations.utils.threedi_api import (
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

        layout.addWidget(self.online_value_cb, 1, 0)
        layout.addWidget(self.online_value_cob, 1, 1, 1, 3)

        self.table = QTableWidget(main_widget)
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Node ID", "Value", "Label"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.customContextMenuRequested.connect(self.menu_requested_level)
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

        add_substance_row_pb = QPushButton("+ Add concentration", main_widget)
        add_substance_from_file_pb = QPushButton("+ Add from local file", main_widget)
        layout.addWidget(add_substance_row_pb, 11, 2)
        layout.addWidget(add_substance_from_file_pb, 11, 3)

        vertical_spacer = QSpacerItem(
            20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding
        )

        layout.addItem(vertical_spacer, 7, 0)

        # Already fetch some data
        initial_waterlevels = fetch_model_initial_waterlevels(
            self.threedi_api, self.new_sim.simulation.threedimodel_id
        )
        self.initial_waterlevels_1d = [
            iw for iw in initial_waterlevels if iw.dimension == "one_d"
        ]

    def initializePage(self):
        # Constant
        if self.new_sim.initial_1d_water_level:
            self.constant_checked(True)
            self.constant_value_le.setText(
                str(self.new_sim.initial_1d_water_level.value)
            )
        else:
            self.constant_checked(False)
            self.constant_value_le.clear()

        # File
        self.online_value_cb.setChecked(False)
        self.online_value_cob.clear()
        for level in self.initial_waterlevels_1d:
            self.online_value_cob.addItem(
                str(level.id) + ":" + level.file.filename, level
            )

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

        # Substances
        substance_names = [substance.name for substance in self.new_sim.substances]
        self.substance_table.setColumnCount(1 + len(substance_names))
        self.substance_table.setHorizontalHeaderLabels(["Node ID"] + substance_names)

    def menu_requested_level(self, pos):
        index = self.table.indexAt(pos)
        menu = QMenu(self)
        action_stop = QAction("Delete", self)
        action_stop.triggered.connect(lambda _, sel_index=index: self.delete(sel_index))
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
            # TODO: Remove the values, if required
            self.online_value_cob.clear()
            self.online_value_cob.setEnabled(False)
        else:
            self.online_value_cob.setEnabled(True)
            for level in self.initial_waterlevels_1d:
                self.online_value_cob.addItem(
                    str(level.id) + ":" + level.file.filename, level
                )

            for level in self.initial_waterlevels_1d:
                if (
                    level.id
                    == self.new_sim.initial_1d_water_level_file.initial_waterlevel_id
                ):
                    self.online_value_cob.setCurrentText(
                        str(level.id) + ":" + level.file.filename
                    )
                    break

            # Retrieve the data and add the values
            # TODO: caching
            download = fetch_model_initial_waterlevels_download(
                self.threedi_api,
                self.new_sim.initial_1d_water_level_file.initial_waterlevel_id,
                self.new_sim.simulation.threedimodel_id,
            )
            with tempfile.TemporaryDirectory() as tmpdir:
                file_path = os.path.join(
                    tmpdir, str(level.id) + ":" + level.file.filename
                )
                get_download_file(download, file_path)
                with open(file_path, "rb") as data_file:
                    byte_data = data_file.read()
                    result = loadb(byte_data)
                    data = np.column_stack((result["node_ids"], result["value"]))
                    for pair in data:
                        row_position = self.table.rowCount()
                        self.table.insertRow(row_position)
                        self.table.setItem(
                            row_position, 0, QTableWidgetItem(str(int(pair[0])))
                        )
                        self.table.setItem(
                            row_position, 1, QTableWidgetItem(str(pair[1]))
                        )

    def add_node(self):
        row = self.table.rowCount()
        self.table.insertRow(row)
        item = QTableWidgetItem("")
        self.table.setItem(row, 0, item)
        self.table.setItem(row, 1, QTableWidgetItem(""))
        self.table.scrollToItem(item, QTableWidget.PositionAtBottom)

    def add_node_from_file(self):
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
        current_node_ids, current_values = self._retrieve_current_nodes()
        d_dialog = DuplicateNodeDialog(
            current_node_ids, current_values, new_node_ids, new_values, self
        )
        last_added_item = None
        if d_dialog.exec() == QDialog.DialogCode.Accepted:
            # Append new values in UI
            new_data = d_dialog.get_new_data()
            for pair in new_data:
                row_position = self.table.rowCount()
                self.table.insertRow(row_position)
                self.table.setItem(row_position, 0, QTableWidgetItem(str(int(pair[0]))))
                last_added_item = QTableWidgetItem(str(float(pair[1])))
                self.table.setItem(row_position, 1, last_added_item)
        if last_added_item:
            self.table.scrollToItem(last_added_item, QTableWidget.PositionAtBottom)

    def _retrieve_current_nodes(self):
        current_node_ids = []
        current_values = []

        for row in range(self.table.rowCount()):
            node_id = int(self.table.item(row, 0).text())
            value = float(self.table.item(row, 1).text())
            current_node_ids.append(node_id)
            current_values.append(value)

        return current_node_ids, current_values

    def delete(self, idx):
        pass

    def validatePage(self):
        # store model
        return True

    def isComplete(self):
        # validate
        return True

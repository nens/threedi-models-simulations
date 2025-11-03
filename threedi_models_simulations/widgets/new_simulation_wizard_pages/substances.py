from qgis.core import Qgis, QgsMessageLog
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (
    QAction,
    QCheckBox,
    QGridLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QMenu,
    QPushButton,
    QRadioButton,
    QSizePolicy,
    QSpacerItem,
    QTableView,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)
from threedi_api_client.openapi import Substance

from threedi_models_simulations.utils.general import ScientificDoubleDelegate
from threedi_models_simulations.widgets.new_simulation_wizard_pages.wizard_page import (
    WizardPage,
)


class SubstancesPage(WizardPage):
    NAME_IDX = 0
    UNIT_IDX = 1
    DECAY_IDX = 2
    DIFFUSION_IDX = 3

    def __init__(self, parent, new_sim, communication):
        super().__init__(parent, show_steps=True)
        self.setTitle("Substances")
        self.setSubTitle(
            r"Define the substances for in your simulation here. The concentrations wil be determined in the following steps."
        )
        self.new_sim = new_sim
        self.communication = communication
        # We need the following flag because Qt calls IsComplete twice (in QWizard and QWizardPage completeChanged() is connected
        # to two functions that both call isComplete())
        self._show_warnings = False
        main_widget = self.get_page_widget()

        layout = QGridLayout()
        main_widget.setLayout(layout)

        self.substance_table = QTableWidget(main_widget)
        self.substance_table.setColumnCount(4)
        self.substance_table.setHorizontalHeaderLabels(
            ["Name", "Units", "Decay coefficient", "Diffusion coefficient"]
        )
        self.substance_table.horizontalHeader().setStretchLastSection(True)
        self.substance_table.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        self.substance_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.substance_table.setSelectionMode(QTableWidget.SingleSelection)
        self.substance_table.customContextMenuRequested.connect(self.menu_requested)

        delegate = ScientificDoubleDelegate(self.substance_table, decimals=2)
        self.substance_table.setItemDelegateForColumn(2, delegate)
        self.substance_table.setItemDelegateForColumn(3, delegate)
        self.substance_table.itemChanged.connect(self.changed)  # Can fire twice
        self.substance_table.model().rowsInserted.connect(self.changed)
        self.substance_table.model().rowsRemoved.connect(self.changed)

        layout.addWidget(self.substance_table, 0, 0, 1, 4)

        add_substance = QPushButton("+ Add substance", main_widget)
        layout.addWidget(add_substance, 1, 3, 1, 1)
        add_substance.clicked.connect(self.add_substance)

        vertical_spacer = QSpacerItem(
            20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding
        )
        layout.addItem(vertical_spacer, 2, 0)

    def add_substance(self):
        self.substance_table.insertRow(self.substance_table.rowCount())

    def delete_substance(self, idx):
        self.substance_table.removeRow(idx.row())

    def menu_requested(self, pos):
        index = self.substance_table.indexAt(pos)
        menu = QMenu(self)
        action_stop = QAction("Delete", self)
        action_stop.triggered.connect(
            lambda _, sel_index=index: self.delete_substance(sel_index)
        )
        menu.addAction(action_stop)
        menu.popup(self.substance_table.viewport().mapToGlobal(pos))

    def changed(self):
        self._show_warnings = (
            True  # Reset the show UI flag. (Qt calls IsComplete() twice)
        )
        self.completeChanged.emit()

    def initializePage(self):
        self.substance_table.clearContents()
        self.substance_table.setColumnCount(4)
        self.substance_table.setRowCount(0)

        # Fill the page with the current model
        for substance in self.new_sim.substances:
            row_position = self.substance_table.rowCount()
            self.substance_table.insertRow(row_position)
            self.substance_table.setItem(
                row_position, self.NAME_IDX, QTableWidgetItem(substance.name)
            )
            self.substance_table.setItem(
                row_position, self.UNIT_IDX, QTableWidgetItem(substance.units)
            )
            self.substance_table.setItem(
                row_position,
                self.DECAY_IDX,
                QTableWidgetItem(str(substance.decay_coefficient)),
            )
            self.substance_table.setItem(
                row_position,
                self.DIFFUSION_IDX,
                QTableWidgetItem(str(substance.diffusion_coefficient)),
            )

    def validatePage(self):
        # Here we update the model, we already know everything is valid (otherwise the next button would not be enabled)
        self.new_sim.substances.clear()
        for row in range(self.substance_table.rowCount()):
            s = Substance(
                name=self.substance_table.item(row, self.NAME_IDX).text(),
                units=self.substance_table.item(row, self.UNIT_IDX).text(),
                decay_coefficient=float(
                    self.substance_table.item(row, self.DECAY_IDX).text()
                ),
                diffusion_coefficient=float(
                    self.substance_table.item(row, self.DIFFUSION_IDX).text()
                ),
            )
            self.new_sim.substances.append(s)

        return True

    def isComplete(self):
        new_state = self.check(self._show_warnings)
        if self._show_warnings:
            self._show_warnings = False
        return new_state

    def check(self, update_ui: bool):
        for row in range(self.substance_table.rowCount()):
            name_item = self.substance_table.item(row, self.NAME_IDX)
            if not name_item or not name_item.text():
                return False

            decay_item = self.substance_table.item(row, self.DECAY_IDX)
            if not decay_item or not decay_item.text():
                return False
            diff_item = self.substance_table.item(row, self.DIFFUSION_IDX)
            if not diff_item or not diff_item.text():
                return False
            try:
                # Utilize the validation in the api client
                Substance(
                    name=self.substance_table.item(row, self.NAME_IDX).text(),
                    units=self.substance_table.item(row, self.UNIT_IDX).text(),
                    decay_coefficient=float(
                        self.substance_table.item(row, self.DECAY_IDX).text()
                    ),
                    diffusion_coefficient=float(
                        self.substance_table.item(row, self.DIFFUSION_IDX).text()
                    ),
                )
            except Exception as e:
                if update_ui:
                    self.communication.show_warn(str(e), self, "Warning")
                return False

        return True

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

from threedi_models_simulations.utils.general import ScientificDoubleDelegate
from threedi_models_simulations.widgets.new_simulation_wizard_pages.wizard_page import (
    WizardPage,
)


class SubstancesPage(WizardPage):
    def __init__(self, parent, new_sim):
        super().__init__(parent, show_steps=True)
        self.setTitle("Substances")
        self.setSubTitle(
            r"Define the substances for in your simulation here. The concentrations wil be determined in the following steps."
        )
        self.new_sim = new_sim

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
        self.substance_table.cellChanged.connect(self.completeChanged)
        self.substance_table.model().rowsInserted.connect(self.completeChanged)
        self.substance_table.model().rowsRemoved.connect(self.completeChanged)
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

    def initializePage(self):
        # Fill the page with the current model
        for substance in self.new_sim.substances:
            row_position = self.substance_table.rowCount()
            self.substance_table.insertRow(row_position)
            self.substance_table.setItem(
                row_position, 0, QTableWidgetItem(substance.name)
            )
            self.substance_table.setItem(
                row_position, 1, QTableWidgetItem(substance.units)
            )
            self.substance_table.setItem(
                row_position, 2, QTableWidgetItem(str(substance.decay_coefficient))
            )
            self.substance_table.setItem(
                row_position, 3, QTableWidgetItem(str(substance.diffusion_coefficient))
            )

    def validatePage(self):
        # when the user clicks Next or Finish to perform some last-minute validation. If it returns true, the next page is shown (or the wizard finishes); otherwise, the current page stays up.

        # Here we update the model
        return True

    def isComplete(self):
        # Check if we have incomplete rows
        for row in range(self.substance_table.rowCount()):
            QgsMessageLog.logMessage(str(row), level=Qgis.Critical)
            name_item = self.substance_table.item(row, 0)
            if not name_item or not name_item.text():
                return False
            decay_item = self.substance_table.item(row, 2)
            if not decay_item or not decay_item.text():
                return False
            diff_item = self.substance_table.item(row, 3)
            if not diff_item or not diff_item.text():
                return False
        return True

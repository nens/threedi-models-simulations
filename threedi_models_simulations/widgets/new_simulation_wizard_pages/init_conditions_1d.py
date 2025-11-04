from qgis.core import Qgis, QgsMessageLog
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QDoubleValidator
from qgis.PyQt.QtWidgets import (
    QAction,
    QCheckBox,
    QComboBox,
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
    QVBoxLayout,
)

from threedi_models_simulations.widgets.new_simulation_wizard_pages.wizard_page import (
    WizardPage,
)


class InitialConditions1DPage(WizardPage):
    def __init__(self, parent, new_sim):
        super().__init__(parent, show_steps=True)
        self.setTitle("Initial conditions 1D")
        self.setSubTitle(
            r'Bla <a href="https://docs.3di.live/i_running_a_simulation.html#starting-a-simulation/">documentation</a>.'
        )
        self.new_sim = new_sim

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
        self.online_value_cob = QComboBox(main_widget)

        layout.addWidget(self.online_value_cb, 1, 0)
        layout.addWidget(self.online_value_cob, 1, 1, 1, 3)

        self.table = QTableWidget(main_widget)
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["ID", "Value", "Label"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.customContextMenuRequested.connect(self.menu_requested)
        self.table.setEnabled(True)
        layout.addWidget(self.table, 2, 0, 4, 4)

        add_node_pb = QPushButton("+ Add node", main_widget)
        add_from_file_pb = QPushButton("+ Add from local file", main_widget)
        layout.addWidget(add_node_pb, 6, 2)
        layout.addWidget(add_from_file_pb, 6, 3)

        vertical_spacer = QSpacerItem(
            20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding
        )

        layout.addItem(vertical_spacer, 7, 0)

    def initializePage(self):
        QgsMessageLog.logMessage(str(self.new_sim), level=Qgis.Critical)
        if self.new_sim.initial_1d_water_level:
            self.constant_checked(True)
            self.constant_value_le.setText(
                str(self.new_sim.initial_1d_water_level.value)
            )
        else:
            self.constant_checked(False)
            self.constant_value_le.clear()

        # Retrieve possible 1d concentration files from API and fill combobox

    def menu_requested(self, pos):
        index = self.substance_table.indexAt(pos)
        menu = QMenu(self)
        action_stop = QAction("Delete", self)
        action_stop.triggered.connect(lambda _, sel_index=index: self.delete(sel_index))
        menu.addAction(action_stop)
        menu.popup(self.substance_table.viewport().mapToGlobal(pos))

    def constant_checked(self, toggled):
        if not toggled:
            self.constant_value_le.clear()
            self.constant_label_le.clear()
            self.constant_value_le.setEnabled(False)
            self.constant_label_le.setEnabled(False)
        else:
            self.constant_value_le.setEnabled(True)
            self.constant_label_le.setEnabled(True)

    def delete(idx):
        pass

    def validatePage(self):
        # store model
        return True

    def isComplete(self):
        # validate
        return True

from qgis.core import Qgis, QgsMessageLog
from qgis.PyQt.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGridLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QRadioButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
)

from threedi_models_simulations.widgets.new_simulation_wizard_pages.wizard_page import (
    WizardPage,
)


class InitialConditionsGroundWaterPage(WizardPage):
    def __init__(self, parent, new_sim):
        super().__init__(parent, show_steps=True)
        self.setTitle("Initial conditions groundwater")
        self.setSubTitle(
            r'Bla <a href="https://docs.3di.live/i_running_a_simulation.html#starting-a-simulation/">documentation</a>.'
        )
        self.new_sim = new_sim

        main_widget = self.get_page_widget()

        layout = QGridLayout()
        main_widget.setLayout(layout)

        global_rb = QRadioButton("Global value", self)
        layout.addWidget(global_rb, 0, 0)
        global_le = QLineEdit("", self)
        layout.addWidget(global_le, 0, 1, 1, 2)
        online_rb = QRadioButton("Online raster", self)
        layout.addWidget(online_rb, 1, 0)
        online_dd = QComboBox(self)
        layout.addWidget(online_dd, 1, 1, 1, 2)
        local_rb = QRadioButton("Local raster", self)
        layout.addWidget(local_rb, 2, 0)
        local_dd = QComboBox(self)
        layout.addWidget(local_dd, 2, 1, 1, 2)
        layout.addWidget(QLabel("Aggregation method"), 3, 0)
        aggregation_dd = QComboBox(self)
        layout.addWidget(aggregation_dd, 3, 1, 1, 2)

        vertical_spacer = QSpacerItem(
            20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding
        )
        layout.addItem(vertical_spacer, 4, 0)

    def initializePage(self):
        pass

    def validatePage(self):
        return True

    def isComplete(self):
        return True

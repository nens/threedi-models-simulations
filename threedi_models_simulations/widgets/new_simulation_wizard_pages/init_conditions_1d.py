from qgis.core import Qgis, QgsMessageLog
from qgis.PyQt.QtWidgets import (
    QCheckBox,
    QGridLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QRadioButton,
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

        layout = QVBoxLayout()
        main_widget.setLayout(layout)

        layout.addWidget(QLabel("Bla", main_widget))

        layout.addStretch()

    def initializePage(self):
        pass

    def validatePage(self):
        return True

    def isComplete(self):
        return True

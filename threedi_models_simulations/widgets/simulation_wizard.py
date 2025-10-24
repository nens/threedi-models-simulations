import os

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QPixmap
from qgis.PyQt.QtWidgets import QWizard

from threedi_models_simulations.constants import ICONS_DIR
from threedi_models_simulations.widgets.new_simulation_wizard_pages.initialization import (
    InitializationPage,
)
from threedi_models_simulations.widgets.new_simulation_wizard_pages.name import (
    NamePage,
)


class SimulationWizard(QWizard):
    def __init__(
        self,
        new_sim,
        parent,
    ):
        super().__init__(parent)
        self.setWindowTitle("New simulation")
        self.setWizardStyle(QWizard.ClassicStyle)
        self.setSubTitleFormat(Qt.RichText)
        self.setPixmap(
            QWizard.WizardPixmap.LogoPixmap,
            QPixmap(os.path.join(ICONS_DIR, "logo.svg")),
        )
        self.addPage(InitializationPage(self, new_sim))
        self.addPage(NamePage(self, new_sim))

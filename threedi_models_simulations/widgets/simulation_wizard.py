import os

from qgis.core import Qgis, QgsApplication, QgsMessageLog
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QPixmap
from qgis.PyQt.QtWidgets import QLabel, QWizard

from threedi_models_simulations.constants import ICONS_DIR
from threedi_models_simulations.widgets.new_simulation_wizard_pages.initialization import (
    InitializationPage,
)


class SimulationWizard(QWizard):
    def __init__(
        self,
        simulation,
        settings_overview,
        events,
        lizard_post_processing_overview,
        simulation_template,
        parent,
    ):
        # QgsMessageLog.logMessage("-----------", level=Qgis.Critical)
        # QgsMessageLog.logMessage(str(simulation), level=Qgis.Critical)
        # QgsMessageLog.logMessage("-----------", level=Qgis.Critical)
        # QgsMessageLog.logMessage(str(settings_overview), level=Qgis.Critical)
        # QgsMessageLog.logMessage("-----------", level=Qgis.Critical)
        # QgsMessageLog.logMessage(str(events), level=Qgis.Critical)
        # QgsMessageLog.logMessage("-----------", level=Qgis.Critical)
        # QgsMessageLog.logMessage(str(lizard_post_processing_overview), level=Qgis.Critical)
        # QgsMessageLog.logMessage("-----------", level=Qgis.Critical)
        # QgsMessageLog.logMessage(str(simulation_template), level=Qgis.Critical)

        super().__init__(parent)
        self.setWindowTitle("New simulation")
        self.setWizardStyle(QWizard.ClassicStyle)
        self.setSubTitleFormat(Qt.RichText)
        self.setPixmap(
            QWizard.WizardPixmap.LogoPixmap,
            QPixmap(os.path.join(ICONS_DIR, "logo.svg")),
        )
        self.addPage(InitializationPage(self))

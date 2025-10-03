import os

from qgis.PyQt.QtGui import QPixmap
from qgis.PyQt.QtWidgets import QLabel, QVBoxLayout, QWizard, QWizardPage

from threedi_models_simulations.constants import ICONS_DIR


class SimulationWizard(QWizard):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Simulation Wizard")
        self.setWizardStyle(QWizard.ClassicStyle)
        self.setPixmap(
            QWizard.WizardPixmap.LogoPixmap,
            QPixmap(os.path.join(ICONS_DIR, "logo.svg")),
        )
        self.addPage(self.createIntroPage())

    def createIntroPage(self):
        page = QWizardPage()
        page.setTitle("Introduction")
        page.setSubTitle("bla")

        label = QLabel(
            "This wizard will help you register your copy of Super Product Two."
        )
        label.setWordWrap(True)
        layout = QVBoxLayout()
        layout.addWidget(label)
        page.setLayout(layout)

        return page

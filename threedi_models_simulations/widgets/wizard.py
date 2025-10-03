from qgis.PyQt.QtWidgets import QWizard


class SimulationWizard(QWizard):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Simulation Wizard")
        self.setWizardStyle(QWizard.ClassicStyle)

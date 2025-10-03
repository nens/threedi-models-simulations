from qgis.PyQt.QtWidgets import QAction

from threedi_models_simulations.constants import PLUGIN_NAME, plugin_icon


class ModelsSimulationsPlugin:
    def __init__(self, iface):
        self.iface = iface

    def initGui(self):
        self.toolbar = self.iface.addToolBar(PLUGIN_NAME)
        self.action = QAction(plugin_icon, "Test", self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.toolbar.addAction(self.action)

    def unload(self):
        self.iface.removeToolBarIcon(self.action)

    def run(self):
        pass

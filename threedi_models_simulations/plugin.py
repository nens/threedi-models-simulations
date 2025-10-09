from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QAction

from threedi_models_simulations.constants import PLUGIN_NAME, logo_icon, plugin_icon
from threedi_models_simulations.models.simulation import Simulation
from threedi_models_simulations.widgets.dock import DockWidget
from threedi_models_simulations.widgets.settings import SettingsDialog
from threedi_models_simulations.widgets.wizard import SimulationWizard


class ModelsSimulationsPlugin:
    def __init__(self, iface):
        self.iface = iface

    def initGui(self):
        self.toolbar = self.iface.addToolBar(PLUGIN_NAME)
        self.action = QAction(
            plugin_icon, "Toggle M&&S plugin", self.iface.mainWindow()
        )
        self.action.triggered.connect(self.run)
        self.toolbar.addAction(self.action)

        self.action_wiz = QAction(
            logo_icon, "Start simulation wizard", self.iface.mainWindow()
        )
        self.action_wiz.triggered.connect(self.start_simulation_wizard)
        self.toolbar.addAction(self.action_wiz)

        self.dockwidget = DockWidget(None, self.iface)
        self.dockwidget.setVisible(False)
        self.iface.addTabifiedDockWidget(
            Qt.DockWidgetArea.RightDockWidgetArea, self.dockwidget, raiseTab=True
        )
        self.dockwidget.pushButton_simulate.pressed.connect(
            self.start_simulation_wizard
        )

    def start_simulation_wizard(self):
        # pass it a model
        # s = Simulation()
        wiz = SimulationWizard(self.dockwidget)
        wiz.exec()

        # pass the model to a sender

    def unload(self):
        self.iface.removeToolBarIcon(self.action)
        self.iface.removeToolBarIcon(self.action_wiz)
        self.iface.removeDockWidget(self.dockwidget)
        del self.dockwidget
        del self.toolbar

    def run(self):
        dialog = SettingsDialog(self.dockwidget)
        dialog.exec()
        self.dockwidget.setVisible(not self.dockwidget.isVisible())

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QAction
from qgis.PyQt.QtWidgets import QMessageBox

from threedi_models_simulations.constants import LOGO_ICON, PLUGIN_ICON, PLUGIN_NAME
from threedi_models_simulations.models.simulation import Simulation
from threedi_models_simulations.widgets.dock import DockWidget
from threedi_models_simulations.widgets.settings import (
    SettingsDialog,
    settings_are_valid,
)
from threedi_models_simulations.widgets.wizard import SimulationWizard


class ModelsSimulationsPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.actions = []

    def initGui(self):
        self.toolbar = self.iface.addToolBar(PLUGIN_NAME)

        self.dockwidget = DockWidget(None, self.iface)
        self.dockwidget.setVisible(False)
        self.iface.addTabifiedDockWidget(
            Qt.DockWidgetArea.RightDockWidgetArea, self.dockwidget, raiseTab=True
        )

        self.add_action(
            PLUGIN_ICON,
            text="3Di Models and Simulations2",
            callback=self.run,
            parent=self.iface.mainWindow(),
        )
        self.add_action(
            PLUGIN_ICON,
            text="Settings2",
            callback=self.show_settings,
            parent=self.iface.mainWindow(),
            add_to_toolbar=False,
        )

    def start_simulation_wizard(self):
        # pass it a model
        # s = Simulation()
        wiz = SimulationWizard(self.dockwidget)
        wiz.exec()

        # pass the model to a sender

    def unload(self):
        self.dockwidget.setVisible(False)

        for action in self.actions:
            self.iface.removePluginMenu("3Di Models and Simulations", action)
            self.iface.removeToolBarIcon(action)

        self.iface.removeDockWidget(self.dockwidget)
        del self.dockwidget
        del self.toolbar

    def show_settings(self):
        dialog = SettingsDialog(self.dockwidget)
        dialog.exec()
        if not settings_are_valid():
            QMessageBox.warning(
                self.dockwidget,
                "Warning",
                "The current settings are not valid, unable to start the M&S plugin",
            )
            return
        # TODO: logout when settings changed
        # self.plugin_settings.settings_changed.connect(dock.on_log_out)

    def run(self):
        if not settings_are_valid():
            dialog = SettingsDialog(self.dockwidget)
            dialog.exec()

        if not settings_are_valid():
            QMessageBox.warning(
                self.dockwidget,
                "Warning",
                "The current settings are not valid, unable to start the M&S plugin",
            )
            return

        self.dockwidget.setVisible(not self.dockwidget.isVisible())

    def add_action(
        self,
        icon,
        text,
        callback,
        add_to_menu=True,
        add_to_toolbar=True,
        parent=None,
    ):
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu("3Di Models and Simulations", action)

        self.actions.append(action)
        return action

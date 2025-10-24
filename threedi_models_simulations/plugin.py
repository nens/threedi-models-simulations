import os

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QAction
from qgis.PyQt.QtWidgets import QMessageBox

from threedi_models_simulations.constants import CACHE_PATH, PLUGIN_ICON, PLUGIN_NAME
from threedi_models_simulations.widgets.dock import DockWidget
from threedi_models_simulations.widgets.settings import (
    SettingsDialog,
    settings_are_valid,
)


class ModelsSimulationsPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.actions = []

    def initGui(self):
        self.toolbar = self.iface.addToolBar(PLUGIN_NAME)

        self.dockwidget = DockWidget(None, self.iface)
        self.dockwidget.setVisible(False)
        self.dockwidget.settings_requested.connect(self.show_settings)
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

    def unload(self):
        self.dockwidget.setVisible(False)
        self.dockwidget.unload()

        for action in self.actions:
            self.iface.removePluginMenu("3Di Models and Simulations", action)
            self.iface.removeToolBarIcon(action)

        self.iface.removeDockWidget(self.dockwidget)
        del self.dockwidget
        del self.toolbar

    def show_settings(self):
        dialog = SettingsDialog(self.dockwidget)
        # logout when settings changed
        dialog.settings_changed.connect(self.dockwidget.on_log_out)

        dialog.exec()
        if not settings_are_valid():
            QMessageBox.warning(
                self.dockwidget,
                "Warning",
                "The current settings are not valid, unable to start the M&S plugin",
            )
            return

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

        os.makedirs(CACHE_PATH, exist_ok=True)

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

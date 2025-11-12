import os

from qgis.core import Qgis, QgsMessageLog
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QFont, QPixmap, QStandardItem, QStandardItemModel
from qgis.PyQt.QtWidgets import QWizard

from threedi_models_simulations.constants import ICONS_DIR
from threedi_models_simulations.widgets.new_simulation_wizard_pages.duration import (
    DurationPage,
)
from threedi_models_simulations.widgets.new_simulation_wizard_pages.init_conditions_1d import (
    InitialConditions1DPage,
)
from threedi_models_simulations.widgets.new_simulation_wizard_pages.init_conditions_2d import (
    InitialConditions2DPage,
)
from threedi_models_simulations.widgets.new_simulation_wizard_pages.init_conditions_groundwater import (
    InitialConditionsGroundWaterPage,
)
from threedi_models_simulations.widgets.new_simulation_wizard_pages.initialization import (
    InitializationPage,
)
from threedi_models_simulations.widgets.new_simulation_wizard_pages.name import (
    NamePage,
)
from threedi_models_simulations.widgets.new_simulation_wizard_pages.settings import (
    SettingsPage,
)
from threedi_models_simulations.widgets.new_simulation_wizard_pages.substances import (
    SubstancesPage,
)


class SimulationWizard(QWizard):
    def __init__(self, new_sim, threedi_api, organisation, parent, communication):
        super().__init__(parent)
        self.setWindowTitle("New simulation")
        self.setWizardStyle(QWizard.ClassicStyle)
        self.setSubTitleFormat(Qt.RichText)
        self.setPixmap(
            QWizard.WizardPixmap.LogoPixmap,
            QPixmap(os.path.join(ICONS_DIR, "logo.svg")),
        )

        self.backPressed = False
        back_button = self.button(QWizard.WizardButton.BackButton)
        back_button.clicked.connect(self.on_back_clicked)

        self.currentIdChanged.connect(self.page_changed)

        self.tree_model = QStandardItemModel(self)
        parent_item = self.tree_model.invisibleRootItem()

        initialization = QStandardItem("Initialization")
        initialization.setData(
            InitializationPage(self, new_sim, threedi_api, organisation)
        )

        name = QStandardItem("Name")
        name.setData(NamePage(self, new_sim))

        duration = QStandardItem("Duration")
        duration.setData(DurationPage(self, new_sim))

        substances = QStandardItem("Substances")
        substances.setData(SubstancesPage(self, new_sim, communication))

        initial_cond_1d = QStandardItem("1D initial waterlevels")
        initial_cond_1d.setData(
            InitialConditions1DPage(self, new_sim, threedi_api, communication)
        )

        initial_cond_2d = QStandardItem("2D initial waterlevels")
        initial_cond_2d.setData(InitialConditions2DPage(self, new_sim))

        initial_cond_groundwater = QStandardItem("Groundwater waterlevels")
        initial_cond_groundwater.setData(
            InitialConditionsGroundWaterPage(self, new_sim)
        )

        settings = QStandardItem("Settings")
        settings.setData(SettingsPage(self, new_sim))

        self.addPage(initialization.data())
        self.addPage(name.data())
        self.addPage(duration.data())
        self.addPage(substances.data())
        self.addPage(initial_cond_1d.data())
        self.addPage(initial_cond_2d.data())
        self.addPage(initial_cond_groundwater.data())
        self.addPage(settings.data())

        parent_item.appendRow(initialization)
        parent_item.appendRow(name)
        parent_item.appendRow(duration)

        sep1 = QStandardItem()
        sep1.setData(True, Qt.UserRole + 10)  # mark as separator
        parent_item.appendRow(sep1)
        parent_item.appendRow(substances)
        sep2 = QStandardItem()
        sep2.setData(True, Qt.UserRole + 10)
        parent_item.appendRow(sep2)

        initial_cond = QStandardItem("Initial conditions")
        initial_cond.appendRow(initial_cond_1d)
        initial_cond.appendRow(initial_cond_2d)
        initial_cond.appendRow(initial_cond_groundwater)
        parent_item.appendRow(initial_cond)
        sep3 = QStandardItem()
        sep3.setData(True, Qt.UserRole + 10)
        parent_item.appendRow(sep3)

        parent_item.appendRow(settings)

        self.resize(800, 700)

    def page_changed(self, newId: int):
        """Update the step widget of the current page"""

        current_page = self.currentPage()
        if current_page is not None:
            if current_page.get_steps_widget() is not None:
                # Find the item in the model corresponding to the current page
                # and set it to bold
                SimulationWizard.set_items_bold_by_data(self.tree_model, current_page)
                current_page.get_steps_tree().setModel(self.tree_model)
                current_page.get_steps_tree().expandAll()

    def on_back_clicked(self):
        # The user went back, needs to be reset in the page's isComplete
        QgsMessageLog.logMessage("self.backPressed = True")
        self.backPressed = True

    @staticmethod
    def set_items_bold_by_data(model, value):
        # sets the item with specific data value to bold, others to normal
        root = model.invisibleRootItem()

        def recurse(parent):
            for row in range(parent.rowCount()):
                item = parent.child(row)
                font = QFont()
                font.setBold(item.data() is value)
                item.setFont(font)
                recurse(item)

        return recurse(root)

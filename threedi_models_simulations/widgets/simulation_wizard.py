import os

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QFont, QPixmap, QStandardItem, QStandardItemModel
from qgis.PyQt.QtWidgets import QWizard

from threedi_models_simulations.constants import ICONS_DIR
from threedi_models_simulations.widgets.new_simulation_wizard_pages.duration import (
    DurationPage,
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
    def __init__(
        self,
        new_sim,
        threedi_api,
        organisation,
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
        substances.setData(SubstancesPage(self, new_sim))

        settings = QStandardItem("Settings")
        settings.setData(SettingsPage(self, new_sim))

        self.addPage(initialization.data())
        self.addPage(name.data())
        self.addPage(duration.data())
        self.addPage(substances.data())
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
        parent_item.appendRow(settings)

        self.resize(800, 700)

    def page_changed(self):
        """Update the step widget of the current page"""

        current_page = self.currentPage()
        if current_page is not None:
            if current_page.get_steps_widget() is not None:
                # Find the item in the model corresponding to the current page
                # and set it to bold
                SimulationWizard.set_items_bold_by_data(self.tree_model, current_page)
                current_page.get_steps_tree().setModel(self.tree_model)

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

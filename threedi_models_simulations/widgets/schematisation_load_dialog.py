from qgis.PyQt.QtCore import QItemSelectionModel, Qt
from qgis.PyQt.QtGui import QStandardItem, QStandardItemModel
from qgis.PyQt.QtWidgets import (
    QDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QTreeView,
)
from threedi_mi_utils import (
    WIPRevision,
    list_local_schematisations,
    replace_revision_data,
)


class SchematisationLoadDialog(QDialog):
    """Dialog for local schematisation loading."""

    def __init__(self, working_dir, communication, parent=None):
        super().__init__(parent)
        self.working_dir = working_dir
        self.communication = communication

        self.setWindowTitle("Load local schematisation")

        self.gridLayout = QGridLayout(self)

        self.schematisation_download_widget = self
        self.innerLayout = QGridLayout()
        self.gridLayout.addLayout(self.innerLayout, 0, 0)

        self.label_2 = QLabel("Available local schematisations")
        self.innerLayout.addWidget(self.label_2, 0, 0)

        self.schematisations_tv = QTreeView()
        self.schematisations_tv.setEditTriggers(QTreeView.NoEditTriggers)
        self.schematisations_tv.setSortingEnabled(True)
        self.innerLayout.addWidget(self.schematisations_tv, 1, 0, 1, 2)

        self.label = QLabel("Local schematisation revisions")
        self.innerLayout.addWidget(self.label, 2, 0)

        self.revisions_tv = QTreeView()
        self.revisions_tv.setEditTriggers(QTreeView.NoEditTriggers)
        self.innerLayout.addWidget(self.revisions_tv, 3, 0)

        self.horizontalLayout_2 = QHBoxLayout()

        self.pb_cancel = QPushButton("Cancel")
        self.horizontalLayout_2.addWidget(self.pb_cancel)

        spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacer)

        self.pb_load = QPushButton("Load")
        self.pb_load.setEnabled(False)
        self.horizontalLayout_2.addWidget(self.pb_load)

        self.innerLayout.addLayout(self.horizontalLayout_2, 4, 0, 1, 2)

        self.local_schematisations = list_local_schematisations(
            self.working_dir, use_config_for_revisions=False
        )
        self.tv_schematisations_model = QStandardItemModel()
        self.schematisations_tv.setModel(self.tv_schematisations_model)
        self.tv_revisions_model = QStandardItemModel()
        self.revisions_tv.setModel(self.tv_revisions_model)
        self.selected_local_schematisation = None
        self.pb_load.clicked.connect(self.load_local_schematisation)
        self.pb_cancel.clicked.connect(self.cancel_load_local_schematisation)
        self.schematisations_tv.selectionModel().selectionChanged.connect(
            self.populate_local_schematisation_revisions
        )
        self.revisions_tv.selectionModel().selectionChanged.connect(
            self.toggle_load_local_schematisation
        )
        self.populate_local_schematisations()

    def populate_local_schematisations(self):
        """Populate local schematisations."""
        self.tv_revisions_model.clear()
        self.tv_schematisations_model.clear()
        header = ["Schematisation name", "Schematisation ID", "Absolute path"]
        self.tv_schematisations_model.setHorizontalHeaderLabels(header)
        for (
            schematisation_id,
            local_schematisation,
        ) in self.local_schematisations.items():
            name_item = QStandardItem(local_schematisation.name)
            name_item.setData(local_schematisation, role=Qt.UserRole)
            id_item = QStandardItem(str(schematisation_id))
            dir_item = QStandardItem(local_schematisation.main_dir)
            self.tv_schematisations_model.appendRow([name_item, id_item, dir_item])
        for i in range(len(header)):
            self.schematisations_tv.resizeColumnToContents(i)

    def populate_local_schematisation_revisions(self):
        """Populate local schematisation revisions."""
        self.tv_revisions_model.clear()
        header = ["Revision number", "Subdirectory"]
        self.tv_revisions_model.setHorizontalHeaderLabels(header)
        local_schematisation = self.get_selected_local_schematisation()
        wip_revision = local_schematisation.wip_revision
        if wip_revision is not None:
            number_item = QStandardItem(str(wip_revision.number))
            number_item.setData(wip_revision, role=Qt.UserRole)
            subdir_item = QStandardItem(wip_revision.sub_dir)
            self.tv_revisions_model.appendRow([number_item, subdir_item])
        for revision_number, local_revision in reversed(
            local_schematisation.revisions.items()
        ):
            number_item = QStandardItem(str(revision_number))
            number_item.setData(local_revision, role=Qt.UserRole)
            subdir_item = QStandardItem(local_revision.sub_dir)
            self.tv_revisions_model.appendRow([number_item, subdir_item])
        for i in range(len(header)):
            self.schematisations_tv.resizeColumnToContents(i)
        if self.tv_revisions_model.rowCount() > 0:
            row_idx = self.tv_revisions_model.index(0, 0)
            self.revisions_tv.selectionModel().setCurrentIndex(
                row_idx, QItemSelectionModel.ClearAndSelect
            )
        self.toggle_load_local_schematisation()

    def toggle_load_local_schematisation(self):
        """Toggle load button if any schematisation revision is selected."""
        selection_model = self.revisions_tv.selectionModel()
        if selection_model.hasSelection():
            self.pb_load.setEnabled(True)
        else:
            self.pb_load.setDisabled(True)

    def get_selected_local_schematisation(self):
        """Get currently selected local schematisation."""
        index = self.schematisations_tv.currentIndex()
        if index.isValid():
            current_row = index.row()
            name_item = self.tv_schematisations_model.item(current_row, 0)
            local_schematisation = name_item.data(Qt.UserRole)
        else:
            local_schematisation = None
        return local_schematisation

    def get_selected_local_revision(self):
        """Get currently selected local revision."""
        index = self.revisions_tv.currentIndex()
        if index.isValid():
            current_row = index.row()
            name_item = self.tv_revisions_model.item(current_row, 0)
            local_revision = name_item.data(Qt.UserRole)
        else:
            local_revision = None
        return local_revision

    def load_local_schematisation(self):
        """Loading selected local schematisation."""
        local_schematisation = self.get_selected_local_schematisation()
        local_revision = self.get_selected_local_revision()
        if not isinstance(local_revision, WIPRevision):
            title = "Pick action"
            question = (
                f"Replace WIP with data from the revision {local_revision.number}?"
            )
            picked_action_name = self.communication.custom_ask(
                self, title, question, "Replace", "Cancel"
            )
            if picked_action_name == "Replace":
                wip_revision = local_schematisation.set_wip_revision(
                    local_revision.number
                )
                replace_revision_data(local_revision, wip_revision)
            else:
                local_schematisation = None
        self.selected_local_schematisation = local_schematisation
        self.close()

    def cancel_load_local_schematisation(self):
        """Cancel local schematisation loading."""
        self.close()

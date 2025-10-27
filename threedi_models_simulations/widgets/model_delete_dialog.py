from operator import attrgetter

from qgis.PyQt.QtCore import QDateTime, Qt
from qgis.PyQt.QtGui import QStandardItem, QStandardItemModel
from qgis.PyQt.QtWidgets import (
    QCheckBox,
    QDialog,
    QGridLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QTreeView,
)
from threedi_api_client.openapi import ApiException

from threedi_models_simulations.constants import MAX_SCHEMATISATION_MODELS
from threedi_models_simulations.utils.threedi_api import (
    FETCH_LIMIT,
    delete_model,
    extract_error_message,
    fetch_contracts,
    fetch_models_with_count,
)


class ModelDeletionDialog(QDialog):
    """Dialog for model(s) deletion."""

    def __init__(
        self,
        communication,
        threedi_api,
        current_local_schematisation,
        organisation,
        parent,
    ):
        super().__init__(parent)

        self.setWindowTitle("Delete excess models")
        self.resize(900, 345)

        layout = QGridLayout(self)

        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setText(
            "<html><head/><body>"
            '<p align="center"><span style=" color:#ff0000;">'
            "Maximum number of active 3Di models for {} is {} ({} found). "
            "Please remove any excess models to continue uploading."
            "</span></p></body></html>"
        )
        layout.addWidget(self.label, 0, 0, 1, 3)

        self.models_tv = QTreeView(self)
        self.models_tv.setFrameShape(QTreeView.NoFrame)
        self.models_tv.setEditTriggers(QTreeView.NoEditTriggers)
        self.models_tv.setSelectionMode(QTreeView.ExtendedSelection)
        layout.addWidget(self.models_tv, 1, 0, 1, 3)

        self.cb_filter = QCheckBox("Only show my own 3Di models", self)
        layout.addWidget(self.cb_filter, 2, 2)

        self.pb_cancel = QPushButton("Cancel", self)
        layout.addWidget(self.pb_cancel, 3, 0)

        spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        layout.addItem(spacer, 3, 1)

        self.pb_delete = QPushButton("Delete selected model(s)", self)
        self.pb_delete.setEnabled(False)
        layout.addWidget(self.pb_delete, 3, 2)

        self.communication = communication
        self.threedi_api = threedi_api
        self.local_schematisation = current_local_schematisation
        self.organisation = organisation

        self.label_template = self.label.text()
        self.threedi_models_to_show = []
        self.models_model = QStandardItemModel()
        self.models_tv.setModel(self.models_model)
        self.pb_delete.clicked.connect(self.delete_models)
        self.pb_cancel.clicked.connect(self.reject)
        self.cb_filter.stateChanged.connect(self.filter_models_by_username)
        self.models_tv.selectionModel().selectionChanged.connect(
            self.toggle_delete_models
        )
        self.check_limits()

    def toggle_delete_models(self):
        """Toggle delete button if any model is selected."""
        selection_model = self.models_tv.selectionModel()
        if selection_model.hasSelection():
            self.pb_delete.setEnabled(True)
        else:
            self.pb_delete.setDisabled(True)

    def filter_models_by_username(self):
        """Filter models list and show only those created by currently logged-in user."""
        if self.cb_filter.isChecked():
            user_models = [
                model
                for model in self.threedi_models_to_show
                if model.user == self.plugin_dock.current_user
            ]
            self.populate_models(user_models)
        else:
            self.populate_models(self.threedi_models_to_show)

    def check_limits(self):
        """Check 3Di models creation limits."""
        self.threedi_models_to_show.clear()
        try:
            schematisation_limit_filters = {
                "limit": FETCH_LIMIT,
                "schematisation_name": self.local_schematisation.name,
            }
            schematisation_limit = MAX_SCHEMATISATION_MODELS
            threedi_models, models_count = fetch_models_with_count(
                self.threedi_api, **schematisation_limit_filters
            )
            if models_count >= schematisation_limit:
                self.label.setText(
                    self.label_template.format(
                        "schematisation", schematisation_limit, models_count
                    )
                )
                self.setup_dialog(threedi_models)
                return
            organisation_uuid = self.organisation.unique_id
            contract = fetch_contracts(
                self.threedi_api, organisation__unique_id=organisation_uuid
            )[0]
            organisation_limit = contract.threedimodel_limit
            organisation_limit_filters = {
                "limit": FETCH_LIMIT,
                "schematisation_owner": organisation_uuid,
            }
            threedi_models, models_count = fetch_models_with_count(
                self.threedi_api, **organisation_limit_filters
            )
            if models_count >= organisation_limit:
                self.label.setText(
                    self.label_template.format(
                        "organisation", organisation_limit, models_count
                    )
                )
                self.setup_dialog(threedi_models)
                return
            else:
                self.accept()
        except ApiException as e:
            error_msg = extract_error_message(e)
            self.communication.show_error(error_msg, self, "Model Deletion")
        except Exception as e:
            error_msg = f"Error: {e}"
            self.communication.show_error(error_msg, self, "Model Deletion")

    def setup_dialog(self, threedi_models):
        """Setup model deletion dialog."""
        self.threedi_models_to_show.clear()
        self.populate_models(threedi_models)
        self.threedi_models_to_show = threedi_models

    def populate_models(self, threedi_models):
        """Populate 3Di models within a dialog."""
        self.models_tv.clearSelection()
        self.models_model.clear()
        header = [
            "ID",
            "Model",
            "Schematisation",
            "Revision",
            "Created By",
            "Created On",
        ]
        self.models_model.setHorizontalHeaderLabels(header)
        for sim_model in sorted(
            threedi_models, key=attrgetter("revision_commit_date"), reverse=True
        ):
            id_item = QStandardItem(str(sim_model.id))
            name_item = QStandardItem(sim_model.name)
            name_item.setData(sim_model, role=Qt.UserRole)
            schema_item = QStandardItem(sim_model.schematisation_name)
            rev_number = sim_model.revision_number
            rev_item = QStandardItem(rev_number)
            rev_item.setData(int(rev_number), role=Qt.DisplayRole)
            created_by_item = QStandardItem(sim_model.user)
            created_on = sim_model.revision_commit_date.split("T")[0]
            created_on_datetime = QDateTime.fromString(created_on, "yyyy-MM-dd")
            created_on_item = QStandardItem(
                created_on_datetime.toString("dd-MMMM-yyyy")
            )
            self.models_model.appendRow(
                [
                    id_item,
                    name_item,
                    schema_item,
                    rev_item,
                    created_by_item,
                    created_on_item,
                ]
            )

    def delete_models(self):
        """Deleting selected model(s)."""
        selection_model = self.models_tv.selectionModel()
        if not selection_model.hasSelection():
            return
        try:
            for index in selection_model.selectedRows():
                current_row = index.row()
                model_id_item = self.models_model.item(current_row, 0)
                model_id = int(model_id_item.text())
                delete_model(self.threedi_api, model_id)
        except ApiException as e:
            error_msg = extract_error_message(e)
            self.communication.show_error(error_msg)
        except Exception as e:
            error_msg = f"Error: {e}"
            self.communication.show_error(error_msg)
        finally:
            self.check_limits()

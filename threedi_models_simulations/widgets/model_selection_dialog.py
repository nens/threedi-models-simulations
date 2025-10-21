import os
from functools import partial
from math import ceil
from operator import attrgetter

from qgis.core import QgsMapLayer, QgsProject, QgsVectorLayer
from qgis.PyQt.QtCore import (
    QDateTime,
    QItemSelectionModel,
    QModelIndex,
    QSize,
    QSortFilterProxyModel,
    Qt,
)
from qgis.PyQt.QtGui import QIcon, QStandardItem, QStandardItemModel
from qgis.PyQt.QtWidgets import (
    QComboBox,
    QDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QSpinBox,
    QToolButton,
    QTreeView,
    QWidget,
)
from qgis.utils import iface
from threedi_api_client.openapi import ApiException
from threedi_mi_utils import LocalSchematisation, list_local_schematisations

from threedi_models_simulations.constants import ICONS_DIR
from threedi_models_simulations.threedi_api_utils import (
    extract_error_message,
    fetch_model_geojson_breaches_download,
    fetch_model_geopackage_download,
    fetch_models_with_count,
    fetch_schematisation,
    fetch_simulation_templates_with_count,
    get_download_file,
)
from threedi_models_simulations.utils import set_named_style
from threedi_models_simulations.widgets.settings import (
    read_3di_settings,
    save_3di_settings,
)
from threedi_models_simulations.workers.runner import CACHE_PATH

TABLE_LIMIT = 10
COLUMN_ID = 0
NAME_COLUMN_IDX = 1
SCHEMATISATION_COLUMN_IDX = 2
SCHEMATISATION_REVISION_COLUMN_IDX = 3
LAST_UPDATED_COLUMN_IDX = 4
UPDATED_BY_COLUMN_IDX = 5


class SortFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)

    def lessThan(self, left: QModelIndex, right: QModelIndex):
        leftData = self.sourceModel().data(left)
        rightData = self.sourceModel().data(right)
        if left.column() in [LAST_UPDATED_COLUMN_IDX]:
            left_datetime = QDateTime.fromString(leftData, "dd-MMMM-yyyy")
            right_datetime = QDateTime.fromString(rightData, "dd-MMMM-yyyy")
            return left_datetime < right_datetime
        elif left.column() in [COLUMN_ID, SCHEMATISATION_REVISION_COLUMN_IDX]:
            return int(leftData) < int(rightData)
        else:
            return leftData < rightData


class ModelSelectionDialog(QDialog):
    """Dialog for model selection."""

    def __init__(
        self,
        communication,
        current_user,
        threedi_api,
        organisations,
        working_dir,
        current_local_schematisation,
        parent,
    ):
        super().__init__(parent)

        self.communication = communication
        self.current_user = current_user
        self.threedi_api = threedi_api
        self.organisations = organisations
        self.working_dir = working_dir
        self.current_local_schematisation = current_local_schematisation

        self.setWindowTitle("Select a model and simulation template")
        self.setMinimumSize(900, 650)
        self.resize(900, 650)
        self.setFocusPolicy(Qt.StrongFocus)

        gridLayout = QGridLayout(self)

        self.model_selection_widget = QWidget(self)
        self.model_selection_widget.setMinimumSize(500, 300)
        self.model_selection_widget.setSizePolicy(
            QSizePolicy.Preferred, QSizePolicy.Expanding
        )

        gridLayout_8 = QGridLayout(self.model_selection_widget)

        self.search_le = QLineEdit()
        self.search_le.setPlaceholderText("🔍 Search in models")
        gridLayout_8.addWidget(self.search_le, 0, 0, 1, 2)

        self.models_tv = QTreeView()
        self.models_tv.setEditTriggers(QTreeView.NoEditTriggers)
        self.models_tv.setSortingEnabled(True)
        gridLayout_8.addWidget(self.models_tv, 1, 0, 1, 2)

        self.pagination_layout = QHBoxLayout()
        self.pagination_layout.addSpacerItem(
            QSpacerItem(400, 20, QSizePolicy.Expanding)
        )

        self.pb_prev_page = QPushButton("<")
        self.pb_prev_page.setMinimumSize(40, 20)
        self.pagination_layout.addWidget(self.pb_prev_page)

        self.page_sbox = QSpinBox()
        self.page_sbox.setMinimumSize(60, 20)
        self.page_sbox.setFocusPolicy(Qt.StrongFocus)
        self.page_sbox.setStyleSheet("QSpinBox {background-color: white;}")
        self.page_sbox.setAlignment(Qt.AlignCenter)
        self.page_sbox.setButtonSymbols(QSpinBox.NoButtons)
        self.page_sbox.setSuffix(" / 100")
        self.page_sbox.setMinimum(1)
        self.pagination_layout.addWidget(self.page_sbox)

        self.pb_next_page = QPushButton(">")
        self.pb_next_page.setMinimumSize(40, 20)
        self.pagination_layout.addWidget(self.pb_next_page)

        gridLayout_8.addLayout(self.pagination_layout, 3, 0, 1, 2)

        self.templates_tv = QTreeView()
        self.templates_tv.setEditTriggers(QTreeView.NoEditTriggers)
        gridLayout_8.addWidget(self.templates_tv, 6, 0, 1, 2)

        templates_label_layout = QHBoxLayout()
        templates_label_layout.addWidget(QLabel("Simulation templates"))

        gridLayout_8.addLayout(templates_label_layout, 5, 0, 1, 2)

        self.templates_pagination_layout = QHBoxLayout()
        self.templates_pagination_layout.setContentsMargins(0, 0, 0, 0)
        self.templates_pagination_layout.addSpacerItem(
            QSpacerItem(400, 20, QSizePolicy.Expanding)
        )

        self.pb_templates_prev_page = QPushButton("<")
        self.pb_templates_prev_page.setMinimumSize(40, 20)
        self.templates_pagination_layout.addWidget(self.pb_templates_prev_page)

        self.templates_page_sbox = QSpinBox()
        self.templates_page_sbox.setMinimumSize(60, 20)
        self.templates_page_sbox.setFocusPolicy(Qt.StrongFocus)
        self.templates_page_sbox.setStyleSheet("QSpinBox {background-color: white;}")
        self.templates_page_sbox.setAlignment(Qt.AlignCenter)
        self.templates_page_sbox.setButtonSymbols(QSpinBox.NoButtons)
        self.templates_page_sbox.setSuffix(" / 1")
        self.templates_page_sbox.setMinimum(1)
        self.templates_pagination_layout.addWidget(self.templates_page_sbox)

        self.pb_templates_next_page = QPushButton(">")
        self.pb_templates_next_page.setMinimumSize(40, 20)
        self.templates_pagination_layout.addWidget(self.pb_templates_next_page)

        gridLayout_8.addLayout(self.templates_pagination_layout, 7, 0, 1, 2)

        self.billing_layout = QHBoxLayout()
        self.billing_layout.setContentsMargins(0, 0, 0, 0)

        label_6 = QLabel("Billing goes to:")
        self.billing_layout.addWidget(label_6)

        self.organisations_box = QComboBox()
        self.organisations_box.setMinimumSize(0, 30)
        self.billing_layout.addWidget(self.organisations_box)

        gridLayout_8.addLayout(self.billing_layout, 8, 0, 1, 2)

        gridLayout_8.addItem(
            QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding), 10, 0
        )

        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)

        self.refresh_btn = QPushButton(
            QIcon(os.path.join(ICONS_DIR, "refresh.svg")), "Update table", self
        )
        self.refresh_btn.setMinimumSize(0, 30)

        button_layout.addWidget(self.refresh_btn)
        button_layout.addSpacerItem(
            QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        )

        self.pb_load = QPushButton("Next")
        self.pb_load.setMinimumSize(100, 30)
        self.pb_load.setEnabled(False)
        button_layout.addWidget(self.pb_load)

        gridLayout_8.addLayout(button_layout, 11, 0, 1, 2)
        gridLayout.addWidget(self.model_selection_widget, 0, 0)

        self.local_schematisations = list_local_schematisations(
            self.working_dir, use_config_for_revisions=False
        )
        self.simulation_templates = None
        self.current_model = None
        self.current_model_gridadmin_gpkg = None
        self.current_model_geojson_breaches = None
        self.current_simulation_template = None
        self.potential_breaches_layer = None
        self.flowlines_layer = None
        self.organisation = None
        self.model_is_loaded = False
        self.source_models_model = QStandardItemModel(self)
        # ProxyModel is a wrapper around the source model, but with filtering/sorting
        self.proxy_models_model = SortFilterProxyModel(self)
        self.proxy_models_model.setSourceModel(self.source_models_model)
        self.models_tv.setModel(self.proxy_models_model)
        self.templates_model = QStandardItemModel()
        self.templates_model.setHorizontalHeaderLabels(
            ["ID", "Template name", "Created at"]
        )
        self.templates_tv.setModel(self.templates_model)
        self.pb_prev_page.clicked.connect(self.move_models_backward)
        self.pb_next_page.clicked.connect(self.move_models_forward)
        self.page_sbox.valueChanged.connect(self.fetch_3di_models)
        self.pb_load.clicked.connect(self.load_model)
        self.search_le.returnPressed.connect(self.search_model)
        self.models_tv.selectionModel().selectionChanged.connect(
            self.refresh_templates_list
        )
        self.templates_tv.selectionModel().selectionChanged.connect(
            self.toggle_load_model
        )
        self.populate_organisations()
        self.fetch_3di_models()
        self.organisations_box.currentTextChanged.connect(
            partial(save_3di_settings, "threedi/last_used_organisation")
        )

        self.refresh_btn.clicked.connect(self.fetch_3di_models)
        self.refresh_btn.clicked.connect(self.refresh_templates_list)

        self.search_le.setFocus()

        if self.current_local_schematisation is not None:
            self.search_le.setText(self.current_local_schematisation.name)
            self.fetch_3di_models()
            self.refresh_templates_list()

    def refresh_templates_list(self):
        """Refresh simulation templates list if any model is selected."""
        selection_model = self.models_tv.selectionModel()
        self.templates_model.clear()
        self.templates_model.setHorizontalHeaderLabels(
            ["ID", "Template name", "Created at"]
        )
        self.templates_page_sbox.setMaximum(1)
        self.templates_page_sbox.setSuffix(" / 1")
        if selection_model.hasSelection():
            self.fetch_simulation_templates()
            if self.templates_model.rowCount() > 0:
                row_idx = self.templates_model.index(0, 0)
                self.templates_tv.selectionModel().setCurrentIndex(
                    row_idx, QItemSelectionModel.ClearAndSelect
                )
        self.toggle_load_model()
        self.switch_to_model_organisation()

    def toggle_load_model(self):
        """Toggle load button if any model is selected."""
        selection_model = self.templates_tv.selectionModel()
        if selection_model.hasSelection():
            self.pb_load.setEnabled(True)
        else:
            self.pb_load.setDisabled(True)

    def move_models_backward(self):
        """Moving to the models previous results page."""
        self.page_sbox.setValue(self.page_sbox.value() - 1)

    def move_models_forward(self):
        """Moving to the models next results page."""
        self.page_sbox.setValue(self.page_sbox.value() + 1)

    def move_templates_backward(self):
        """Moving to the templates previous results page."""
        self.templates_page_sbox.setValue(self.page_sbox.value() - 1)

    def move_templates_forward(self):
        """Moving to the templates next results page."""
        self.templates_page_sbox.setValue(self.page_sbox.value() + 1)

    def populate_organisations(self):
        """Populating organisations list inside combo box."""
        for org in self.organisations.values():
            self.organisations_box.addItem(org.name, org)
        last_organisation = read_3di_settings("threedi/last_used_organisation")
        if last_organisation:
            self.organisations_box.setCurrentText(last_organisation)

    def switch_to_model_organisation(self):
        """Switch to model organisation."""
        selection_model = self.models_tv.selectionModel()
        if not selection_model.hasSelection():
            return
        schematisation_id = self.get_selected_model_schematisation()
        try:
            model_schematisation = fetch_schematisation(
                self.threedi_api, schematisation_id
            )
            model_schematisation_owner = model_schematisation.owner
            organisation = self.organisations.get(model_schematisation_owner)
            if organisation is not None:
                self.organisations_box.setCurrentText(organisation.name)
        except ApiException as e:
            self.close()
            error_msg = extract_error_message(e)
            self.communication.show_error(error_msg, self, "Error")
        except Exception as e:
            self.close()
            error_msg = f"Error: {e}"
            self.communication.show_error(error_msg, self, "Error")

    def fetch_3di_models(self):
        """Fetching 3Di models list."""
        try:
            offset = (self.page_sbox.value() - 1) * TABLE_LIMIT
            text = self.search_le.text()
            threedi_models, models_count = fetch_models_with_count(
                self.threedi_api, limit=TABLE_LIMIT, offset=offset, name_contains=text
            )
            pages_nr = ceil(models_count / TABLE_LIMIT) or 1
            self.page_sbox.setMaximum(pages_nr)
            self.page_sbox.setSuffix(f" / {pages_nr}")
            self.source_models_model.clear()
            header = [
                "ID",
                "Model",
                "Schematisation",
                "Revision",
                "Updated at",
                "Updated by",
            ]
            self.source_models_model.setHorizontalHeaderLabels(header)
            for sim_model in sorted(
                threedi_models, key=attrgetter("revision_commit_date"), reverse=True
            ):
                id_item = QStandardItem(str(sim_model.id))
                name_item = QStandardItem(sim_model.name)
                name_item.setData(sim_model, role=Qt.UserRole)
                schema_item = QStandardItem(sim_model.schematisation_name)
                schema_item.setData(sim_model.schematisation_id, role=Qt.UserRole)
                rev_number = sim_model.revision_number
                rev_item = QStandardItem(rev_number)
                rev_item.setData(int(rev_number), role=Qt.DisplayRole)
                last_updated_day = sim_model.revision_commit_date.split("T")[0]
                lu_datetime = QDateTime.fromString(last_updated_day, "yyyy-MM-dd")
                lu_item = QStandardItem(lu_datetime.toString("MMMM dd, yyyy"))
                ub_item = QStandardItem(sim_model.user)
                self.source_models_model.appendRow(
                    [id_item, name_item, schema_item, rev_item, lu_item, ub_item]
                )
        except ApiException as e:
            self.close()
            error_msg = extract_error_message(e)
            self.communication.show_error(error_msg, self, "Error")
        except Exception as e:
            self.close()
            error_msg = f"Error: {e}"
            self.communication.show_error(error_msg, self, "Error")

    def fetch_simulation_templates(self):
        """Fetching simulation templates list."""
        try:
            offset = (self.templates_page_sbox.value() - 1) * TABLE_LIMIT
            selected_model = self.get_selected_model()
            model_pk = selected_model.id
            templates, templates_count = fetch_simulation_templates_with_count(
                self.threedi_api, model_pk, limit=TABLE_LIMIT, offset=offset
            )
            pages_nr = ceil(templates_count / TABLE_LIMIT) or 1
            self.templates_page_sbox.setMaximum(pages_nr)
            self.templates_page_sbox.setSuffix(f" / {pages_nr}")
            self.templates_model.clear()
            header = ["ID", "Template name", "Created at"]
            self.templates_model.setHorizontalHeaderLabels(header)
            for template in sorted(templates, key=attrgetter("id"), reverse=True):
                id_item = QStandardItem(str(template.id))
                name_item = QStandardItem(template.name)
                name_item.setData(template, role=Qt.UserRole)
                creation_date = (
                    template.created.strftime(r"%B %d, %Y") if template.created else ""
                )
                creation_date_item = QStandardItem(creation_date)
                self.templates_model.appendRow([id_item, name_item, creation_date_item])
            for i in range(len(header)):
                self.templates_tv.resizeColumnToContents(i)
            self.simulation_templates = templates
        except ApiException as e:
            error_msg = extract_error_message(e)
            self.communication.show_error(error_msg, self, "Error")
        except Exception as e:
            error_msg = f"Error: {e}"
            self.communication.show_error(error_msg, self, "Error")

    def search_model(self):
        """Method used for searching models with text typed withing search bar."""
        self.page_sbox.valueChanged.disconnect(self.fetch_3di_models)
        self.page_sbox.setValue(1)
        self.page_sbox.valueChanged.connect(self.fetch_3di_models)
        self.fetch_3di_models()

    def load_breach_layers(self):
        """Loading breach layers into the map canvas."""
        if self.current_model_geojson_breaches is not None:
            potential_breaches_layer = QgsVectorLayer(
                self.current_model_geojson_breaches, "Potential breaches", "ogr"
            )
            if (
                potential_breaches_layer.isValid()
                and potential_breaches_layer.featureCount() > 0
            ):
                self.potential_breaches_layer = potential_breaches_layer
                set_named_style(self.potential_breaches_layer, "Potential breach.qml")
                self.potential_breaches_layer.setFlags(
                    QgsMapLayer.Searchable | QgsMapLayer.Identifiable
                )
                QgsProject.instance().addMapLayer(self.potential_breaches_layer, False)
                QgsProject.instance().layerTreeRoot().insertLayer(
                    0, self.potential_breaches_layer
                )
        if self.current_model_gridadmin_gpkg is not None:
            flowlines_uri = f"{self.current_model_gridadmin_gpkg}|layername=flowline"
            flowlines_layer = QgsVectorLayer(flowlines_uri, "1D2D flowlines", "ogr")
            flowlines_layer.setSubsetString('"line_type" IN (51, 52, 53, 54)')
            if flowlines_layer.isValid() and flowlines_layer.featureCount() > 0:
                self.flowlines_layer = flowlines_layer
                set_named_style(self.flowlines_layer, "1D2D flowline.qml")
                self.flowlines_layer.setFlags(
                    QgsMapLayer.Searchable | QgsMapLayer.Identifiable
                )
                QgsProject.instance().addMapLayer(self.flowlines_layer, False)
                QgsProject.instance().layerTreeRoot().insertLayer(
                    0, self.flowlines_layer
                )

    def unload_breach_layers(self):
        """Removing model related vector layers from map canvas."""
        try:
            if self.potential_breaches_layer is not None:
                QgsProject.instance().removeMapLayer(self.potential_breaches_layer)
                self.potential_breaches_layer = None
            if self.flowlines_layer is not None:
                QgsProject.instance().removeMapLayer(self.flowlines_layer)
                self.flowlines_layer = None
            iface.mapCanvas().refresh()
        except (AttributeError, RuntimeError):
            pass

    def load_model(self):
        """Loading selected model."""
        index = self.models_tv.currentIndex()
        if index.isValid():
            self.organisation = self.organisations_box.currentData()
            self.unload_breach_layers()
            source_index = self.proxy_models_model.mapToSource(index)
            current_row = source_index.row()
            name_item = self.source_models_model.item(current_row, NAME_COLUMN_IDX)
            self.current_model = name_item.data(Qt.UserRole)
            schematisation_name_item = self.source_models_model.item(
                current_row, SCHEMATISATION_COLUMN_IDX
            )
            selected_model_schematisation_id = schematisation_name_item.data(
                Qt.UserRole
            )
            selected_model_schematisation_name = schematisation_name_item.text()
            schematisation_revision_item = self.source_models_model.item(
                current_row, SCHEMATISATION_REVISION_COLUMN_IDX
            )
            selected_model_schematisation_revision = schematisation_revision_item.data(
                Qt.DisplayRole
            )
            self.current_model_gridadmin_gpkg = self.get_gridadmin_gpkg_path(
                selected_model_schematisation_id,
                selected_model_schematisation_name,
                selected_model_schematisation_revision,
            )
            self.current_model_geojson_breaches = self.get_breach_geojson_path(
                "breaches"
            )
            self.current_simulation_template = self.get_selected_template()
            self.model_is_loaded = True
        self.close()

    def get_selected_model(self):
        """Get currently selected model."""
        index = self.models_tv.currentIndex()
        if index.isValid():
            source_index = self.proxy_models_model.mapToSource(index)
            current_row = source_index.row()
            name_item = self.source_models_model.item(current_row, NAME_COLUMN_IDX)
            selected_model = name_item.data(Qt.UserRole)
        else:
            selected_model = None
        return selected_model

    def get_selected_model_schematisation(self):
        """Get currently selected model schematisation."""
        index = self.models_tv.currentIndex()
        if index.isValid():
            source_index = self.proxy_models_model.mapToSource(index)
            current_row = source_index.row()
            schematisation_name_item = self.source_models_model.item(
                current_row, SCHEMATISATION_COLUMN_IDX
            )
            selected_model_schematisation_id = schematisation_name_item.data(
                Qt.UserRole
            )
        else:
            selected_model_schematisation_id = None
        return selected_model_schematisation_id

    def get_selected_template(self):
        """Get currently selected simulation template."""
        index = self.templates_tv.currentIndex()
        if index.isValid():
            current_row = index.row()
            name_item = self.templates_model.item(current_row, NAME_COLUMN_IDX)
            selected_template = name_item.data(Qt.UserRole)
        else:
            selected_template = None
        return selected_template

    def get_gridadmin_gpkg_path(
        self, schematisation_id, schematisation_name, schematisation_revision
    ):
        """Get model gridadmin.gpkg file."""
        try:
            local_schematisation = self.local_schematisations[schematisation_id]
        except KeyError:
            local_schematisation = None
        if local_schematisation is None:
            local_schematisation = LocalSchematisation(
                self.working_dir, schematisation_id, schematisation_name, create=True
            )
            self.local_schematisations[schematisation_id] = local_schematisation
            local_revision = local_schematisation.add_revision(schematisation_revision)
        else:
            try:
                local_revision = local_schematisation.revisions[schematisation_revision]
            except KeyError:
                local_revision = local_schematisation.add_revision(
                    schematisation_revision
                )
        available_gridadming_gpkg_path = None
        expected_gridadming_gpkg_path = os.path.join(
            local_revision.grid_dir, "gridadmin.gpkg"
        )
        if not os.path.exists(expected_gridadming_gpkg_path):
            try:
                model_id = self.current_model.id
                gridadmin_file_gpkg, gridadmin_download_gpkg = (
                    fetch_model_geopackage_download(self.threedi_api, model_id)
                )
                get_download_file(
                    gridadmin_download_gpkg, expected_gridadming_gpkg_path
                )
                available_gridadming_gpkg_path = expected_gridadming_gpkg_path
                self.communication.bar_info(f"Gridadmin GeoPackage downloaded.")
            except ApiException as e:
                error_msg = extract_error_message(e)
                if "Geopackage file not found" in error_msg:
                    pass
                else:
                    self.communication.bar_error(error_msg)
            except Exception as e:
                error_msg = f"Error: {e}"
                self.communication.bar_error(error_msg)
        else:
            available_gridadming_gpkg_path = expected_gridadming_gpkg_path
        return available_gridadming_gpkg_path

    def get_breach_geojson_path(self, geojson_name):
        """Get breach geojson data (should be cached)."""
        breach_geojson_cached_file_path = None
        try:
            model_id = self.current_model.id
            if geojson_name == "breaches":
                download = fetch_model_geojson_breaches_download(
                    self.threedi_api, model_id
                )
            else:
                return breach_geojson_cached_file_path
            filename = f"{geojson_name}_{model_id}_{download.etag}.json"
            file_path = os.path.join(CACHE_PATH, filename)
            if not os.path.isfile(file_path):
                get_download_file(download, file_path)
            breach_geojson_cached_file_path = file_path
            self.communication.bar_info(f"Model {geojson_name} cached.")
        except ApiException as e:
            error_msg = extract_error_message(e)
            if "geojson file not found" in error_msg:
                pass
            else:
                self.communication.bar_error(error_msg)
        except Exception as e:
            error_msg = f"Error: {e}"
            self.communication.bar_error(error_msg)
        return breach_geojson_cached_file_path

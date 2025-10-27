import os
from math import ceil
from operator import attrgetter
from time import sleep

from qgis.PyQt.QtCore import QSettings, QSize, Qt
from qgis.PyQt.QtGui import QIcon, QStandardItem, QStandardItemModel
from qgis.PyQt.QtWidgets import (
    QDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QSpinBox,
    QToolButton,
    QTreeView,
    QWidget,
)
from threedi_api_client.openapi import ApiException
from threedi_mi_utils import LocalSchematisation, list_local_schematisations

from threedi_models_simulations.constants import ICONS_DIR
from threedi_models_simulations.utils.file import unzip_archive
from threedi_models_simulations.utils.threedi_api import (
    download_schematisation_revision_raster,
    download_schematisation_revision_sqlite,
    extract_error_message,
    fetch_model_geopackage_download,
    fetch_model_gridadmin_download,
    fetch_schematisation_revision_models,
    fetch_schematisation_revisions_with_count,
    fetch_schematisations_with_count,
    get_download_file,
)


class SchematisationDownloadDialog(QDialog):
    """Dialog for schematisation download."""

    TABLE_LIMIT = 10

    def __init__(self, working_dir, threedi_api, organisations, communication, parent):
        super().__init__(parent)
        self.setWindowTitle("Download schematisation")
        self.resize(900, 650)

        gridLayout = QGridLayout(self)

        main_widget = QWidget()
        main_layout = QGridLayout(main_widget)
        main_widget.setMinimumSize(500, 300)

        self.schematisations_search_le = QLineEdit()
        self.schematisations_search_le.setPlaceholderText(
            "🔍 Search in schematisations"
        )
        main_layout.addWidget(self.schematisations_search_le, 0, 0, 1, 2)

        self.schematisations_tv = QTreeView()
        self.schematisations_tv.setEditTriggers(QTreeView.NoEditTriggers)
        self.schematisations_tv.setSortingEnabled(True)
        main_layout.addWidget(self.schematisations_tv, 1, 0, 1, 2)

        pagination_layout = QHBoxLayout()
        pagination_layout.addSpacerItem(
            QSpacerItem(200, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        )
        pb_schematisations_prev_page = QPushButton("<")
        pagination_layout.addWidget(pb_schematisations_prev_page)

        self.schematisations_page_sbox = QSpinBox()
        self.schematisations_page_sbox.setMinimum(1)
        self.schematisations_page_sbox.setSuffix(" / 1")
        self.schematisations_page_sbox.setAlignment(Qt.AlignCenter)
        pagination_layout.addWidget(self.schematisations_page_sbox)

        pb_schematisations_next_page = QPushButton(">")
        pagination_layout.addWidget(pb_schematisations_next_page)
        main_layout.addLayout(pagination_layout, 2, 0, 1, 2)

        label_layout = QHBoxLayout()
        label = QLabel("Available schematisation revisions")
        label_layout.addWidget(label)
        label_layout.addSpacerItem(
            QSpacerItem(200, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        )
        self.refresh_btn = QToolButton()
        self.refresh_btn.setEnabled(False)
        self.refresh_btn.setToolTip("Refresh")
        self.refresh_btn.setIcon(QIcon(os.path.join(ICONS_DIR, "refresh.svg")))
        self.refresh_btn.setIconSize(QSize(18, 18))
        label_layout.addWidget(self.refresh_btn)
        main_layout.addLayout(label_layout, 4, 0, 1, 2)

        self.revisions_tv = QTreeView()
        self.revisions_tv.setEditTriggers(QTreeView.NoEditTriggers)
        main_layout.addWidget(self.revisions_tv, 5, 0, 1, 2)

        revisions_pagination = QHBoxLayout()
        revisions_pagination.addSpacerItem(
            QSpacerItem(200, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        )
        self.pb_revisions_prev_page = QPushButton("<")
        revisions_pagination.addWidget(self.pb_revisions_prev_page)

        self.revisions_page_sbox = QSpinBox()
        self.revisions_page_sbox.setMinimum(1)
        self.revisions_page_sbox.setSuffix(" / 1")
        revisions_pagination.addWidget(self.revisions_page_sbox)

        self.pb_revisions_next_page = QPushButton(">")
        revisions_pagination.addWidget(self.pb_revisions_next_page)
        main_layout.addLayout(revisions_pagination, 6, 0, 1, 2)

        self.pbar_download = QProgressBar()
        self.pbar_download.setValue(0)
        main_layout.addWidget(self.pbar_download, 7, 0, 1, 2)

        buttons_layout = QHBoxLayout()
        self.pb_cancel = QPushButton("Cancel")
        self.pb_cancel.setMinimumSize(100, 30)
        buttons_layout.addWidget(self.pb_cancel)
        buttons_layout.addSpacerItem(
            QSpacerItem(200, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        )
        self.pb_download = QPushButton("Download")
        self.pb_download.setMinimumSize(100, 30)
        self.pb_download.setEnabled(False)
        buttons_layout.addWidget(self.pb_download)
        main_layout.addLayout(buttons_layout, 8, 0, 1, 2)
        gridLayout.addWidget(main_widget)

        self.working_dir = working_dir
        self.threedi_api = threedi_api
        self.organisations = organisations
        self.communication = communication

        self.schematisations = None
        self.revisions = None
        self.local_schematisations = list_local_schematisations(
            self.working_dir, use_config_for_revisions=False
        )
        self.downloaded_local_schematisation = None
        self.downloaded_geopackage_filepath = None
        self.tv_schematisations_model = QStandardItemModel()
        self.schematisations_tv.setModel(self.tv_schematisations_model)
        self.tv_revisions_model = QStandardItemModel()
        self.revisions_tv.setModel(self.tv_revisions_model)
        pb_schematisations_prev_page.clicked.connect(self.move_schematisations_backward)
        pb_schematisations_next_page.clicked.connect(self.move_schematisations_forward)
        self.schematisations_page_sbox.valueChanged.connect(self.fetch_schematisations)
        self.pb_revisions_prev_page.clicked.connect(self.move_revisions_backward)
        self.pb_revisions_next_page.clicked.connect(self.move_revisions_forward)
        self.revisions_page_sbox.valueChanged.connect(self.fetch_revisions)
        self.pb_download.clicked.connect(self.download_schematisation_revision)
        self.pb_cancel.clicked.connect(self.cancel_download_schematisation_revision)
        self.schematisations_search_le.returnPressed.connect(
            self.search_schematisations
        )
        self.schematisations_tv.selectionModel().selectionChanged.connect(
            self.toggle_fetch_revisions
        )
        self.schematisations_tv.selectionModel().selectionChanged.connect(
            self.fetch_revisions
        )
        self.revisions_tv.selectionModel().selectionChanged.connect(
            self.toggle_download_schematisation_revision
        )
        self.refresh_btn.clicked.connect(self.fetch_revisions)

        self.fetch_schematisations()

    def toggle_fetch_revisions(self):
        """Toggle fetch revisions button if any schematisation is selected."""
        selection_model = self.schematisations_tv.selectionModel()
        if selection_model.hasSelection():
            self.refresh_btn.setEnabled(True)
        else:
            self.refresh_btn.setDisabled(True)
        self.tv_revisions_model.clear()
        self.revisions_page_sbox.setMaximum(1)
        self.revisions_page_sbox.setSuffix(" / 1")
        self.toggle_download_schematisation_revision()

    def toggle_download_schematisation_revision(self):
        """Toggle download button if any schematisation revision is selected."""
        selection_model = self.revisions_tv.selectionModel()
        if selection_model.hasSelection():
            self.pb_download.setEnabled(True)
        else:
            self.pb_download.setDisabled(True)

    def move_schematisations_backward(self):
        """Moving to the previous schematisations results page."""
        self.schematisations_page_sbox.setValue(
            self.schematisations_page_sbox.value() - 1
        )

    def move_schematisations_forward(self):
        """Moving to the next schematisations results page."""
        self.schematisations_page_sbox.setValue(
            self.schematisations_page_sbox.value() + 1
        )

    def search_schematisations(self):
        """Method used for searching schematisations with text typed withing search bar."""
        self.schematisations_page_sbox.valueChanged.disconnect(
            self.fetch_schematisations
        )
        self.schematisations_page_sbox.setValue(1)
        self.schematisations_page_sbox.valueChanged.connect(self.fetch_schematisations)
        self.fetch_schematisations()
        self.toggle_fetch_revisions()

    def move_revisions_backward(self):
        """Moving to the previous revisions results page."""
        self.revisions_page_sbox.setValue(self.revisions_page_sbox.value() - 1)

    def move_revisions_forward(self):
        """Moving to the next revisions results page."""
        self.revisions_page_sbox.setValue(self.revisions_page_sbox.value() + 1)

    def fetch_schematisations(self):
        """Fetching schematisation list."""
        try:
            offset = (self.schematisations_page_sbox.value() - 1) * self.TABLE_LIMIT
            text = self.schematisations_search_le.text()
            schematisations, schematisations_count = fetch_schematisations_with_count(
                self.threedi_api,
                limit=self.TABLE_LIMIT,
                offset=offset,
                name_contains=text,
            )
            pages_nr = ceil(schematisations_count / self.TABLE_LIMIT) or 1
            self.schematisations_page_sbox.setMaximum(pages_nr)
            self.schematisations_page_sbox.setSuffix(f" / {pages_nr}")
            self.tv_schematisations_model.clear()
            header = [
                "Schematisation name",
                "Description",
                "Owner",
                "Created by",
                "Last updated",
            ]
            self.tv_schematisations_model.setHorizontalHeaderLabels(header)
            for schematisation in sorted(
                schematisations,
                key=lambda s: s.last_updated.timestamp() if s.last_updated else 1,
                reverse=True,
            ):
                name_item = QStandardItem(schematisation.name)
                name_item.setData(schematisation, role=Qt.UserRole)
                try:
                    description_item = QStandardItem(schematisation.meta["description"])
                except (KeyError, TypeError):
                    description_item = QStandardItem("")
                organisation = self.organisations[schematisation.owner]
                owner_item = QStandardItem(organisation.name)
                created_by_item = QStandardItem(
                    f"{schematisation.created_by_first_name} {schematisation.created_by_last_name}"
                )
                last_updated_item = QStandardItem(
                    schematisation.last_updated.strftime("%d-%m-%Y")
                    if schematisation.last_updated
                    else ""
                )
                self.tv_schematisations_model.appendRow(
                    [
                        name_item,
                        description_item,
                        owner_item,
                        created_by_item,
                        last_updated_item,
                    ]
                )
            for i in range(len(header)):
                self.schematisations_tv.resizeColumnToContents(i)
            self.schematisations = schematisations
        except ApiException as e:
            self.close()
            error_msg = extract_error_message(e)
            self.communication.show_error(error_msg, self.parent, "Error")
        except Exception as e:
            self.close()
            error_msg = f"Error: {e}"
            self.communication.show_error(error_msg, self.parent, "Error")

    def fetch_revisions(self):
        """Fetching schematisation revisions list."""
        try:
            offset = (self.revisions_page_sbox.value() - 1) * self.TABLE_LIMIT
            selected_schematisation = self.get_selected_schematisation()
            schematisation_pk = selected_schematisation.id
            revisions, revisions_count = fetch_schematisation_revisions_with_count(
                self.threedi_api,
                schematisation_pk,
                limit=self.TABLE_LIMIT,
                offset=offset,
            )
            pages_nr = ceil(revisions_count / self.TABLE_LIMIT) or 1
            self.revisions_page_sbox.setMaximum(pages_nr)
            self.revisions_page_sbox.setSuffix(f" / {pages_nr}")
            self.tv_revisions_model.clear()
            header = [
                "Revision number",
                "Commit message",
                "Committed by",
                "Commit date",
            ]
            self.tv_revisions_model.setHorizontalHeaderLabels(header)
            for revision in revisions:
                number_item = QStandardItem(str(revision.number))
                number_item.setData(revision, role=Qt.UserRole)
                commit_message_item = QStandardItem(revision.commit_message or "")
                commit_user_item = QStandardItem(
                    f"{revision.commit_first_name} {revision.commit_last_name}"
                )
                commit_date = (
                    revision.commit_date.strftime("%d-%m-%Y")
                    if revision.commit_date
                    else ""
                )
                commit_date_item = QStandardItem(commit_date)
                self.tv_revisions_model.appendRow(
                    [
                        number_item,
                        commit_message_item,
                        commit_user_item,
                        commit_date_item,
                    ]
                )
            for i in range(len(header)):
                self.revisions_tv.resizeColumnToContents(i)
            self.revisions = revisions
        except ApiException as e:
            error_msg = extract_error_message(e)
            self.communication.show_error(error_msg)
        except Exception as e:
            self.communication.show_error(f"Error: {e}")

    def get_selected_schematisation(self):
        """Get currently selected schematisation."""
        index = self.schematisations_tv.currentIndex()
        if index.isValid():
            current_row = index.row()
            name_item = self.tv_schematisations_model.item(current_row, 0)
            selected_schematisation = name_item.data(Qt.UserRole)
        else:
            selected_schematisation = None
        return selected_schematisation

    def get_selected_revision(self):
        """Get currently selected revision."""
        index = self.revisions_tv.currentIndex()
        if index.isValid():
            current_row = index.row()
            name_item = self.tv_revisions_model.item(current_row, 0)
            selected_revision = name_item.data(Qt.UserRole)
        else:
            selected_revision = None
        return selected_revision

    def download_schematisation_revision(self):
        """Downloading selected schematisation revision."""
        selected_schematisation = self.get_selected_schematisation()
        selected_revision = self.get_selected_revision()
        self.download_required_files(selected_schematisation, selected_revision, False)
        if self.downloaded_local_schematisation:
            self.close()

    def download_required_files(
        self, schematisation, revision, is_latest_revision, external_progress_bar=None
    ):
        """Download required schematisation revision files."""
        try:
            progress_bar = (
                external_progress_bar if external_progress_bar else self.pbar_download
            )
            schematisation_pk = schematisation.id
            schematisation_name = schematisation.name
            revision_pk = revision.id
            revision_number = revision.number
            revision_sqlite = revision.sqlite
            if not is_latest_revision:
                latest_online_revision = (
                    max([rev.number for rev in self.revisions])
                    if self.revisions
                    else None
                )
                is_latest_revision = revision_number == latest_online_revision
            try:
                local_schematisation = self.local_schematisations[schematisation_pk]
                local_schematisation_present = True
            except KeyError:
                local_schematisation = LocalSchematisation(
                    self.working_dir,
                    schematisation_pk,
                    schematisation_name,
                    create=True,
                )
                self.local_schematisations[schematisation_pk] = local_schematisation
                local_schematisation_present = False

            def decision_tree():
                replace, store, cancel = "Replace", "Store", "Cancel"
                title = "Pick action"
                question = (
                    f"Replace local WIP or store as a revision {revision_number}?"
                )
                picked_action_name = self.communication.custom_ask(
                    self, title, question, replace, store, cancel
                )
                if picked_action_name == replace:
                    # Replace
                    local_schematisation.set_wip_revision(revision_number)
                    schema_db_dir = local_schematisation.wip_revision.schematisation_dir
                elif picked_action_name == store:
                    # Store as a separate revision
                    if revision_number in local_schematisation.revisions:
                        question = (
                            f"Replace local revision {revision_number} or Cancel?"
                        )
                        picked_action_name = self.communication.custom_ask(
                            self, title, question, "Replace", "Cancel"
                        )
                        if picked_action_name == "Replace":
                            local_revision = local_schematisation.add_revision(
                                revision_number
                            )
                            schema_db_dir = local_revision.schematisation_dir
                        else:
                            schema_db_dir = None
                    else:
                        local_revision = local_schematisation.add_revision(
                            revision_number
                        )
                        schema_db_dir = local_revision.schematisation_dir
                else:
                    schema_db_dir = None
                return schema_db_dir

            if local_schematisation_present:
                if is_latest_revision:
                    if local_schematisation.wip_revision is None:
                        # WIP not exist
                        local_schematisation.set_wip_revision(revision_number)
                        schematisation_db_dir = (
                            local_schematisation.wip_revision.schematisation_dir
                        )
                    else:
                        # WIP exist
                        schematisation_db_dir = decision_tree()
                else:
                    schematisation_db_dir = decision_tree()
            else:
                local_schematisation.set_wip_revision(revision_number)
                schematisation_db_dir = (
                    local_schematisation.wip_revision.schematisation_dir
                )

            if not schematisation_db_dir:
                return

            sqlite_download = download_schematisation_revision_sqlite(
                self.threedi_api, schematisation_pk, revision_pk
            )
            revision_models = fetch_schematisation_revision_models(
                self.threedi_api, schematisation_pk, revision_pk
            )
            rasters_downloads = []
            for raster_file in revision.rasters or []:
                raster_download = download_schematisation_revision_raster(
                    self.threedi_api, raster_file.id, schematisation_pk, revision_pk
                )
                rasters_downloads.append((raster_file.name, raster_download))
            number_of_steps = len(rasters_downloads) + 1

            gridadmin_file, gridadmin_download = (None, None)
            gridadmin_file_gpkg, gridadmin_download_gpkg = (None, None)
            ignore_gridadmin_error_messages = [
                "Gridadmin file not found",
                "Geopackage file not found",
            ]
            for revision_model in sorted(
                revision_models, key=attrgetter("id"), reverse=True
            ):
                try:
                    gridadmin_file, gridadmin_download = fetch_model_gridadmin_download(
                        self.threedi_api, revision_model.id
                    )
                    if gridadmin_download is not None:
                        gridadmin_file_gpkg, gridadmin_download_gpkg = (
                            fetch_model_geopackage_download(
                                self.threedi_api, revision_model.id
                            )
                        )
                        number_of_steps += 1
                        break
                except ApiException as e:
                    error_msg = extract_error_message(e)
                    if not any(
                        ignore_error_msg in error_msg
                        for ignore_error_msg in ignore_gridadmin_error_messages
                    ):
                        raise
            if revision_number not in local_schematisation.revisions:
                local_schematisation.add_revision(revision_number)
            zip_filepath = os.path.join(
                schematisation_db_dir, revision_sqlite.file.filename
            )
            progress_bar.setMaximum(number_of_steps)
            current_progress = 0
            progress_bar.setValue(current_progress)
            get_download_file(sqlite_download, zip_filepath)
            content_list = unzip_archive(zip_filepath)
            os.remove(zip_filepath)
            schematisation_db_file = content_list[0]
            current_progress += 1
            progress_bar.setValue(current_progress)
            if gridadmin_download is not None:
                grid_filepath = os.path.join(
                    local_schematisation.revisions[revision_number].grid_dir,
                    gridadmin_file.filename,
                )
                get_download_file(gridadmin_download, grid_filepath)
                current_progress += 1
                progress_bar.setValue(current_progress)
            if gridadmin_download_gpkg is not None:
                gpkg_filepath = os.path.join(
                    local_schematisation.revisions[revision_number].grid_dir,
                    gridadmin_file_gpkg.filename,
                )
                get_download_file(gridadmin_download_gpkg, gpkg_filepath)
                current_progress += 1
                progress_bar.setValue(current_progress)
            for raster_filename, raster_download in rasters_downloads:
                raster_filepath = os.path.join(
                    schematisation_db_dir, "rasters", raster_filename
                )
                get_download_file(raster_download, raster_filepath)
                current_progress += 1
                progress_bar.setValue(current_progress)
            self.downloaded_local_schematisation = local_schematisation
            expected_geopackage_path = os.path.join(
                schematisation_db_dir, schematisation_db_file
            )
            if expected_geopackage_path.lower().endswith(".sqlite"):
                expected_geopackage_path = (
                    expected_geopackage_path.rsplit(".", 1)[0] + ".gpkg"
                )
            if os.path.isfile(expected_geopackage_path):
                self.downloaded_geopackage_filepath = expected_geopackage_path
            sleep(1)
            settings = QSettings()
            settings.setValue(
                "threedi/last_schematisation_folder", schematisation_db_dir
            )
            msg = f"Schematisation '{schematisation_name} (revision {revision_number})' downloaded!"
            self.communication.bar_info(msg)
        except ApiException as e:
            error_msg = extract_error_message(e)
            self.communication.show_error(error_msg)
        except Exception as e:
            self.communication.show_error(f"Error: {e}")

    def cancel_download_schematisation_revision(self):
        self.close()

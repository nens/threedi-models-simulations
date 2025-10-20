import os
import shutil
from datetime import datetime

from dateutil.relativedelta import relativedelta
from qgis.PyQt.QtCore import (
    QModelIndex,
    QSettings,
    QSize,
    QSortFilterProxyModel,
    Qt,
    QThreadPool,
    pyqtSignal,
)
from qgis.PyQt.QtGui import QIcon, QStandardItem, QStandardItemModel
from qgis.PyQt.QtWidgets import (
    QDialog,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QToolButton,
    QTreeView,
)
from threedi_api_client.openapi import ApiException
from threedi_mi_utils import (
    LocalRevision,
    LocalSchematisation,
    bypass_max_path_limit,
    list_local_schematisations,
)

from threedi_models_simulations.constants import (
    API_DATETIME_FORMAT,
    ICONS_DIR,
    USER_DATETIME_FORMAT,
)
from threedi_models_simulations.threedi_api_utils import (
    expiration_time,
    extract_error_message,
    fetch_model,
    fetch_model_geopackage_download,
    fetch_model_gridadmin_download,
    fetch_simulation,
    fetch_simulation_downloads,
)
from threedi_models_simulations.utils import translate_illegal_chars
from threedi_models_simulations.widgets.utils.download_progress_delegate import (
    DownloadProgressDelegate,
)
from threedi_models_simulations.workers.download import DownloadProgressWorker

SIMULATION_NAME_IDX = 0
EXPIRES_COLUMN_IDX = 1
USERNAME_COLUMN_IDX = 2
PROGRESS_COLUMN_IDX = 3
MAX_THREAD_COUNT = 4


class SortFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, parent):
        super().__init__(parent)

    def lessThan(self, left: QModelIndex, right: QModelIndex):
        leftData = self.sourceModel().data(left)
        rightData = self.sourceModel().data(right)
        if left.column() in [EXPIRES_COLUMN_IDX]:
            left_int = int(leftData.split()[0])
            right_int = int(rightData.split()[0])
            return left_int < right_int
        else:
            return leftData < rightData


class SimulationResultDialog(QDialog):
    """Dialog with methods for handling simulations results."""

    fetch_request = pyqtSignal()

    def __init__(self, threedi_api, user_info, communication, workdir, parent):
        super().__init__(parent)

        self.setWindowModality(Qt.ApplicationModal)
        self.resize(850, 600)
        self.setWindowTitle("Results")

        self.threedi_api = threedi_api
        self.communication = communication
        self.work_dir = workdir

        gridLayout = QGridLayout(self)
        gridLayout.addWidget(QLabel("Finished simulations", self), 0, 0)

        self.username_filter_grp = QGroupBox("Filter by username", self)
        self.username_filter_grp.setCheckable(True)
        self.username_filter_grp.setChecked(False)
        gridLayout_3 = QGridLayout(self.username_filter_grp)

        self.first_name_le = QLineEdit(self.username_filter_grp)
        self.last_name_le = QLineEdit(self.username_filter_grp)

        gridLayout_3.addWidget(QLabel("First name:", self.username_filter_grp), 0, 0)
        gridLayout_3.addWidget(self.first_name_le, 0, 1)
        gridLayout_3.addWidget(QLabel("Last name:", self.username_filter_grp), 0, 2)
        gridLayout_3.addWidget(self.last_name_le, 0, 3)
        gridLayout.addWidget(self.username_filter_grp, 1, 0, 1, 5)

        self.tv_finished_sim_tree = QTreeView(self)
        self.tv_finished_sim_tree.setEditTriggers(QTreeView.NoEditTriggers)
        self.tv_finished_sim_tree.setSelectionMode(QTreeView.SingleSelection)
        self.tv_finished_sim_tree.setSortingEnabled(True)
        gridLayout.addWidget(self.tv_finished_sim_tree, 2, 0, 1, 5)

        horizontalLayout_2 = QHBoxLayout()

        spacerItem1 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        horizontalLayout_2.addItem(spacerItem1)

        self.label_last_updated = QLabel("Last updated: never", self)
        horizontalLayout_2.addWidget(self.label_last_updated)

        self.refresh_btn = QToolButton(self)
        self.refresh_btn.setToolTip("Refresh")
        self.refresh_btn.setIcon(QIcon(os.path.join(ICONS_DIR, "refresh.svg")))
        self.refresh_btn.setIconSize(QSize(18, 18))
        horizontalLayout_2.addWidget(self.refresh_btn)

        gridLayout.addLayout(horizontalLayout_2, 3, 0, 1, 5)

        gridLayout_2 = QGridLayout()
        gridLayout_2.setContentsMargins(0, 0, 0, 0)

        self.pb_cancel = QPushButton("Cancel", self)
        self.pb_cancel.setMinimumSize(125, 30)
        self.pb_cancel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        gridLayout_2.addWidget(self.pb_cancel, 0, 0)

        spacerItem2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        gridLayout_2.addItem(spacerItem2, 0, 1)

        self.pb_download = QPushButton("Download", self)
        self.pb_download.setMinimumSize(125, 30)
        self.pb_download.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        gridLayout_2.addWidget(self.pb_download, 0, 2)

        gridLayout.addLayout(gridLayout_2, 4, 0, 1, 5)

        self.setTabOrder(self.tv_finished_sim_tree, self.refresh_btn)
        self.setTabOrder(self.refresh_btn, self.pb_cancel)
        self.setTabOrder(self.pb_cancel, self.pb_download)

        self.first_name_le.setText(user_info["first_name"])
        self.last_name_le.setText(user_info["last_name"])

        self.download_results_pool = QThreadPool()
        self.download_results_pool.setMaxThreadCount(MAX_THREAD_COUNT)
        self.finished_simulations = {}
        self.download_progress_bars = {}
        self.running_downloads = set()
        self.tv_model = None
        self.setup_view_model()

        self.pb_cancel.clicked.connect(self.close)
        self.pb_download.clicked.connect(self.download_results)
        self.tv_finished_sim_tree.selectionModel().selectionChanged.connect(
            self.toggle_refresh_results
        )
        self.tv_finished_sim_tree.doubleClicked.connect(self.download_results)
        self.refresh_btn.clicked.connect(self.refresh_finished_simulations_list)
        self.username_filter_grp.toggled.connect(self.filter_finished_simulations_list)
        self.first_name_le.textChanged.connect(self.filter_finished_simulations_list)
        self.last_name_le.textChanged.connect(self.filter_finished_simulations_list)

    def refresh_last_updated_label(self):
        """Refresh last update datetime label."""
        self.label_last_updated.setText(
            f"Last updated: {datetime.now().strftime(USER_DATETIME_FORMAT)}"
        )

    def setup_view_model(self):
        """Setting up model and columns for TreeView."""
        self.tv_model = QStandardItemModel(0, 3, self)
        # ProxyModel is a wrapper around the source model, but with filtering/sorting
        self.proxy_model = SortFilterProxyModel(self)
        self.proxy_model.setSourceModel(self.tv_model)
        delegate = DownloadProgressDelegate(self.tv_finished_sim_tree)
        self.tv_finished_sim_tree.setItemDelegateForColumn(
            PROGRESS_COLUMN_IDX, delegate
        )
        self.tv_model.setHorizontalHeaderLabels(
            ["Simulation name", "Expires", "Username", "Download progress"]
        )
        self.tv_finished_sim_tree.setModel(self.proxy_model)

    def refresh_finished_simulations_list(self):
        """Refresh finished simulation results list."""
        self.tv_finished_sim_tree.selectionModel().selectionChanged.disconnect(
            self.toggle_refresh_results
        )

        # TODO
        # self.plugin_dock.simulations_progresses_sentinel.simulation_finished.disconnect(self.update_finished_list)

        self.tv_model.clear()
        self.finished_simulations.clear()
        self.download_progress_bars.clear()
        self.running_downloads.clear()
        self.setup_view_model()

        # TODO
        # self.plugin_dock.simulations_progresses_sentinel.simulation_finished.connect(self.update_finished_list)
        self.tv_finished_sim_tree.selectionModel().selectionChanged.connect(
            self.toggle_refresh_results
        )

        # TODO
        # self.plugin_dock.simulations_progresses_sentinel.fetch_finished_simulations()
        self.fetch_request.emit()

        self.communication.bar_info("Finished simulation results reloaded!")

    def toggle_refresh_results(self):
        """Toggle refresh if any simulation results are downloading."""
        if self.download_results_pool.activeThreadCount() == 0:
            self.refresh_btn.setEnabled(True)
            self.refresh_btn.setToolTip("Refresh")
        else:
            self.refresh_btn.setDisabled(True)
            self.refresh_btn.setToolTip("Refreshing disabled while downloading")

    def add_finished_simulation_to_model(self, sim_id, sim_data):
        """Method for adding information about finished simulation to the model."""
        sim_name = sim_data["name"]
        sim_name_item = QStandardItem(f"{sim_name} ({sim_id})")
        sim_name_item.setData(sim_id, Qt.UserRole)
        create_str = sim_data["date_created"]
        create_datetime = datetime.strptime(create_str, API_DATETIME_FORMAT)
        delta = relativedelta(create_datetime, expiration_time())
        expires_item = QStandardItem(f"{delta.days} day(s)")
        simulation_user_first_name = sim_data["simulation_user_first_name"]
        simulation_user_last_name = sim_data["simulation_user_last_name"]
        username_item = QStandardItem(
            f"{simulation_user_first_name} {simulation_user_last_name}"
        )
        username_item.setData(
            (simulation_user_first_name, simulation_user_last_name), Qt.UserRole
        )
        progress_item = QStandardItem()
        progress_item.setData(-1, Qt.UserRole)
        self.tv_model.insertRow(
            0, [sim_name_item, expires_item, username_item, progress_item]
        )
        self.finished_simulations[sim_id] = sim_data
        self.download_progress_bars[sim_id] = progress_item

    def update_finished_list(self, finished_simulations_data):
        """Update finished simulations list."""
        for sim_id, sim_data in sorted(finished_simulations_data.items()):
            if sim_id not in self.finished_simulations:
                self.add_finished_simulation_to_model(sim_id, sim_data)
        self.tv_finished_sim_tree.resizeColumnToContents(SIMULATION_NAME_IDX)
        self.refresh_last_updated_label()
        self.filter_finished_simulations_list()

    def filter_finished_simulations_list(self):
        """Filter finished simulations list."""
        filter_first_name = self.first_name_le.text().lower()
        filter_last_name = self.last_name_le.text().lower()
        row_count = self.proxy_model.rowCount()
        root_model_index = self.tv_model.invisibleRootItem().index()
        if self.username_filter_grp.isChecked():
            for row in range(row_count):
                model_index = self.proxy_model.index(row, USERNAME_COLUMN_IDX)
                first_name, last_name = self.proxy_model.data(model_index, Qt.UserRole)
                first_name_match, last_name_match = True, True
                if filter_first_name:
                    if filter_first_name not in first_name.lower():
                        first_name_match = False
                if filter_last_name:
                    if filter_last_name not in last_name.lower():
                        last_name_match = False
                hide_row = not all([first_name_match, last_name_match])
                self.tv_finished_sim_tree.setRowHidden(row, root_model_index, hide_row)
        else:
            for row in range(row_count):
                self.tv_finished_sim_tree.setRowHidden(row, root_model_index, False)

    def on_download_progress_update(self, percentage, sim_id):
        """Update download progress bar."""
        progress_item = self.download_progress_bars[sim_id]
        progress_item.setData(percentage, Qt.UserRole)
        if percentage == 0:
            row = progress_item.index().row()
            name_text = self.tv_model.item(row, 0).text()
            msg = f"Downloading results of {name_text} started!"
            self.communication.bar_info(msg)

    def on_download_finished_success(self, msg, results_dir, sim_id):
        """Reporting finish successfully status and closing download thread."""
        self.running_downloads.remove(sim_id)
        self.communication.bar_info(msg, log_text_color=Qt.darkGreen)

        grid_file_names = ["gridadmin.h5", "gridadmin.gpkg"]
        grid_dir = os.path.join(os.path.dirname(os.path.dirname(results_dir)), "grid")
        if os.path.exists(grid_dir):
            for grid_file_name in grid_file_names:
                grid_file = os.path.join(results_dir, grid_file_name)
                if os.path.exists(grid_file):
                    grid_file_copy = os.path.join(grid_dir, grid_file_name)
                    shutil.copyfile(
                        grid_file, bypass_max_path_limit(grid_file_copy, is_file=True)
                    )
        self.toggle_refresh_results()

    def on_download_finished_failed(self, msg, sim_id):
        """Reporting failure and closing download thread."""
        self.running_downloads.remove(sim_id)
        self.communication.bar_error(msg, log_text_color=Qt.red)
        self.toggle_refresh_results()

    def pick_results_destination_dir(self):
        """Pick folder where results will be written to."""
        last_folder = QSettings().value(
            "threedi/last_results_folder", self.work_dir, type=str
        )
        directory = QFileDialog.getExistingDirectory(
            self, "Select Results Directory", last_folder
        )
        if len(directory) == 0:
            return None
        QSettings().setValue("threedi/last_results_folder", directory)
        return directory

    def download_results(self):
        """Download simulation results files."""
        current_index = self.tv_finished_sim_tree.currentIndex()
        if not current_index.isValid():
            return
        current_row = current_index.row()
        current_sim_id_index = self.proxy_model.index(current_row, 0)
        sim_id = self.proxy_model.data(current_sim_id_index, Qt.UserRole)
        if sim_id in self.running_downloads:
            self.communication.bar_warn(
                "The selected results are already being downloaded!"
            )
            return
        local_schematisations = list_local_schematisations(
            self.work_dir, use_config_for_revisions=False
        )
        try:
            simulation = fetch_simulation(self.threedi_api, sim_id)
            simulation_name = simulation.name
            simulation_model_id = int(simulation.threedimodel_id)
            results_dir, gridadmin_downloads, gridadmin_downloads_gpkg = (
                None,
                None,
                None,
            )
            try:
                model_3di = fetch_model(self.threedi_api, simulation_model_id)
                gridadmin_downloads = fetch_model_gridadmin_download(
                    self.threedi_api, simulation_model_id
                )
                if model_3di.schematisation_id:
                    model_schematisation_id = model_3di.schematisation_id
                    model_schematisation_name = model_3di.schematisation_name
                    model_revision_number = model_3di.revision_number
                    try:
                        local_schematisation = local_schematisations[
                            model_schematisation_id
                        ]
                    except KeyError:
                        local_schematisation = LocalSchematisation(
                            self.work_dir,
                            model_schematisation_id,
                            model_schematisation_name,
                            create=True,
                        )
                    try:
                        local_revision = local_schematisation.revisions[
                            model_revision_number
                        ]
                    except KeyError:
                        local_revision = LocalRevision(
                            local_schematisation, model_revision_number
                        )
                        local_revision.make_revision_structure()
                    results_dir = local_revision.results_dir
                else:
                    warn_msg = (
                        "The 3Di model to which these results belong was uploaded with Tortoise and does not "
                        "belong to any schematisation. Therefore, it cannot be determined to which "
                        "schematisation the results should be downloaded.\n\nPlease select a directory to save "
                        "the result files to."
                    )
                    self.communication.show_warn(warn_msg, self, "Warning")
                    results_dir = self.pick_results_destination_dir()
                    if not results_dir:
                        self.communication.show_warn(warn_msg, self, "Warning")
                        return
                gridadmin_downloads_gpkg = fetch_model_geopackage_download(
                    self.threedi_api, simulation_model_id
                )
            except ApiException as e:
                error_msg = extract_error_message(e)
                if e.status == 404:
                    warn_msg = (
                        "The 3Di model to which these results belong is owned by an organisation for which "
                        "you do not have sufficient rights. Therefore, you cannot download the computational "
                        "grid (gridadmin.h5) and it cannot be determined to which schematisation the results "
                        "should be downloaded.\n\nContact the servicedesk to obtain access rights to the "
                        "organisation that owns the 3Di model.\n\nPlease select a directory to save the result"
                        " files to."
                    )
                    self.communication.show_warn(warn_msg, self, "Warning")
                    results_dir = self.pick_results_destination_dir()
                elif "Geopackage file not found" in error_msg:
                    pass
                else:
                    raise e
            if not results_dir:
                return
            simulation_subdirectory = translate_illegal_chars(
                f"{simulation_name} ({sim_id})"
            )
            simulation_subdirectory_path = os.path.join(
                results_dir, simulation_subdirectory
            )
            downloads = fetch_simulation_downloads(self.threedi_api, sim_id)
            if gridadmin_downloads is not None:
                downloads.append(gridadmin_downloads)
            if gridadmin_downloads_gpkg is not None:
                downloads.append(gridadmin_downloads_gpkg)
            downloads.sort(key=lambda x: x[-1].size)
        except ApiException as e:
            error_msg = extract_error_message(e)
            self.communication.show_error(error_msg, self, "Error")
            return
        except Exception as e:
            error_msg = f"Error: {e}"
            self.communication.show_error(error_msg, self, "Error")
            return
        download_worker = DownloadProgressWorker(
            simulation, downloads, simulation_subdirectory_path
        )
        download_worker.signals.thread_finished.connect(
            self.on_download_finished_success
        )
        download_worker.signals.download_failed.connect(
            self.on_download_finished_failed
        )
        download_worker.signals.download_progress.connect(
            self.on_download_progress_update
        )
        self.download_results_pool.start(download_worker)
        self.running_downloads.add(sim_id)
        self.toggle_refresh_results()

import os
from datetime import datetime

from qgis.core import Qgis, QgsApplication, QgsMessageLog
from qgis.PyQt.QtCore import QObject, Qt, QThreadPool, pyqtSignal
from qgis.PyQt.QtGui import QAction, QColor, QIcon, QStandardItem, QStandardItemModel
from qgis.PyQt.QtWidgets import (
    QDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMenu,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QTreeView,
)
from threedi_api_client.openapi import ApiException

from threedi_models_simulations.constants import ICONS_DIR
from threedi_models_simulations.threedi_api_utils import (
    create_simulation_action,
    extract_error_message,
    fetch_simulation_events,
    fetch_simulation_lizard_postprocessing_overview,
    fetch_simulation_settings_overview,
)
from threedi_models_simulations.widgets.model_selection_dialog import (
    ModelSelectionDialog,
)
from threedi_models_simulations.widgets.simulation_results_dialog import (
    API_DATETIME_FORMAT,
    USER_DATETIME_FORMAT,
)
from threedi_models_simulations.widgets.simulation_wizard import SimulationWizard
from threedi_models_simulations.widgets.utils.simulation_progress_delegate import (
    PROGRESS_ROLE,
    SimulationProgressDelegate,
)
from threedi_models_simulations.workers.runner import SimulationRunner
from threedi_models_simulations.workers.simulations import SimulationStatusName


class SimulationOverviewDialog(QDialog):
    """Dialog with methods for handling running simulations."""

    PROGRESS_COLUMN_IDX = 1
    MAX_THREAD_COUNT = 1

    refresh_requested = pyqtSignal()

    def __init__(
        self,
        communication,
        threedi_api,
        current_user,
        current_local_schematisation,
        organisations,
        working_dir,
        parent,
    ):
        super().__init__(parent)

        self.setWindowModality(Qt.ApplicationModal)
        self.setMinimumSize(750, 500)
        self.resize(750, 500)
        self.setWindowTitle("Running simulations")

        gridLayout = QGridLayout(self)

        self.tv_sim_tree = QTreeView(self)
        self.tv_sim_tree.setEditTriggers(QTreeView.NoEditTriggers)
        self.tv_sim_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tv_sim_tree.customContextMenuRequested.connect(self.menuRequested)
        gridLayout.addWidget(self.tv_sim_tree, 0, 1, 1, 3)

        self.horizontalLayout = QHBoxLayout()

        self.refresh_btn = QPushButton(
            QIcon(os.path.join(ICONS_DIR, "refresh.svg")), "Update table", self
        )
        self.refresh_btn.setMinimumSize(0, 30)
        self.horizontalLayout.addWidget(self.refresh_btn)

        self.label_last_updated = QLabel("Last updated: never", self)
        self.horizontalLayout.addWidget(self.label_last_updated)

        spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacer)

        self.pb_new_sim = QPushButton("New Simulation", self)
        self.pb_new_sim.setMinimumSize(0, 30)
        self.pb_new_sim.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.horizontalLayout.addWidget(self.pb_new_sim)

        gridLayout.addLayout(self.horizontalLayout, 1, 1, 1, 3)

        self.setTabOrder(self.tv_sim_tree, self.refresh_btn)
        self.setTabOrder(self.refresh_btn, self.pb_new_sim)

        self.threedi_api = threedi_api
        self.current_user = current_user
        self.communication = communication
        self.current_local_schematisation = current_local_schematisation
        self.organisations = organisations
        self.working_dir = working_dir

        self.simulation_runner_pool = QThreadPool()
        self.simulation_runner_pool.setMaxThreadCount(self.MAX_THREAD_COUNT)
        self.simulation_init_wizard = None
        self.simulation_wizard = None
        self.running_simulations = {}
        self.last_progresses = {}
        self.simulations_without_progress = set()
        self.tv_model = None
        self.setup_view_model()

        self.pb_new_sim.clicked.connect(self.new_wizard_init)
        self.refresh_btn.clicked.connect(self.refresh_running_simulations_list)

    def exec(self):
        self.refresh_running_simulations_list()
        return super().exec()

    def setup_view_model(self):
        """Setting up model and columns for TreeView."""
        delegate = SimulationProgressDelegate(self.tv_sim_tree)
        self.tv_sim_tree.setItemDelegateForColumn(self.PROGRESS_COLUMN_IDX, delegate)
        self.tv_model = QStandardItemModel(0, 4)
        self.tv_model.setHorizontalHeaderLabels(
            ["Simulation name", "Progress", "User", "Created at"]
        )
        self.tv_sim_tree.setModel(self.tv_model)

    def refresh_last_updated_label(self):
        """Refresh last update datetime label."""
        self.label_last_updated.setText(
            f"Last updated: {datetime.now().strftime(USER_DATETIME_FORMAT)}"
        )

    def menuRequested(self, pos):
        index = self.tv_sim_tree.indexAt(pos)
        menu = QMenu(self)
        action_stop = QAction("Stop simulation", self)
        action_stop.triggered.connect(
            lambda _, sel_index=index: self.stop_simulation(sel_index)
        )
        menu.addAction(action_stop)
        menu.popup(self.tv_sim_tree.viewport().mapToGlobal(pos))

    def refresh_running_simulations_list(self):
        """Refresh running simulations list."""
        # Is this necessary?
        # self.plugin_dock.simulations_progresses_sentinel.progresses_fetched.disconnect(self.update_progress)
        # self.plugin_dock.simulations_progresses_sentinel.stop_listening(be_quite=True)

        self.tv_model.clear()
        self.running_simulations.clear()
        self.last_progresses.clear()
        self.simulations_without_progress.clear()
        self.setup_view_model()

        # Is this necessary?
        # self.plugin_dock.simulations_progresses_sentinel.progresses_fetched.connect(self.update_progress)
        # self.plugin_dock.simulations_progresses_sentinel.start_listening()
        self.refresh_requested.emit()

    def add_simulation_to_model(self, sim_id, sim_data):
        """Method for adding simulation to the model."""
        sim_name = sim_data["name"]
        sim_name_item = QStandardItem(f"{sim_name} ({sim_id})")
        sim_name_item.setData(sim_id, Qt.UserRole)
        user_name = sim_data["user_name"]
        user_item = QStandardItem(user_name)
        status_name = sim_data["status"]
        progress_percentage = sim_data["progress"]
        progress_item = QStandardItem()
        created_at = sim_data["date_created"]
        created_date = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        formatted_date = created_date.strftime("%B %d, %Y")
        date_item = QStandardItem(formatted_date)
        progress_item.setData((status_name, progress_percentage), PROGRESS_ROLE)
        self.tv_model.appendRow([sim_name_item, progress_item, user_item, date_item])
        self.running_simulations[sim_id] = sim_data
        for i in range(self.PROGRESS_COLUMN_IDX):
            self.tv_sim_tree.resizeColumnToContents(i)

    def update_progress(self, running_simulations_data):
        """Updating progress bars in the running simulations list."""
        for sim_id, sim_data in sorted(running_simulations_data.items()):
            status_name = sim_data["status"]
            if status_name not in {
                SimulationStatusName.INITIALIZED.value,
                SimulationStatusName.POSTPROCESSING.value,
                SimulationStatusName.QUEUED.value,
                SimulationStatusName.STARTING.value,
            }:
                continue
            if sim_id not in self.running_simulations:
                self.add_simulation_to_model(sim_id, sim_data)
        row_count = self.tv_model.rowCount()
        for row_idx in range(row_count):
            name_item = self.tv_model.item(row_idx, 0)
            sim_id = name_item.data(Qt.UserRole)
            if (
                sim_id in self.simulations_without_progress
                or sim_id not in running_simulations_data
            ):
                continue
            progress_item = self.tv_model.item(row_idx, self.PROGRESS_COLUMN_IDX)
            sim_data = running_simulations_data[sim_id]
            new_status_name = sim_data["status"]
            new_progress = sim_data["progress"]
            if new_status_name in {
                SimulationStatusName.CRASHED.value,
                SimulationStatusName.STOPPED.value,
            }:
                old_status, old_progress = progress_item.data(PROGRESS_ROLE)
                progress_item.setData((new_status_name, old_progress), PROGRESS_ROLE)
                self.simulations_without_progress.add(sim_id)
            else:
                progress_item.setData((new_status_name, new_progress), PROGRESS_ROLE)
            if new_status_name == SimulationStatusName.FINISHED.value:
                self.simulations_without_progress.add(sim_id)
                sim_name = sim_data["name"]
                msg = f"Simulation {sim_name} finished!"
                self.communication.bar_info(msg, log_text_color=QColor(Qt.darkGreen))
        self.refresh_last_updated_label()

    def new_wizard_init(self):
        """Open new simulation initiation options dialog."""
        model_selection_dlg = ModelSelectionDialog(
            self.communication,
            self.current_user,
            self.threedi_api,
            self.organisations,
            self.working_dir,
            self.current_local_schematisation,
            self,
        )

        if model_selection_dlg.exec() == QDialog.DialogCode.Accepted:
            simulation_template = model_selection_dlg.current_simulation_template
            (
                simulation,
                settings_overview,
                events,
                lizard_post_processing_overview,
            ) = self.get_simulation_data_from_template(simulation_template)

            self.new_simulation_wizard(
                simulation,
                settings_overview,
                events,
                lizard_post_processing_overview,
                simulation_template,
            )

    def get_simulation_data_from_template(self, template):
        """Fetching simulation, settings and events data from the simulation template."""
        simulation, settings_overview, events, lizard_post_processing_overview = (
            None,
            None,
            None,
            None,
        )
        try:
            simulation = template.simulation
            sim_id = simulation.id
            settings_overview = fetch_simulation_settings_overview(
                self.threedi_api, str(sim_id)
            )
            events = fetch_simulation_events(self.threedi_api, sim_id)
            cloned_from_url = simulation.cloned_from
            if cloned_from_url:
                source_sim_id = cloned_from_url.strip("/").split("/")[-1]
                lizard_post_processing_overview = (
                    fetch_simulation_lizard_postprocessing_overview(
                        self.threedi_api, source_sim_id
                    )
                )
        except ApiException as e:
            error_msg = extract_error_message(e)
            if "No basic post-processing resource found" not in error_msg:
                self.communication.bar_error(error_msg)
        except Exception as e:
            error_msg = f"Error: {e}"
            self.communication.bar_error(error_msg)
        return simulation, settings_overview, events, lizard_post_processing_overview

    def new_simulation_wizard(
        self,
        simulation,
        settings_overview,
        events,
        lizard_post_processing_overview,
        simulation_template,
    ):
        """Opening a wizard which allows defining and running new simulations."""
        # pass it a model
        # s = Simulation()

        wiz = SimulationWizard(self)

        # This is hack to be able to add hyperlinks in QWizard subtitle (for this we need
        # to find the QLabel holding the subtitle, but this is only created after showing the widget)
        wiz.show()
        QgsApplication.instance().processEvents()
        for label in self.findChildren(QLabel):
            if "href" in str(label.text()):
                label.setTextInteractionFlags(Qt.TextBrowserInteraction)
                label.setOpenExternalLinks(True)

        if wiz.exec() == QDialog.DialogCode.Accepted:
            QgsMessageLog.logMessage("ACCEPT", level=Qgis.Critical)

        # pass the model to a sender

        # self.simulation_init_wizard = SimulationInit(
        #     self.model_selection_dlg.current_model,
        #     simulation_template,
        #     settings_overview,
        #     events,
        #     lizard_post_processing_overview,
        #     organisation=self.model_selection_dlg.organisation,
        #     api=self.threedi_api,
        #     parent=self,
        # )

        # self.simulation_wizard = SimulationWizard(
        #     self.plugin_dock, self.model_selection_dlg, self.simulation_init_wizard
        # )
        # if simulation:
        #     self.simulation_wizard.load_template_parameters(
        #         simulation, settings_overview, events, lizard_post_processing_overview
        #     )
        # self.close()
        # self.simulation_wizard.exec()

    def start_simulations(self, simulations_to_run):
        """Start the simulations."""
        upload_timeout = self.settings.value("threedi/timeout", 900, type=int)
        simulations_runner = SimulationRunner(
            self.threedi_api, simulations_to_run, upload_timeout=upload_timeout
        )
        simulations_runner.signals.initializing_simulations_progress.connect(
            self.on_initializing_progress
        )
        simulations_runner.signals.initializing_simulations_failed.connect(
            self.on_initializing_failed
        )
        simulations_runner.signals.initializing_simulations_finished.connect(
            self.on_initializing_finished
        )
        self.simulation_runner_pool.start(simulations_runner)

    def stop_simulation(self, index):
        """Sending request to shut down currently selected simulation."""
        if not index.isValid():
            return
        title = "Warning"
        question = "This simulation is now running.\nAre you sure you want to stop it?"
        answer = self.communication.ask(self, title, question, QMessageBox.Warning)
        if answer is True:
            try:
                name_item = self.tv_model.item(index.row(), 0)
                sim_id = name_item.data(Qt.UserRole)
                create_simulation_action(self.threedi_api, sim_id, name="shutdown")
                msg = f"Simulation {name_item.text()} stopped!"
                self.communication.bar_info(msg)
            except ApiException as e:
                error_msg = extract_error_message(e)
                self.communication.show_error(error_msg, self, "Error")
            except Exception as e:
                error_msg = f"Error: {e}"
                self.communication.show_error(error_msg, self, "Error")

    def on_initializing_progress(
        self,
        new_simulation,
        new_simulation_initialized,
        current_progress,
        total_progress,
    ):
        """Feedback on new simulation(s) initialization progress signal."""
        msg = f'Initializing simulation "{new_simulation.name}"...'
        self.communication.progress_bar(
            msg, 0, total_progress, current_progress, clear_msg_bar=True
        )
        if new_simulation_initialized:
            sim = new_simulation.simulation
            initial_status = new_simulation.initial_status
            status_name = initial_status.name
            date_created = initial_status.created.strftime(API_DATETIME_FORMAT)
            sim_data = {
                "date_created": date_created,
                "name": sim.name,
                "progress": 0,
                "status": status_name,
                "user_name": sim.user,
                "simulation_user_first_name": self.current_user["first_name"],
                "simulation_user_last_name": self.current_user["last_name"],
            }
            self.add_simulation_to_model(sim.id, sim_data)
            info_msg = f"Simulation {new_simulation.name} added to queue!"
            self.communication.bar_info(info_msg)

    def on_initializing_failed(self, error_message):
        """Feedback on new simulation(s) initialization failure signal."""
        self.communication.clear_message_bar()
        self.communication.bar_error(error_message, log_text_color=QColor(Qt.red))

    def on_initializing_finished(self, message):
        """Feedback on new simulation(s) initialization finished signal."""
        self.communication.clear_message_bar()
        self.communication.bar_info(message)

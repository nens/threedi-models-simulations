from collections import OrderedDict, defaultdict
from enum import Enum

from qgis.PyQt.QtCore import QItemSelectionModel, QObject, Qt, QThreadPool, pyqtSignal
from qgis.PyQt.QtGui import QStandardItem, QStandardItemModel
from qgis.PyQt.QtWidgets import (
    QDialog,
    QGridLayout,
    QLabel,
    QListView,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QTreeView,
    QWidget,
)

from threedi_models_simulations.communication import UICommunication
from threedi_models_simulations.threedi_api_utils import (
    fetch_schematisation,
    fetch_schematisation_latest_revision,
)
from threedi_models_simulations.utils import is_loaded_in_schematisation_editor
from threedi_models_simulations.widgets.schematisation_upload_wizard import (
    SchematisationUploadWizard,
)
from threedi_models_simulations.workers.upload import SchematisationUploadWorker

# from ..communication import ListViewLogger
# from .model_deletion import ModelDeletionDialog


class UploadStatus(Enum):
    IN_PROGRESS = "In progress"
    SUCCESS = "Success"
    FAILURE = "Failure"
    CANCELED = "Canceled"


class UploadManagementSignals(QObject):
    """Upload management signals."""

    cancel_upload = pyqtSignal()


class SchematisationUploadDialog(QDialog):
    """Upload status overview dialog."""

    MAX_SCHEMATISATION_MODELS = 3
    MAX_THREAD_COUNT = 1

    def __init__(
        self, threedi_api, current_local_schematisation, organisations, parent
    ):
        super().__init__(parent)

        self.setWindowTitle("Upload status")
        self.setMinimumSize(750, 600)

        gridLayout = QGridLayout(self)

        gridLayout.addWidget(QLabel("Running uploads"), 0, 0, 1, 2)
        self.tv_uploads = QTreeView()
        self.tv_uploads.setMaximumHeight(100)
        self.tv_uploads.setAutoScrollMargin(16)
        self.tv_uploads.setEditTriggers(QTreeView.NoEditTriggers)
        self.tv_uploads.setIndentation(20)
        gridLayout.addWidget(self.tv_uploads, 1, 0, 1, 2)
        gridLayout.addWidget(QLabel("Upload feedback"), 2, 0, 1, 2)

        self.lv_upload_feedback = QListView()
        self.lv_upload_feedback.setEditTriggers(QListView.NoEditTriggers)
        gridLayout.addWidget(self.lv_upload_feedback, 3, 0, 1, 2)

        pb_hide = QPushButton("Cancel")
        gridLayout.addWidget(pb_hide, 4, 0)
        pb_new_upload = QPushButton("New Upload")
        gridLayout.addWidget(pb_new_upload, 4, 1)

        self.progress_widget = QWidget()
        gridLayout_2 = QGridLayout(self.progress_widget)
        gridLayout_2.addWidget(QLabel("TOTAL PROGRESS"), 0, 0)

        self.pbar_total_upload = QProgressBar()
        self.pbar_total_upload.setMinimumHeight(25)
        gridLayout_2.addWidget(self.pbar_total_upload, 1, 0, 1, 2)

        self.lbl_current_task = QLabel("TASK PROGRESS")
        gridLayout_2.addWidget(self.lbl_current_task, 2, 0)

        self.pbar_current_task = QProgressBar()
        self.pbar_current_task.setMinimumHeight(25)
        self.pbar_current_task.setMaximum(100)
        gridLayout_2.addWidget(self.pbar_current_task, 3, 0, 1, 2)

        horizontalSpacer = QSpacerItem(
            40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum
        )
        gridLayout_2.addItem(horizontalSpacer, 4, 0)

        pb_cancel_upload = QPushButton("Cancel upload")
        gridLayout_2.addWidget(pb_cancel_upload, 5, 0, 1, 2)

        gridLayout.addWidget(self.progress_widget, 5, 0, 1, 2)
        self.label_success = QLabel(
            '<span style="color:#00aa00;">✓ Completed successfully</span>'
        )
        gridLayout.addWidget(self.label_success, 9, 0, 1, 2)
        self.label_failure = QLabel(
            '<span style="color:#ff0000;">✕ Upload failed</span>'
        )
        gridLayout.addWidget(self.label_failure, 10, 0, 1, 2)

        self.threedi_api = threedi_api
        self.current_local_schematisation = current_local_schematisation
        self.organisations = organisations

        # self.feedback_logger = ListViewLogger(self.lv_upload_feedback)
        self.upload_thread_pool = QThreadPool()
        self.upload_thread_pool.setMaxThreadCount(self.MAX_THREAD_COUNT)
        self.ended_tasks = OrderedDict()
        self.upload_management_signals = {}
        self.upload_progresses = defaultdict(lambda: ("NO TASK", 0, 0))
        self.current_upload_row = 0
        self.schematisation = None
        self.schematisation_filepath = None
        self.schematisation_id = None
        pb_new_upload.clicked.connect(self.upload_new_model)
        pb_hide.clicked.connect(self.close)
        pb_cancel_upload.clicked.connect(self.on_cancel_upload)
        self.tv_model = None
        self.setup_view_model()
        # self.adjustSize()

    def setup_view_model(self):
        """Setting up model and columns for TreeView."""
        nr_of_columns = 4
        self.tv_model = QStandardItemModel(0, nr_of_columns - 1)
        self.tv_model.setHorizontalHeaderLabels(
            ["Schematisation name", "Revision", "Commit message", "Status"]
        )
        self.tv_uploads.setModel(self.tv_model)
        self.tv_uploads.selectionModel().selectionChanged.connect(
            self.on_upload_context_change
        )
        for i in range(nr_of_columns):
            self.tv_uploads.resizeColumnToContents(i)
        self.progress_widget.hide()
        self.label_success.hide()
        self.label_failure.hide()

    def on_upload_context_change(self):
        """Updating progress bars based on upload selection change."""
        selected_indexes = self.tv_uploads.selectedIndexes()
        if selected_indexes:
            current_index = selected_indexes[0]
            current_row = current_index.row()
            self.current_upload_row = current_row + 1
            self.on_update_upload_progress(
                self.current_upload_row,
                *self.upload_progresses[self.current_upload_row],
            )
            # self.feedback_logger.clear()  # TODO
            try:
                for msg, success in self.ended_tasks[self.current_upload_row]:
                    if success is True:
                        # self.feedback_logger.log_info(msg)
                        pass
                    elif success is False:
                        # self.feedback_logger.log_error(msg)
                        pass
                    else:
                        # self.feedback_logger.log_warn(msg, log_text_color=Qt.darkGray)
                        pass
            except KeyError:
                pass
            status_item = self.tv_model.item(current_row, 3)
            status = status_item.text()
            if status == UploadStatus.SUCCESS.value:
                self.progress_widget.hide()
                self.label_success.show()
                self.label_failure.hide()
            elif status == UploadStatus.FAILURE.value:
                self.progress_widget.hide()
                self.label_success.hide()
                self.label_failure.show()
            elif status == UploadStatus.CANCELED.value:
                self.progress_widget.hide()
                self.label_success.hide()
                self.label_failure.hide()
            else:
                self.progress_widget.show()
                self.label_success.hide()
                self.label_failure.hide()

    def add_upload_to_model(self, upload_specification):
        """Initializing a new upload."""
        create_revision = upload_specification["create_revision"]
        schematisation = upload_specification["schematisation"]
        schema_name_item = QStandardItem(f"{schematisation.name}")
        revision = upload_specification["latest_revision"]
        revision_number = (
            revision.number + 1 if create_revision is True else revision.number
        )
        revision_item = QStandardItem(f"{revision_number}")
        revision_item.setData(revision_number, role=Qt.DisplayRole)
        commit_msg_item = QStandardItem(f"{upload_specification['commit_message']}")
        status_item = QStandardItem(UploadStatus.IN_PROGRESS.value)
        self.tv_model.appendRow(
            [schema_name_item, revision_item, commit_msg_item, status_item]
        )
        upload_row_number = self.tv_model.rowCount()
        upload_row_idx = self.tv_model.index(upload_row_number - 1, 0)
        self.tv_uploads.selectionModel().setCurrentIndex(
            upload_row_idx, QItemSelectionModel.ClearAndSelect
        )
        upload_worker = SchematisationUploadWorker(
            self.threedi_api,
            self.current_local_schematisation,
            upload_specification,
            upload_row_number,
        )
        upload_worker.progress.connect(self.on_update_upload_progress)
        upload_worker.finished.connect(self.on_upload_finished_success)
        upload_worker.failed.connect(self.on_upload_failed)
        upload_worker.canceled.connect(self.on_upload_canceled)
        upload_worker.revision_committed.connect(self.on_revision_committed)
        management_signals = UploadManagementSignals()
        management_signals.cancel_upload.connect(upload_worker.stop_upload_tasks)
        self.upload_management_signals[upload_row_number] = management_signals
        self.upload_thread_pool.start(upload_worker)

    def upload_new_model(self):
        """Initializing new upload wizard."""
        if (
            not self.current_local_schematisation
            or not self.current_local_schematisation.schematisation_db_filepath
        ):
            warn_msg = (
                "Please load the schematisation first before starting the upload."
            )
            UICommunication.show_warn(warn_msg, self, "Load schematisation")
            # TODO
            # self.plugin_dock.build_options.load_local_schematisation()
            return
        self.schematisation_filepath = (
            self.current_local_schematisation.schematisation_db_filepath
        )
        schema_gpkg_loaded = is_loaded_in_schematisation_editor(
            self.schematisation_filepath
        )
        if schema_gpkg_loaded is False:
            title = "Warning"
            question = (
                "Warning: the GeoPackage that you loaded with the 3Di Schematisation Editor is not in the revision you "
                "are about to upload. Do you want to continue?"
            )
            on_continue_answer = UICommunication.ask(
                self, title, question, QMessageBox.Warning
            )
            if on_continue_answer is not True:
                return
        self.schematisation_id = self.current_local_schematisation.id
        self.schematisation = fetch_schematisation(
            self.threedi_api, self.schematisation_id
        )
        current_wip_revision = self.current_local_schematisation.wip_revision
        latest_revision = (
            fetch_schematisation_latest_revision(
                self.threedi_api, self.schematisation_id
            )
            if current_wip_revision.number > 0
            else None
        )
        latest_revision_number = latest_revision.number if latest_revision else 0
        if latest_revision_number != current_wip_revision.number:
            question = f"WIP revision number different than latest online revision ({latest_revision_number})"
            answer = UICommunication.custom_ask(
                self, "Pick action", question, "Upload anyway?", "Cancel"
            )
            if answer == "Cancel":
                return

        upload_wizard_dialog = SchematisationUploadWizard(
            self.current_local_schematisation,
            self.schematisation,
            self.schematisation_filepath,
            self.threedi_api,
            self.organisations[self.schematisation.owner],
            self,
        )
        upload_wizard_dialog.exec_()
        new_upload = upload_wizard_dialog.new_upload
        if not new_upload:
            return
        if new_upload["make_3di_model"]:
            deletion_dlg = ModelDeletionDialog(self.parent)
            if deletion_dlg.threedi_models_to_show:
                deletion_dlg.exec()
                if deletion_dlg.threedi_models_to_show:
                    UICommunication.bar_warn("Uploading canceled...")
                    return
        self.add_upload_to_model(new_upload)

    def on_revision_committed(self):
        """Handling actions on successful revision commit."""
        # TODO
        # self.plugin_dock.update_schematisation_view()
        pass

    def on_cancel_upload(self):
        """Handling of canceling upload tasks."""
        question = "Do you want to cancel revision upload task?"
        yes = UICommunication.ask(self, "Cancel upload?", question)
        if not yes:
            return
        item = self.tv_model.item(self.current_upload_row - 1, 3)
        item.setText("Canceling...")
        management_signals = self.upload_management_signals[self.current_upload_row]
        management_signals.cancel_upload.emit()

    def on_upload_canceled(self, upload_row_number):
        """Handling signal send when upload was canceled."""
        item = self.tv_model.item(upload_row_number - 1, 3)
        item.setText(UploadStatus.CANCELED.value)
        cancel_msg, success = "Upload task canceled by the user", None
        canceled_task_row = (cancel_msg, success)
        if upload_row_number not in self.ended_tasks:
            self.ended_tasks[upload_row_number] = [canceled_task_row]
        else:
            self.ended_tasks[upload_row_number].append(canceled_task_row)
        # self.feedback_logger.log_warn(cancel_msg, log_text_color=Qt.darkGray)
        self.on_upload_context_change()

    def on_update_upload_progress(
        self, upload_row_number, task_name, task_progress, total_progress
    ):
        """Handling actions on upload progress update."""
        self.upload_progresses[upload_row_number] = (
            task_name,
            task_progress,
            total_progress,
        )
        if self.current_upload_row == upload_row_number:
            self.lbl_current_task.setText(task_name)
            self.pbar_current_task.setValue(task_progress)
            self.pbar_total_upload.setValue(total_progress)
            if task_progress == 100 and task_name != "DONE":
                success = True
                enriched_success_message = f"{task_name} ==> done"
                ended_task_row = (enriched_success_message, success)
                if upload_row_number not in self.ended_tasks:
                    self.ended_tasks[upload_row_number] = [ended_task_row]
                else:
                    upload_ended_tasks = self.ended_tasks[upload_row_number]
                    if ended_task_row not in upload_ended_tasks:
                        upload_ended_tasks.append(ended_task_row)
                    else:
                        return
                # self.feedback_logger.log_info(enriched_success_message)

    def on_upload_finished_success(self, upload_row_number, msg):
        """Handling action on upload success."""
        item = self.tv_model.item(upload_row_number - 1, 3)
        item.setText(UploadStatus.SUCCESS.value)
        UICommunication.bar_info(msg, log_text_color=Qt.darkGreen)
        self.on_upload_context_change()

    def on_upload_failed(self, upload_row_number, error_message):
        """Handling action on upload failure."""
        item = self.tv_model.item(upload_row_number - 1, 3)
        item.setText(UploadStatus.FAILURE.value)
        UICommunication.bar_error(error_message, log_text_color=Qt.red)
        success = False
        failed_task_name = self.upload_progresses[self.current_upload_row][0]
        enriched_error_message = f"{failed_task_name} ==> failed\n{error_message}"
        failed_task_row = (enriched_error_message, success)
        if upload_row_number not in self.ended_tasks:
            self.ended_tasks[upload_row_number] = [failed_task_row]
        else:
            self.ended_tasks[upload_row_number].append(failed_task_row)
        # self.feedback_logger.log_error(enriched_error_message)
        self.on_upload_context_change()

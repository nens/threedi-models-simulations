import os
import time
from enum import Enum
from functools import partial

from qgis.PyQt.QtCore import QByteArray, QObject, QRunnable, QUrl, pyqtSignal, pyqtSlot
from threedi_api_client.files import upload_file

from threedi_models_simulations.constants import UPLOAD_CHUNK_SIZE
from threedi_models_simulations.threedi_api_utils import (
    FileState,
    SchematisationApiMapper,
    ThreediModelTaskStatus,
    UploadFileStatus,
    commit_schematisation_revision,
    create_schematisation_revision,
    create_schematisation_revision_model,
    create_schematisation_revision_raster,
    delete_schematisation_revision_raster,
    delete_schematisation_revision_sqlite,
    fetch_model,
    fetch_model_tasks,
    fetch_schematisation_revision,
    fetch_schematisation_revision_task,
    fetch_schematisation_revision_tasks,
    upload_schematisation_revision,
    upload_schematisation_revision_raster,
)
from threedi_models_simulations.utils.file import zip_into_archive


class RevisionUploadError(Exception):
    pass


class UploadWorkerSignals(QObject):
    """Separate object for signals as QRunnable is not a QObject."""

    finished = pyqtSignal(int, str)
    failed = pyqtSignal(int, str)
    progress = pyqtSignal(
        int, str, int, int
    )  # upload row number, task name, task progress, total progress
    canceled = pyqtSignal(int)
    revision_committed = pyqtSignal()


class SchematisationUploadWorker(QRunnable):
    """Worker object responsible for uploading models."""

    UPLOAD_CHECK_INTERVAL = 10
    UPLOAD_CHECK_RETRIES = 15
    TASK_CHECK_INTERVAL = 2.5
    TASK_CHECK_RETRIES = 4

    def __init__(
        self, threedi_api, local_schematisation, upload_specification, upload_row_number
    ):
        super().__init__()
        self.threedi_api = threedi_api
        self.local_schematisation = local_schematisation
        self.upload_specification = upload_specification
        self.upload_row_number = upload_row_number
        self.current_task = "NO TASK"
        self.current_task_progress = 0
        self.total_progress = 0
        self.schematisation = self.upload_specification["schematisation"]
        self.revision = self.upload_specification["latest_revision"]
        self.signals = UploadWorkerSignals()
        self.upload_canceled = False

    def stop_upload_tasks(self):
        """Mark the upload task as canceled."""
        self.upload_canceled = True

    @pyqtSlot()
    def run(self):
        """Run all schematisation upload tasks."""
        tasks_list = self.build_tasks_list()
        if not tasks_list:
            self.current_task = "DONE"
            self.current_task_progress = 100
            self.total_progress = 100
            self.report_upload_progress()
            self.signals.finished.emit(
                self.upload_row_number, "Nothing to upload or process"
            )
            return
        progress_per_task = int(1 / len(tasks_list) * 100)
        try:
            for i, task in enumerate(tasks_list, start=1):
                if self.upload_canceled:
                    self.signals.canceled.emit(self.upload_row_number)
                    return
                task()
                self.total_progress = progress_per_task * i
            self.current_task = "DONE"
            self.total_progress = 100
            self.report_upload_progress()
            msg = f"Schematisation '{self.schematisation.name}' (revision: {self.revision.number}) files uploaded"
            self.signals.finished.emit(self.upload_row_number, msg)
        except Exception as e:
            error_msg = f"Error: {e}"
            self.signals.failed.emit(self.upload_row_number, error_msg)

    def build_tasks_list(self):
        """Build upload tasks list."""
        tasks = list()
        create_revision = self.upload_specification["create_revision"]
        make_3di_model = self.upload_specification["make_3di_model"]
        inherit_templates = self.upload_specification["cb_inherit_templates"]
        if create_revision:
            tasks.append(self.create_revision_task)
        for file_name, file_state in self.upload_specification[
            "selected_files"
        ].items():
            make_action_on_file = file_state["make_action"]
            file_status = file_state["status"]
            if make_action_on_file is False:
                continue
            if file_status == UploadFileStatus.NEW:
                if file_name == "geopackage":
                    tasks.append(self.upload_schematisation_task)
                else:
                    tasks.append(partial(self.upload_raster_task, file_name))
            elif file_status == UploadFileStatus.CHANGES_DETECTED:
                if file_name == "geopackage":
                    tasks.append(self.delete_schematisation_task)
                    tasks.append(self.upload_schematisation_task)
                else:
                    tasks.append(partial(self.delete_raster_task, file_name))
                    tasks.append(partial(self.upload_raster_task, file_name))
            elif file_status == UploadFileStatus.DELETED_LOCALLY:
                tasks.append(partial(self.delete_raster_task, file_name))
            else:
                continue
        tasks.append(self.commit_revision_task)
        if make_3di_model:
            tasks.append(partial(self.create_3di_model_task, inherit_templates))
        return tasks

    def create_revision_task(self):
        """Run creation of the new revision task."""
        self.current_task = "CREATE REVISION"
        self.current_task_progress = 0
        self.report_upload_progress()
        self.revision = create_schematisation_revision(
            self.threedi_api, self.schematisation.id
        )
        self.current_task_progress = 100
        self.report_upload_progress()

    def upload_schematisation_task(self):
        self.current_task = "UPLOAD SCHEMATISATION DATABASE"
        self.current_task_progress = 0
        self.report_upload_progress()
        schematisation_geopackage = self.upload_specification["selected_files"][
            "geopackage"
        ]["filepath"]
        zipped_geopackage_filepath = zip_into_archive(schematisation_geopackage)
        zipped_geopackage_file_name = os.path.basename(zipped_geopackage_filepath)
        upload = upload_schematisation_revision(
            self.threedi_api,
            self.schematisation.id,
            self.revision.id,
            zipped_geopackage_file_name,
        )
        upload_file(
            upload.put_url,
            zipped_geopackage_filepath,
            UPLOAD_CHUNK_SIZE,
            callback_func=self.monitor_upload_progress,
        )
        os.remove(zipped_geopackage_filepath)
        self.current_task_progress = 100
        self.report_upload_progress()

    def delete_schematisation_task(self):
        self.current_task = "DELETE SCHEMATISATION DATABASE"
        self.current_task_progress = 0
        self.report_upload_progress()
        delete_schematisation_revision_sqlite(
            self.threedi_api, self.schematisation.id, self.revision.id
        )
        self.current_task_progress = 100
        self.report_upload_progress()

    def upload_raster_task(self, raster_type):
        """Run raster file upload task."""
        self.current_task = f"UPLOAD RASTER ({raster_type})"
        self.current_task_progress = 0
        self.report_upload_progress()
        raster_filepath = self.upload_specification["selected_files"][raster_type][
            "filepath"
        ]
        raster_file = os.path.basename(raster_filepath)
        raster_revision = create_schematisation_revision_raster(
            self.threedi_api,
            self.schematisation.id,
            self.revision.id,
            raster_file,
            raster_type=SchematisationApiMapper.api_client_raster_type(raster_type),
        )
        raster_upload = upload_schematisation_revision_raster(
            self.threedi_api,
            raster_revision.id,
            self.schematisation.id,
            self.revision.id,
            raster_file,
        )
        upload_file(
            raster_upload.put_url,
            raster_filepath,
            UPLOAD_CHUNK_SIZE,
            callback_func=self.monitor_upload_progress,
        )
        self.current_task_progress = 100
        self.report_upload_progress()

    def delete_raster_task(self, raster_type):
        """Run raster file deletion task."""
        types_to_delete = [SchematisationApiMapper.api_client_raster_type(raster_type)]
        if raster_type == "dem_file":
            types_to_delete.append(
                "dem_raw_file"
            )  # We need to remove legacy 'dem_raw_file` as well
        self.current_task = f"DELETE RASTER ({raster_type})"
        self.current_task_progress = 0
        self.report_upload_progress()
        for revision_raster in self.revision.rasters:
            revision_raster_type = revision_raster.type
            if revision_raster_type in types_to_delete:
                delete_schematisation_revision_raster(
                    self.threedi_api,
                    revision_raster.id,
                    self.schematisation.id,
                    self.revision.id,
                )
                break
        self.current_task_progress = 100
        self.report_upload_progress()

    def commit_revision_task(self):
        """Run committing revision task."""
        self.current_task = "COMMIT REVISION"
        self.current_task_progress = 0
        self.report_upload_progress()
        commit_ready_file_states = {FileState.UPLOADED, FileState.PROCESSED}
        for i in range(self.UPLOAD_CHECK_RETRIES):
            before_commit_revision = fetch_schematisation_revision(
                self.threedi_api, self.schematisation.id, self.revision.id
            )
            revision_files = [before_commit_revision.sqlite.file] + [
                r.file for r in before_commit_revision.rasters
            ]
            revision_file_states = {FileState(file.state) for file in revision_files}
            if all(
                file_state in commit_ready_file_states
                for file_state in revision_file_states
            ):
                break
            elif FileState.ERROR in revision_file_states:
                err = RevisionUploadError("Processing of the uploaded files failed!")
                raise err
            else:
                time.sleep(self.UPLOAD_CHECK_INTERVAL)
        commit_message = self.upload_specification["commit_message"]
        commit_schematisation_revision(
            self.threedi_api,
            self.schematisation.id,
            self.revision.id,
            commit_message=commit_message,
        )
        self.revision = fetch_schematisation_revision(
            self.threedi_api, self.schematisation.id, self.revision.id
        )
        while self.revision.is_valid is None:
            time.sleep(2)
            self.revision = fetch_schematisation_revision(
                self.threedi_api, self.schematisation.id, self.revision.id
            )
        self.current_task_progress = 100
        self.report_upload_progress()
        self.local_schematisation.update_wip_revision(self.revision.number)
        self.signals.revision_committed.emit()

    def create_3di_model_task(self, inherit_templates=False):
        """Run creation of the new model out of revision data."""
        self.current_task = "MAKE 3DI MODEL"
        self.current_task_progress = 0
        self.report_upload_progress()
        # Wait for the 'modelchecker' validations
        model_checker_task = None
        revision_tasks = fetch_schematisation_revision_tasks(
            self.threedi_api, self.schematisation.id, self.revision.id
        )
        for i in range(self.TASK_CHECK_RETRIES):
            for rtask in revision_tasks:
                if rtask.name == "modelchecker":
                    model_checker_task = rtask
                    break
            if model_checker_task:
                break
            else:
                time.sleep(self.TASK_CHECK_INTERVAL)
        if model_checker_task:
            status = model_checker_task.status
            while status != ThreediModelTaskStatus.SUCCESS.value:
                model_checker_task = fetch_schematisation_revision_task(
                    self.threedi_api,
                    model_checker_task.id,
                    self.schematisation.id,
                    self.revision.id,
                )
                status = model_checker_task.status
                if status == ThreediModelTaskStatus.SUCCESS.value:
                    break
                elif status == ThreediModelTaskStatus.FAILURE.value:
                    err = RevisionUploadError(model_checker_task.detail["message"])
                    raise err
                else:
                    time.sleep(self.TASK_CHECK_INTERVAL)
            checker_errors = model_checker_task.detail["result"]["errors"]
            if checker_errors:
                error_msg = "\n".join(error["description"] for error in checker_errors)
                err = RevisionUploadError(error_msg)
                raise err
        # Create 3Di model
        model = create_schematisation_revision_model(
            self.threedi_api,
            self.schematisation.id,
            self.revision.id,
            inherit_templates,
        )
        model_id = model.id
        finished_tasks = {
            "make_gridadmin": False,
            "make_tables": False,
            "make_aggregations": False,
            "make_cog": False,
            "make_geojson": False,
            "make_simulation_templates": False,
        }
        expected_tasks_number = len(finished_tasks)
        while not all(finished_tasks.values()):
            model_tasks = fetch_model_tasks(self.threedi_api, model_id)
            for task in model_tasks:
                task_status = task.status
                if task_status == ThreediModelTaskStatus.SUCCESS.value:
                    finished_tasks[task.name] = True
                elif task_status == ThreediModelTaskStatus.FAILURE.value:
                    err = RevisionUploadError(task.detail["message"])
                    raise err
            model = fetch_model(self.threedi_api, model_id)
            if getattr(model, "is_valid", False):
                finished_tasks = {
                    task_name: True for task_name in finished_tasks.keys()
                }
            finished_tasks_count = len([val for val in finished_tasks.values() if val])
            self.monitor_upload_progress(finished_tasks_count, expected_tasks_number)
            if finished_tasks_count != expected_tasks_number:
                time.sleep(self.TASK_CHECK_INTERVAL)

    def report_upload_progress(self):
        """Report upload progress."""
        self.signals.progress.emit(
            self.upload_row_number,
            self.current_task,
            self.current_task_progress,
            self.total_progress,
        )

    def monitor_upload_progress(self, chunk_size, total_size):
        """Upload progress callback method."""
        upload_progress = int(chunk_size / total_size * 100)
        self.current_task_progress = upload_progress
        self.report_upload_progress()

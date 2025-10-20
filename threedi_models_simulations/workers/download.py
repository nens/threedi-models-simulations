import os

import requests
from qgis.PyQt.QtCore import QObject, QRunnable, pyqtSignal, pyqtSlot
from threedi_mi_utils import bypass_max_path_limit

from threedi_models_simulations.constants import DOWNLOAD_CHUNK_SIZE
from threedi_models_simulations.utils import unzip_archive


class DownloadWorkerSignals(QObject):
    """Definition of the download worker signals. Needs to be separate class as QRunnable is not a QObject"""

    thread_finished = pyqtSignal(
        str, str, int
    )  # finish message, download directory, sim_id
    download_failed = pyqtSignal(str, int)
    download_progress = pyqtSignal(float, int)


class DownloadProgressWorker(QRunnable):
    """Worker object responsible for downloading simulations results."""

    NOT_STARTED = -1
    FINISHED = 100
    FAILED = 101

    def __init__(self, simulation, downloads, directory):
        super().__init__()
        self.simulation = simulation
        self.simulation_id = simulation.id
        self.downloads = downloads
        self.directory = bypass_max_path_limit(directory)
        self.success = True
        self.signals = DownloadWorkerSignals()

    @pyqtSlot()
    def run(self):
        """Downloading simulation results files."""
        if self.downloads:
            finished_message = (
                f"Downloading results of {self.simulation.name} ({self.simulation.id}) finished! "
                f"The files have been saved in the following location: '{self.directory}'"
            )
        else:
            finished_message = "Nothing to download!"
        total_size = sum(download.size for result_file, download in self.downloads)
        size = 0
        self.signals.download_progress.emit(size, self.simulation_id)
        for result_file, download in self.downloads:
            filename = result_file.filename
            filename_path = bypass_max_path_limit(
                os.path.join(self.directory, filename), is_file=True
            )
            try:
                os.makedirs(self.directory, exist_ok=True)
                file_data = requests.get(download.get_url, stream=True, timeout=15)
                with open(filename_path, "wb") as f:
                    for chunk in file_data.iter_content(chunk_size=DOWNLOAD_CHUNK_SIZE):
                        if chunk:
                            f.write(chunk)
                            size += len(chunk)
                            self.signals.download_progress.emit(
                                size / total_size * 100, self.simulation_id
                            )
                if filename.lower().endswith(".zip"):
                    unzip_archive(filename_path)
                continue
            except Exception as e:
                error_msg = f"Error: {e}"
            self.signals.download_progress.emit(self.FAILED, self.simulation_id)
            self.signals.download_failed.emit(error_msg, self.simulation_id)
            self.success = False
            break
        if self.success is True:
            self.signals.download_progress.emit(self.FINISHED, self.simulation_id)
            self.signals.thread_finished.emit(
                finished_message, self.directory, self.simulation_id
            )

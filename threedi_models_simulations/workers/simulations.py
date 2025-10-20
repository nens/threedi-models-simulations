import base64
import json
import time

from qgis.core import Qgis, QgsMessageLog
from qgis.PyQt.QtCore import QByteArray, QObject, QUrl, pyqtSignal, pyqtSlot
from qgis.PyQt.QtNetwork import QNetworkRequest
from threedi_api_client.openapi import ApiException

from threedi_models_simulations.threedi_api_utils import (
    SimulationStatusName,
    extract_error_message,
    fetch_simulation_statuses,
)
from threedi_models_simulations.widgets.simulation_results_dialog import (
    API_DATETIME_FORMAT,
)


class SimulationProgressWorker(QObject):
    """
    Worker object that will be moved to a separate thread and will check progresses of the running simulations.
    This worker is fetching data through the websocket.
    """

    thread_finished = pyqtSignal(str)
    thread_failed = pyqtSignal(str)
    progresses_fetched = pyqtSignal(dict)
    simulation_finished = pyqtSignal(dict)

    def __init__(self, threedi_api, wss_url, personal_api_key, model_id=None):
        super().__init__()
        self.threedi_api = threedi_api
        self.wss_url = wss_url
        self.personal_api_key = personal_api_key
        self.ws_client = None
        self.running_simulations = {}
        self.model_id = model_id

    @pyqtSlot()
    def run(self):
        """Checking running simulations progresses."""
        self.fetch_finished_simulations()
        self.start_listening()

    def fetch_finished_simulations(self):
        """Fetches finished simulations data."""
        try:
            finished_simulations_statuses = fetch_simulation_statuses(
                self.threedi_api, name=SimulationStatusName.FINISHED.value
            )
            if self.model_id:
                finished_simulations_statuses = (
                    status
                    for status in finished_simulations_statuses
                    if status.threedimodel_id == self.model_id
                )
            finished_simulations_data = {
                status.simulation_id: {
                    "date_created": status.created.strftime(API_DATETIME_FORMAT),
                    "name": status.simulation_name,
                    "progress": 100,
                    "status": status.name,
                    "simulation_user_first_name": status.simulation_user_first_name,
                    "simulation_user_last_name": status.simulation_user_last_name,
                }
                for status in finished_simulations_statuses
            }
            time.sleep(1)
            self.simulation_finished.emit(finished_simulations_data)
        except ApiException as e:
            error_msg = extract_error_message(e)
            self.thread_failed.emit(error_msg)

    def start_listening(self):
        """Start listening of active simulations websocket."""
        identifier = "Basic"
        api_key = base64.b64encode(f"__key__:{self.personal_api_key}".encode()).decode()
        basic_auth_token = f"{identifier} {api_key}"
        api_version = self.threedi_api.version
        ws_request = QNetworkRequest(
            QUrl(f"{self.wss_url}/{api_version}/active-simulations/")
        )
        ws_request.setRawHeader(
            QByteArray().append("Authorization"), QByteArray().append(basic_auth_token)
        )
        try:
            # It seems QtWebSockets is not packaged with Qgis so we need to explicitly import it from the PyQt5 namespace
            from PyQt5 import QtWebSockets
        except ImportError:
            QtWebSockets = None
        if QtWebSockets is None:
            QgsMessageLog.logMessage("No websockets available", level=Qgis.Critical)
            return

        self.ws_client = QtWebSockets.QWebSocket(
            version=QtWebSockets.QWebSocketProtocol.VersionLatest
        )
        self.ws_client.textMessageReceived.connect(
            self.all_simulations_progress_web_socket
        )
        self.ws_client.error.connect(self.websocket_error)
        self.ws_client.open(ws_request)

    def stop_listening(self, be_quite=False):
        """Close websocket client."""
        if self.ws_client is not None:
            self.ws_client.textMessageReceived.disconnect(
                self.all_simulations_progress_web_socket
            )
            self.ws_client.error.disconnect(self.websocket_error)
            self.ws_client.close()
            if be_quite is False:
                stop_message = "Checking running simulation stopped."
                self.thread_finished.emit(stop_message)

    def websocket_error(self, error_code):
        """Report errors from websocket."""
        error_string = self.ws_client.errorString()
        error_msg = f"Websocket error ({error_code}): {error_string}"
        self.thread_failed.emit(error_msg)

    def all_simulations_progress_web_socket(self, data):
        """Get all simulations progresses through the websocket."""
        data = json.loads(data)
        data_type = data.get("type")
        if data_type == "active-simulations" or data_type == "active-simulation":
            simulations = data.get("data")
            for sim_id_str, sim_data_str in simulations.items():
                sim_id = int(sim_id_str)
                sim_data = json.loads(sim_data_str)
                self.running_simulations[sim_id] = sim_data
        elif data_type == "progress":
            sim_id = int(data["data"]["simulation_id"])
            progress_percentage = data["data"]["progress"]
            sim_data = self.running_simulations[sim_id]
            sim_data["progress"] = progress_percentage
        elif data_type == "status":
            sim_id = int(data["data"]["simulation_id"])
            status_name = data["data"]["status"]
            sim_data = self.running_simulations[sim_id]
            sim_data["status"] = status_name
            if status_name == SimulationStatusName.FINISHED.value:
                if sim_data["progress"] == 100:
                    statuses = {
                        status.simulation_id: status
                        for status in fetch_simulation_statuses(self.threedi_api)
                    }
                    sim_status = statuses[sim_id]
                    sim_data["status"] = SimulationStatusName.FINISHED.value
                    sim_data["simulation_user_first_name"] = (
                        sim_status.simulation_user_first_name
                    )
                    sim_data["simulation_user_last_name"] = (
                        sim_status.simulation_user_last_name
                    )
                    self.simulation_finished.emit({sim_id: sim_data})
                else:
                    sim_data["status"] = SimulationStatusName.STOPPED.value
        self.progresses_fetched.emit(self.running_simulations)

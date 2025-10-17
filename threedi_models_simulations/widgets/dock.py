import functools
import webbrowser
from pathlib import Path

from qgis.PyQt import uic
from qgis.PyQt.QtCore import QSettings, pyqtSignal
from qgis.PyQt.QtWidgets import QDialog, QDockWidget

from threedi_models_simulations.communication import UICommunication
from threedi_models_simulations.constants import MANAGEMENT_URL_PREFIX
from threedi_models_simulations.schematisation_loader import (
    SchematisationLoader,
    SchematisationLoaderActions,
)
from threedi_models_simulations.widgets.login import LogInDialog
from threedi_models_simulations.widgets.schematisation_upload_dialog import (
    SchematisationUploadDialog,
)


def login_required(func):
    """Decorator for enforcing authentication"""

    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        if self.threedi_api is None:
            self.communication.bar_info(
                "Action reserved for logged in users. Logging-in..."
            )
            log_in_dialog = LogInDialog(self)
            log_in_dialog.settings_requested.connect(self.settings_requested)
            if log_in_dialog.exec() == QDialog.DialogCode.Accepted:
                self.threedi_api = log_in_dialog.get_api()
                self.current_user_info = log_in_dialog.get_user_info()
                self.organisations = log_in_dialog.get_organisations()
                self.initialize_authorized_view()
            else:
                self.communication.bar_warn("Logging-in canceled. Action aborted!")
                return

        return func(self, *args, **kwargs)

    return wrapper


FORM_CLASS, _ = uic.loadUiType(
    Path(__file__).parent / "dock.ui",
)


class DockWidget(QDockWidget, FORM_CLASS):
    settings_requested = pyqtSignal()

    def __init__(self, parent, iface):
        super().__init__(parent)
        self.setupUi(self)

        self.iface = iface
        self.threedi_api = None
        self.current_user_info = None
        self.organisations = {}
        self.communication = UICommunication(self.lv_log)
        self.schematisation_loader = SchematisationLoader(self, self.communication)
        self.current_local_schematisation = None

        self.btn_log_in_out.clicked.connect(self.on_log_in_log_out)
        self.btn_load_schematisation.clicked.connect(self.load_local_schematisation)
        self.btn_load_revision.clicked.connect(self.load_local_schematisation)
        self.btn_download.clicked.connect(self.download_schematisation)
        self.btn_upload.clicked.connect(self.upload_schematisation)
        self.btn_new.clicked.connect(self.new_schematisation)
        self.btn_manage.clicked.connect(self.on_manage)

    def on_log_in_log_out(self):
        """Trigger log-in or log-out action."""
        if self.threedi_api is None:
            self.on_log_in()
        else:
            self.on_log_out()

    @login_required
    def on_log_in(self):
        # Login handled in decorator
        pass

    def on_log_out(self):
        # if self.simulations_progresses_thread is not None:
        #     self.stop_fetching_simulations_progresses()
        #     if (
        #         self.simulation_overview_dlg is not None
        #         and self.simulation_overview_dlg.model_selection_dlg is not None
        #     ):
        #         self.simulation_overview_dlg.model_selection_dlg.unload_breach_layers()
        #         self.simulation_overview_dlg = None
        # if self.simulation_results_dlg is not None:
        #     self.simulation_results_dlg = None
        # if self.upload_dlg:
        #     self.upload_dlg.hide()
        #     self.upload_dlg = None

        self.threedi_api = None
        self.current_user_info = None
        self.organisations.clear()

        self.label_user.setText("-")
        # set_icon(self.btn_log_in_out, "arrow.svg")
        self.btn_log_in_out.setToolTip("Log in")

    def initialize_authorized_view(self):
        """Method for initializing processes after logging in 3Di API."""
        self.btn_log_in_out.setToolTip("Log out")

        self.label_user.setText(
            f"{self.current_user_info['first_name']} {self.current_user_info['last_name']}"
        )
        # self.initialize_simulations_progresses_thread()
        # self.initialize_simulation_overview()
        # self.initialize_simulation_results()

    def load_local_schematisation(
        self,
        local_schematisation=None,
        action=SchematisationLoaderActions.LOADED,
        custom_geopackage_filepath=None,
    ):
        # This function can also be called externally on the plugin instance
        self.current_local_schematisation = (
            self.schematisation_loader.load_local_schematisation(
                self.communication,
                local_schematisation,
                action,
                custom_geopackage_filepath,
            )
        )
        self.update_schematisation_view()

    @login_required
    def download_schematisation(self, *args, **kwargs):
        self.current_local_schematisation = (
            self.schematisation_loader.download_schematisation(
                self.threedi_api, self.organisations, self.communication
            )
        )
        self.update_schematisation_view()

    @login_required
    def new_schematisation(self, *args, **kwargs):
        local_schematisation = self.schematisation_loader.new_schematisation(
            self.threedi_api, self.organisations
        )
        if local_schematisation:
            self.current_local_schematisation = local_schematisation
            self.update_schematisation_view()

    @login_required
    def upload_schematisation(self, *args, **kwargs):
        # TODO
        # if self.upload_dlg is None:
        upload_dlg = SchematisationUploadDialog(
            self.threedi_api,
            self.current_local_schematisation,
            self.organisations,
            self.communication,
            self,
        )
        upload_dlg.load_local_schematisation_required.connect(
            self.load_local_schematisation
        )
        upload_dlg.update_schematisation_view_required.connect(
            self.update_schematisation_view
        )
        upload_dlg.exec()

    def update_schematisation_view(self):
        """Method for updating loaded schematisation labels."""
        if self.current_local_schematisation:
            schema_name = self.current_local_schematisation.name
            schema_dir = self.current_local_schematisation.main_dir
            schema_label_text = f'<a href="file:///{schema_dir}">{schema_name}</a>'
            schema_tooltip = f"{schema_name}\n{schema_dir}"
            self.label_schematisation.setText(schema_label_text)
            self.label_schematisation.setOpenExternalLinks(True)
            self.label_schematisation.setToolTip(schema_tooltip)
            if self.current_local_schematisation.wip_revision:
                self.label_revision.setText(
                    str(self.current_local_schematisation.wip_revision.number) or ""
                )
            else:
                self.label_revision.setText("")
        else:
            self.label_schematisation.setText("")
            self.label_schematisation.setToolTip("")
            self.label_revision.setText("")

    def on_manage(self):
        """Open 3Di management webpage."""
        url = QSettings().value("threedi/base_url")
        if url:
            url = f"{MANAGEMENT_URL_PREFIX}{url}"
            webbrowser.open(url)

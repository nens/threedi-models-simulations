from pathlib import Path

from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDialog, QDockWidget

from threedi_models_simulations.schematisation_loader import SchematisationLoader
from threedi_models_simulations.widgets.login import LogInDialog

FORM_CLASS, _ = uic.loadUiType(
    Path(__file__).parent / "dock.ui",
)


class DockWidget(QDockWidget, FORM_CLASS):
    def __init__(self, parent, iface):
        super().__init__(parent)
        self.setupUi(self)

        self.iface = iface
        self.threedi_api = None
        self.current_user_info = None
        self.organisations = {}
        self.schematisation_loader = SchematisationLoader(self)

        self.btn_log_in_out.clicked.connect(self.on_log_in_log_out)
        self.btn_load_schematisation.clicked.connect(self.load_local_schematisation)

    def on_log_in_log_out(self):
        """Trigger log-in or log-out action."""
        if self.threedi_api is None:
            self.on_log_in()
        else:
            self.on_log_out()

    def on_log_in(self):
        log_in_dialog = LogInDialog(self)
        if log_in_dialog.exec() == QDialog.DialogCode.Accepted:
            self.threedi_api = log_in_dialog.get_api()
            self.current_user_info = log_in_dialog.get_user_info()
            self.organisations = log_in_dialog.get_organisations()

            self.initialize_authorized_view()

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

    def load_local_schematisation(self):
        if self.schematisation_loader.load_local_schematisation():
            self.plugin_dock.update_schematisation_view()

from pathlib import Path

from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDockWidget

from threedi_models_simulations.widgets.login import LogInDialog

FORM_CLASS, _ = uic.loadUiType(
    Path(__file__).parent / "dock.ui",
)


class DockWidget(QDockWidget, FORM_CLASS):
    def __init__(self, parent, iface):
        super().__init__(parent)
        self.iface = iface

        self.setupUi(self)

        # Set logo
        # path_3di_logo = str(PLUGIN_DIR / "icons" / "icon.png")
        # logo_3di = QPixmap(path_3di_logo)
        # logo_3di = logo_3di.scaledToHeight(30)
        # self.logo.setPixmap(logo_3di)

        self.btn_log_in_out.clicked.connect(self.on_log_in_log_out)

    def on_log_in_log_out(self):
        """Trigger log-in or log-out action."""
        # if self.threedi_api is None:
        self.on_log_in()
        # else:
        #    self.on_log_out()

    def on_log_in(self):
        """Handle logging-in."""
        log_in_dialog = LogInDialog(self)
        log_in_dialog.open()
        # QTimer.singleShot(10, log_in_dialog.log_in_threedi)
        log_in_dialog.exec()
        # if log_in_dialog.LOGGED_IN:
        #     self.threedi_api = log_in_dialog.threedi_api
        #     self.current_user = log_in_dialog.user
        #     self.current_user_first_name = log_in_dialog.user_first_name
        #     self.current_user_last_name = log_in_dialog.user_last_name
        #     self.current_user_full_name = log_in_dialog.user_full_name
        #     self.organisations = log_in_dialog.organisations
        #     self.initialize_authorized_view()

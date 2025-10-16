from qgis.PyQt.QtCore import Qt, QTimer, pyqtSignal
from qgis.PyQt.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

from threedi_models_simulations.workers.login import LoginWorker


class LogInDialog(QDialog):
    settings_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.threedi_api = None
        self.user_info = None
        self.organisations = {}

        self.setWindowTitle("Log in")

        gridLayout = QVBoxLayout(self)

        bar_widget = QWidget(self)
        bar_layout = QHBoxLayout(bar_widget)
        bar_widget.setLayout(bar_layout)

        # Spacers and Progress Bar
        bar_layout.addItem(
            QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        )
        self.log_pbar = QProgressBar(self)
        self.log_pbar.setMinimumSize(200, 20)
        self.log_pbar.setMaximum(100)
        self.log_pbar.setValue(0)
        self.log_pbar.setTextVisible(False)
        bar_layout.addWidget(self.log_pbar)
        bar_layout.addItem(
            QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        )

        gridLayout.addWidget(bar_widget)

        msg_widget = QWidget(self)
        msg_widget.setStyleSheet("QWidget {background-color: white;}")

        verticalLayout = QVBoxLayout(msg_widget)

        self.log_msg = QLabel("Logging you in..", msg_widget)
        self.log_msg.setAlignment(Qt.AlignCenter)
        verticalLayout.addWidget(self.log_msg)

        self.fetch_msg = QLabel("Fetching organisations..", msg_widget)
        self.fetch_msg.setAlignment(Qt.AlignCenter)
        self.fetch_msg.setVisible(False)
        verticalLayout.addWidget(self.fetch_msg)

        self.done_msg = QLabel("Done", msg_widget)
        self.done_msg.setAlignment(Qt.AlignCenter)
        self.done_msg.setVisible(False)
        verticalLayout.addWidget(self.done_msg)

        vSpacer2 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        verticalLayout.addItem(vSpacer2)

        msg_widget.setLayout(verticalLayout)
        gridLayout.addWidget(msg_widget)

    def get_user_info(self):
        return self.user_info

    def get_organisations(self):
        return self.organisations

    def get_api(self):
        return self.threedi_api

    def exec(self):
        self.login()
        return super().exec()

    def login(self):
        self.fetch_msg.hide()
        self.done_msg.hide()
        self.log_pbar.setValue(25)

        self.worker = LoginWorker()
        self.worker.api_success.connect(self.on_api_success)
        self.worker.settings_requested.connect(self.settings_requested)
        self.worker.profile_success.connect(self.on_profile_success)
        self.worker.org_success.connect(self.on_organisation_success)
        self.worker.error.connect(self.on_error)
        self.worker.start()

    def on_api_success(self, api):
        self.threedi_api = api

    def on_profile_success(self, user_info):
        self.user_info = user_info

        self.log_pbar.setValue(50)

    def on_organisation_success(self, orgs):
        self.organisations = orgs

        self.log_pbar.setValue(100)
        self.fetch_msg.show()
        self.done_msg.show()
        self.log_pbar.setValue(100)
        QTimer.singleShot(1000, self.accept)

    def on_error(self, msg):
        QMessageBox.warning(self, "Error", msg)
        QTimer.singleShot(1000, self.reject)

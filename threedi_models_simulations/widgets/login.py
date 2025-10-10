from qgis.PyQt.QtCore import Qt, QThread, QTimer, pyqtSignal
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
from threedi_api_client import ThreediApi
from threedi_api_client.openapi import ApiException

from threedi_models_simulations.authentication import get_3di_auth
from threedi_models_simulations.threedi_api_utils import (
    extract_error_message,
    get_api_client_with_personal_api_token,
    paginated_fetch,
)
from threedi_models_simulations.widgets.settings import api_url


class AuthorizationException(Exception):
    pass


class LogInDialog(QDialog):
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


class LoginWorker(QThread):
    api_success = pyqtSignal(ThreediApi)
    profile_success = pyqtSignal(dict)
    org_success = pyqtSignal(dict)
    error = pyqtSignal(str)

    def run(self):
        try:
            username, personal_api_token = get_3di_auth()
            if not username or not personal_api_token:
                raise AuthorizationException("Personal API Key is not set.")

            threedi_api = get_api_client_with_personal_api_token(
                personal_api_token, api_url()
            )
            self.api_success.emit(threedi_api)

            user_profile = threedi_api.auth_profile_list()
            user_info = {
                "username": user_profile.username,
                "first_name": user_profile.first_name,
                "last_name": user_profile.last_name,
            }

            self.profile_success.emit(user_info)
            organisations = paginated_fetch(threedi_api.organisations_list)
            orgs = {org.unique_id: org for org in organisations}
            self.org_success.emit(orgs)

        except ApiException as e:
            api_url_error_message = (
                f"Error: Invalid Base API URL '{api_url()}'. "
                f"The 3Di API expects that the version is not included. "
                f"Please change the Base API URL in the 3Di Models and Simulations plugin settings."
            )
            ssl_error_message = (
                "An error occurred. This specific error is probably caused by issues with an expired SSL "
                "certificate that has not properly been removed by your operating system. Please ask your system "
                "administrator to remove this expired SSL certificate manually. Instructions can be found here: "
                "https://docs.3di.live/f_problem_solving.html#connecting-to-the-3di-api"
            )
            if e.status == 404:
                error_msg = api_url_error_message
            else:
                error_msg = extract_error_message(e)
            if "SSLError" in error_msg:
                error_msg = f"{ssl_error_message}\n\n{error_msg}"
            self.error.emit(error_msg)
        except AuthorizationException:
            self.error.emit(
                "Personal API Key is not filled. Please set it in the Settings Dialog."
            )
            # self.plugin_dock.plugin_settings.exec_()  # TODO
        except Exception as e:
            if "THREEDI_API_HOST" in str(e):
                error_msg = api_url_error_message
            else:
                error_msg = f"Error: {e}"
            self.error.emit(error_msg)

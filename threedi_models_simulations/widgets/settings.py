import os
import webbrowser
from tempfile import gettempdir

from qgis.PyQt.QtCore import QSettings, Qt, pyqtSignal
from qgis.PyQt.QtWidgets import (
    QDialog,
    QFileDialog,
    QGridLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QSpinBox,
)

from threedi_models_simulations.authentication import get_3di_auth, set_3di_auth
from threedi_models_simulations.constants import (
    API_URL_PREFIX,
    DEFAULT_BASE_URL,
    DEFAULT_UPLOAD_TIMEOUT,
    MANAGEMENT_URL_PREFIX,
)
from threedi_models_simulations.utils.file import is_writable


def settings_are_valid() -> bool:
    work_dir = QSettings().value("threedi/working_dir", "")
    if not work_dir or not os.path.exists(work_dir) or not is_writable(work_dir):
        return False
    return True


def save_3di_settings(entry_name, value):
    QSettings().setValue(f"threedi/{entry_name}", value)


def read_3di_settings(entry_name, default_value=""):
    return QSettings().value(f"threedi/{entry_name}", default_value)


def api_url():
    return API_URL_PREFIX + QSettings().value("threedi/base_url", DEFAULT_BASE_URL)


def wss_url():
    return api_url().replace("https:", "wss:").replace("http:", "ws:")


class SettingsDialog(QDialog):
    settings_changed = pyqtSignal()

    def __init__(self, parent=None):
        super(SettingsDialog, self).__init__(parent)
        self.setWindowTitle("3Di Models and Simulations settings")
        self.resize(600, 300)
        layout = QGridLayout(self)

        layout.addWidget(QLabel("Base URL:", self), 0, 0)

        self.base_url_le = QLineEdit(self)
        layout.addWidget(self.base_url_le, 0, 1, 1, 4)

        label = QLabel(
            "WARNING: Please note that changes will take effect after next logging in.",
            self,
        )
        label.setWordWrap(True)
        layout.addWidget(label, 2, 1, 1, 4)

        layout.addWidget(QLabel("Uploads processing timeout:", self), 5, 0)

        self.upload_timeout_sb = QSpinBox(self)
        self.upload_timeout_sb.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.upload_timeout_sb.setMinimum(1)
        self.upload_timeout_sb.setMaximum(86400)
        self.upload_timeout_sb.setValue(900)
        self.upload_timeout_sb.setSuffix(" seconds")
        layout.addWidget(self.upload_timeout_sb, 5, 3, 1, 2)

        layout.addWidget(QLabel("Working directory:", self), 6, 0)

        self.working_dir_le = QLineEdit(self)
        self.working_dir_le.setReadOnly(True)
        self.working_dir_le.setPlaceholderText(
            "Place to store all schematisations and results"
        )
        layout.addWidget(self.working_dir_le, 6, 1, 1, 3)

        browse_pb = QPushButton("Browse", self)
        layout.addWidget(browse_pb, 6, 4)

        layout.addWidget(QLabel("API Key:", self), 7, 0)

        self.pak_label = QLabel('<span style="color:#ff0000;">✕ Not found</span>', self)
        layout.addWidget(self.pak_label, 7, 1)

        set_pak_pb = QPushButton("Set...", self)
        layout.addWidget(set_pak_pb, 7, 3)

        obtain_pak_pb = QPushButton("Obtain...", self)
        layout.addWidget(obtain_pak_pb, 7, 4)

        vertical_spacer = QSpacerItem(
            20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding
        )
        layout.addItem(vertical_spacer, 10, 0)

        defaults_pb = QPushButton("Use defaults", self)
        layout.addWidget(defaults_pb, 11, 0)

        horizontal_spacer = QSpacerItem(
            40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum
        )
        layout.addItem(horizontal_spacer, 11, 1)

        cancel_pb = QPushButton("Cancel", self)
        layout.addWidget(cancel_pb, 11, 3)

        save_pb = QPushButton("Save", self)
        layout.addWidget(save_pb, 11, 4)

        browse_pb.clicked.connect(self.set_working_directory)
        set_pak_pb.clicked.connect(self.set_personal_api_key)
        obtain_pak_pb.clicked.connect(self.obtain_personal_api_key)
        defaults_pb.clicked.connect(self.restore_defaults)
        cancel_pb.clicked.connect(self.reject)
        save_pb.clicked.connect(self.accept)

        self.load_settings()

    def load_settings(self):
        base_url = QSettings().value("threedi/base_url", DEFAULT_BASE_URL)
        self.base_url_le.setText(base_url)
        self.working_dir_le.setText(QSettings().value("threedi/working_dir", ""))
        upload_timeout = QSettings().value(
            "threedi/timeout", DEFAULT_UPLOAD_TIMEOUT, type=int
        )
        self.upload_timeout_sb.setValue(upload_timeout)
        _, password = get_3di_auth()
        if password:
            self.set_personal_api_key_label(True)
        else:
            self.set_personal_api_key_label(False)

    def set_personal_api_key_label(self, personal_api_key_available: bool):
        """Setting Personal API Key label text."""
        if personal_api_key_available:
            label_txt = """<html><head/><body><p><span style=" color:#00aa00;">
            ✓ Available</span></p></body></html>"""
        else:
            label_txt = """<html><head/><body><p><span style=" color:#ff0000;">
            ✕ Not found</span></p></body></html>"""
        self.pak_label.setText(label_txt)

    def obtain_personal_api_key(self):
        """Open website where user can get his Personal API Key."""
        webbrowser.open(f"{self.management_url}/personal_api_keys/")

    def set_working_directory(self):
        work_dir = QFileDialog.getExistingDirectory(
            self, "Select Working Directory", self.working_dir_le.text()
        )
        if work_dir:
            if not is_writable(work_dir):
                QMessageBox.warning(
                    self,
                    "Warning",
                    "Can't write to the selected location. Please select a folder to which you have write permission.",
                )
                return
            self.working_dir_le.setText(work_dir)

    def save_settings(self):
        """Saving plugin settings in QSettings."""
        working_dir = self.working_dir_le.text()
        upload_timeout = self.upload_timeout_sb.value()
        QSettings().setValue("threedi/base_url", self.base_url)
        QSettings().setValue("threedi/working_dir", working_dir)
        QSettings().setValue("threedi/timeout", upload_timeout)

    def accept(self):
        """Accepting changes and closing dialog."""
        if self.settings_are_valid():
            self.save_settings()
            self.settings_changed.emit()
            super().accept()

    def restore_defaults(self):
        """Restoring default settings values."""
        self.base_url_le.setText(DEFAULT_BASE_URL)
        self.working_dir_le.setText(SettingsDialog.default_working_dir() or "")
        self.upload_timeout_sb.setValue(DEFAULT_UPLOAD_TIMEOUT)

    @staticmethod
    def default_working_dir():
        """Create and return default working directory location."""
        user_dir = os.path.expanduser("~")
        try:
            threedi_working_dir = os.path.join(user_dir, "Documents", "3Di")
            os.makedirs(threedi_working_dir, exist_ok=True)
            try_to_write(threedi_working_dir)
        except (PermissionError, OSError):
            threedi_working_dir = gettempdir()
        return threedi_working_dir

    def set_personal_api_key(self):
        """Setting active Personal API Key."""
        pak, accept = QInputDialog.getText(
            self, "Personal API Key", "Paste your Personal API Key:"
        )
        if accept is False:
            return
        set_3di_auth(pak)
        self.set_personal_api_key_label(True)

    @property
    def management_url(self):
        url = self.base_url
        if url:
            url = f"{MANAGEMENT_URL_PREFIX}{url}"
        else:
            url = f"{MANAGEMENT_URL_PREFIX}{DEFAULT_BASE_URL}"
        return url

    @property
    def base_url(self):
        url = self.base_url_le.text()
        if url.startswith(API_URL_PREFIX):
            url = url[len(API_URL_PREFIX) :]
        return url

    def settings_are_valid(self):
        """Check validity of the settings."""
        if not self.working_dir_le.text() or not os.path.exists(
            self.working_dir_le.text()
        ):
            QMessageBox.warning(
                "Missing or invalid working directory. Please set it up before running the plugin.",
                self,
            )
            return False
        else:
            return True

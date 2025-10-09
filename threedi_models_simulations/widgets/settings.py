from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (
    QDialog,
    QGridLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QSpinBox,
)


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super(SettingsDialog, self).__init__(parent)
        self.setWindowTitle("3Di Models and Simulations settings")
        self.resize(600, 300)

        layout = QGridLayout(self)

        self.label = QLabel("Base URL:", self)
        layout.addWidget(self.label, 0, 0)

        self.base_url_le = QLineEdit(self)
        layout.addWidget(self.base_url_le, 0, 1, 1, 4)

        self.label_2 = QLabel(
            "WARNING: Please note that changes will take effect after next logging in.",
            self,
        )
        self.label_2.setWordWrap(True)
        layout.addWidget(self.label_2, 2, 1, 1, 4)

        self.label_3 = QLabel("Uploads processing timeout:", self)
        layout.addWidget(self.label_3, 5, 0)

        self.upload_timeout_sb = QSpinBox(self)
        self.upload_timeout_sb.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.upload_timeout_sb.setMinimum(1)
        self.upload_timeout_sb.setMaximum(86400)
        self.upload_timeout_sb.setValue(900)
        self.upload_timeout_sb.setSuffix(" seconds")
        layout.addWidget(self.upload_timeout_sb, 5, 3, 1, 2)

        # Row 6 - Working directory
        self.label_4 = QLabel("Working directory:", self)
        layout.addWidget(self.label_4, 6, 0)

        self.working_dir_le = QLineEdit(self)
        self.working_dir_le.setReadOnly(True)
        self.working_dir_le.setPlaceholderText(
            "Place to store all schematisations and results"
        )
        layout.addWidget(self.working_dir_le, 6, 1, 1, 3)

        self.browse_pb = QPushButton("Browse", self)
        layout.addWidget(self.browse_pb, 6, 4)

        self.label_5 = QLabel("API Key:", self)
        layout.addWidget(self.label_5, 7, 0)

        self.pak_label = QLabel('<span style="color:#ff0000;">✕ Not found</span>', self)
        layout.addWidget(self.pak_label, 7, 1)

        self.set_pak_pb = QPushButton("Set...", self)
        layout.addWidget(self.set_pak_pb, 7, 3)

        self.obtain_pak_pb = QPushButton("Obtain...", self)
        layout.addWidget(self.obtain_pak_pb, 7, 4)

        vertical_spacer = QSpacerItem(
            20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding
        )
        layout.addItem(vertical_spacer, 10, 0)

        self.defaults_pb = QPushButton("Use defaults", self)
        layout.addWidget(self.defaults_pb, 11, 0)

        horizontal_spacer = QSpacerItem(
            40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum
        )
        layout.addItem(horizontal_spacer, 11, 1)

        self.cancel_pb = QPushButton("Cancel", self)
        layout.addWidget(self.cancel_pb, 11, 3)

        self.save_pb = QPushButton("Save", self)
        layout.addWidget(self.save_pb, 11, 4)

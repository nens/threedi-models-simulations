from pathlib import Path

from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDockWidget

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

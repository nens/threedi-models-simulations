import os

from qgis.PyQt.QtGui import QIcon

PLUGIN_NAME = "3Di Models & Simulations"

# Base path for the icons directory
ICONS_DIR = os.path.join(os.path.dirname(__file__), "icons")
plugin_icon = QIcon(os.path.join(ICONS_DIR, "icon.png"))
logo_icon = QIcon(os.path.join(ICONS_DIR, "logo.svg"))

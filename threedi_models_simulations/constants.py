import os

from qgis.PyQt.QtGui import QIcon

PLUGIN_NAME = "3Di Models & Simulations"

# Base path for the icons directory
ICONS_DIR = os.path.join(os.path.dirname(__file__), "icons")
PLUGIN_ICON = QIcon(os.path.join(ICONS_DIR, "icon.png"))
LOGO_ICON = QIcon(os.path.join(ICONS_DIR, "logo.svg"))

API_URL_PREFIX = "https://api."
MANAGEMENT_URL_PREFIX = "https://management."
LIVE_URL_PREFIX = "https://www."
DEFAULT_BASE_URL = "3di.live"
DEFAULT_UPLOAD_TIMEOUT = 900

DOWNLOAD_CHUNK_SIZE = 1024**2

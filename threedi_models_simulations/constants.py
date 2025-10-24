import os

from qgis.PyQt.QtGui import QIcon

PLUGIN_NAME = "3Di Models & Simulations"
PLUGIN_PATH = os.path.dirname(os.path.realpath(__file__))

# Base path for the icons directory
ICONS_DIR = os.path.join(os.path.dirname(__file__), "icons")
PLUGIN_ICON = QIcon(os.path.join(ICONS_DIR, "icon.png"))
LOGO_ICON = QIcon(os.path.join(ICONS_DIR, "logo.svg"))

API_URL_PREFIX = "https://api."
MANAGEMENT_URL_PREFIX = "https://management."
LIVE_URL_PREFIX = "https://www."
DEFAULT_BASE_URL = "3di.live"
DEFAULT_UPLOAD_TIMEOUT = 900

CACHE_PATH = os.path.join(PLUGIN_PATH, "_cached_data")
DOWNLOAD_CHUNK_SIZE = 1024**2
UPLOAD_CHUNK_SIZE = 1024**2
MAX_SCHEMATISATION_MODELS = 3
USER_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
API_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%f%z"

RADAR_ID = "d6c2347d-7bd1-4d9d-a1f6-b342c865516f"

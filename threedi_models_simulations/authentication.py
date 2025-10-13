from qgis.core import QgsApplication, QgsAuthMethodConfig
from qgis.PyQt.QtCore import QSettings

# TODO: @api_client_required wrapper


def get_3di_auth():
    """Getting 3Di credentials from the QGIS Authorization Manager."""
    authcfg = QSettings().value("threedi/authcfg", None)
    auth_manager = QgsApplication.authManager()
    cfg = QgsAuthMethodConfig()
    auth_manager.loadAuthenticationConfig(authcfg, cfg, True)
    username = cfg.config("username")
    password = cfg.config("password")
    return username, password


def set_3di_auth(personal_api_key, username="__key__"):
    """Setting 3Di credentials in the QGIS Authorization Manager."""
    settings = QSettings()
    authcfg = settings.value("threedi/authcfg", None)
    cfg = QgsAuthMethodConfig()
    auth_manager = QgsApplication.authManager()
    auth_manager.setMasterPassword()
    auth_manager.loadAuthenticationConfig(authcfg, cfg, True)

    if cfg.id():
        cfg.setConfig("username", username)
        cfg.setConfig("password", personal_api_key)
        auth_manager.updateAuthenticationConfig(cfg)
    else:
        cfg.setMethod("Basic")
        cfg.setName("3Di Personal Api Key")
        cfg.setConfig("username", username)
        cfg.setConfig("password", personal_api_key)
        auth_manager.storeAuthenticationConfig(cfg)
        settings.setValue("threedi/authcfg", cfg.id())

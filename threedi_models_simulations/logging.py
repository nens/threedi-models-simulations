from qgis.core import Qgis, QgsMessageLog


class Logger:
    @staticmethod
    def log_warn(msg: str):
        QgsMessageLog.logMessage(msg, "plugin", Qgis.MessageLevel.Warning)

    @staticmethod
    def log_info(msg: str):
        QgsMessageLog.logMessage(msg, "plugin", Qgis.MessageLevel.Info)

    @staticmethod
    def log_critical(msg: str):
        QgsMessageLog.logMessage(msg, "plugin", Qgis.MessageLevel.Critical)

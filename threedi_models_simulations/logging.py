from enum import Enum

from qgis.core import Qgis, QgsMessageLog
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QBrush, QColor, QStandardItem, QStandardItemModel


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


class LogLevels(Enum):
    """Model Checker log levels."""

    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    FUTURE_ERROR = "FUTURE_ERROR"


class ListViewLogger(object):
    """Utility class for logging in ListView"""

    def __init__(self, list_view=None):
        self.list_view = list_view
        self.model = QStandardItemModel()
        self.list_view.setModel(self.model)

    def clear(self):
        """Clear list view model."""
        self.list_view.model().clear()

    def log_info(self, msg, log_text_color=QColor(Qt.darkGreen)):
        """Showing info message bar."""
        if self.list_view is not None:
            item = QStandardItem(msg)
            item.setForeground(QBrush(log_text_color))
            self.model.appendRow([item])
        else:
            print(msg)

    def log_warn(self, msg, log_text_color=QColor(Qt.darkYellow)):
        """Showing warning message bar."""
        if self.list_view is not None:
            item = QStandardItem(msg)
            item.setForeground(QBrush(log_text_color))
            self.model.appendRow([item])
        else:
            print(msg)

    def log_error(self, msg, log_text_color=QColor(Qt.red)):
        """Showing error message bar."""
        if self.list_view is not None:
            item = QStandardItem(msg)
            item.setForeground(QBrush(log_text_color))
            self.model.appendRow([item])
        else:
            print(msg)


class TreeViewLogger(object):
    """Utility class for logging in TreeView"""

    def __init__(self, tree_view=None, header=None):
        self.tree_view = tree_view
        self.header = header
        self.model = QStandardItemModel()
        self.tree_view.setModel(self.model)
        self.levels_colors = {
            LogLevels.INFO.value: QColor(Qt.black),
            LogLevels.WARNING.value: QColor(229, 144, 80),
            LogLevels.ERROR.value: QColor(Qt.red),
            LogLevels.FUTURE_ERROR.value: QColor(102, 51, 153),
        }
        self.initialize_view()

    def clear(self):
        """Clear list view model."""
        self.tree_view.model().clear()

    def initialize_view(self):
        """Clear list view model and set header columns if available."""
        self.tree_view.model().clear()
        if self.header:
            self.tree_view.model().setHorizontalHeaderLabels(self.header)

    def log_result_row(self, row, log_level):
        """Show row data with proper log level styling."""
        text_color = self.levels_colors[log_level]
        if self.tree_view is not None:
            items = []
            for value in row:
                item = QStandardItem(str(value))
                item.setForeground(QBrush(text_color))
                items.append(item)
            self.model.appendRow(items)
            for i in range(len(self.header)):
                self.tree_view.resizeColumnToContents(i)
        else:
            print(row)

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QColor, QPalette
from qgis.PyQt.QtWidgets import (
    QApplication,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionProgressBar,
)


class DownloadProgressDelegate(QStyledItemDelegate):
    """Class with definition of the custom downloading results progress bar item that can be inserted into the model."""

    def paint(self, painter, option, index):
        new_percentage = int(index.data(Qt.UserRole))
        pbar = QStyleOptionProgressBar()
        pbar.rect = option.rect
        pbar.minimum = 0
        pbar.maximum = 100
        default_color = QColor(0, 140, 255)

        if new_percentage < 0:
            new_percentage = 0
            pbar_color = Qt.lightGray
            ptext = f"Ready to download"
        elif 0 <= new_percentage < 100:
            pbar_color = default_color
            ptext = f"Downloading ({new_percentage}%) .."
        elif new_percentage == 100:
            pbar_color = QColor(10, 180, 40)
            ptext = f"Download finished"
        else:
            new_percentage = 100
            pbar_color = Qt.red
            ptext = f"Download failed"

        pbar.progress = new_percentage
        pbar.text = ptext
        pbar.textVisible = True
        palette = pbar.palette
        palette.setColor(QPalette.Highlight, pbar_color)
        pbar.palette = palette
        QApplication.style().drawControl(QStyle.CE_ProgressBar, pbar, painter)

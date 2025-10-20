from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QColor, QPalette
from qgis.PyQt.QtWidgets import (
    QApplication,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionProgressBar,
)

from threedi_models_simulations.workers.simulations import SimulationStatusName

PROGRESS_ROLE = Qt.UserRole + 1000


class SimulationProgressDelegate(QStyledItemDelegate):
    """Class with definition of the custom simulation progress bar item that can be inserted into the model."""

    def paint(self, painter, option, index):
        status_name, progress_percentage = index.data(PROGRESS_ROLE)
        new_percentage = int(progress_percentage)
        pbar = QStyleOptionProgressBar()
        pbar.rect = option.rect
        pbar.minimum = 0
        pbar.maximum = 100
        default_color = QColor(0, 140, 255)

        if status_name in {SimulationStatusName.CREATED.value}:
            pbar_color = default_color
            ptext = "Created simulation"
        elif status_name in {SimulationStatusName.STARTING.value}:
            pbar_color = default_color
            ptext = "Starting up simulation .."
        elif status_name in {
            SimulationStatusName.INITIALIZED.value,
            SimulationStatusName.POSTPROCESSING.value,
        }:
            pbar_color = default_color
            ptext = f"{new_percentage}%"
        elif status_name == SimulationStatusName.FINISHED.value:
            pbar_color = QColor(10, 180, 40)
            ptext = f"{new_percentage}%"
        elif status_name in {
            SimulationStatusName.ENDED.value,
            SimulationStatusName.STOPPED.value,
        }:
            pbar_color = Qt.gray
            ptext = f"{new_percentage}% (stopped)"
        elif status_name == SimulationStatusName.CRASHED.value:
            pbar_color = Qt.red
            ptext = f"{new_percentage}% (crashed)"
        else:
            pbar_color = Qt.lightGray
            ptext = f"{status_name}"

        pbar.progress = new_percentage
        pbar.text = ptext
        pbar.textVisible = True
        palette = pbar.palette
        palette.setColor(QPalette.Highlight, pbar_color)
        pbar.palette = palette
        QApplication.style().drawControl(QStyle.CE_ProgressBar, pbar, painter)

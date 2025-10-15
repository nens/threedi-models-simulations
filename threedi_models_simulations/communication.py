from qgis.core import Qgis
from qgis.PyQt.QtCore import QCoreApplication, Qt
from qgis.PyQt.QtGui import QBrush, QColor, QStandardItem, QStandardItemModel
from qgis.PyQt.QtWidgets import QMessageBox, QProgressBar, QPushButton
from qgis.utils import iface


def progress_bar_callback_factory(
    communication, minimum=0, maximum=100, clear_msg_bar=True
):
    """Callback function to track progress."""

    def progress_bar_callback(progres_value, message):
        communication.progress_bar(
            message, minimum, maximum, progres_value, clear_msg_bar=clear_msg_bar
        )
        QCoreApplication.processEvents()

    return progress_bar_callback


class UICommunication(object):
    def __init__(self, list_view=None):
        self.list_view = list_view
        # Automatically add bar_info/warn/error messages to a listview
        if self.list_view:
            self.model = QStandardItemModel()
            self.list_view.setModel(self.model)

    @staticmethod
    def custom_ask(parent, title, question, *buttons_labels):
        """Ask for custom operation confirmation."""
        msg_box = QMessageBox(parent)
        msg_box.setIcon(QMessageBox.Question)
        msg_box.setWindowTitle(title)
        msg_box.setTextFormat(Qt.RichText)
        msg_box.setText(question)
        for button_txt in buttons_labels:
            msg_box.addButton(QPushButton(button_txt), QMessageBox.YesRole)
        msg_box.exec()
        clicked_button = msg_box.clickedButton()
        clicked_button_text = clicked_button.text()
        return clicked_button_text

    @staticmethod
    def ask(parent, title, question, box_icon=QMessageBox.Question):
        """Ask for operation confirmation."""
        msg_box = QMessageBox(parent)
        msg_box.setIcon(box_icon)
        msg_box.setWindowTitle(title)
        msg_box.setTextFormat(Qt.RichText)
        msg_box.setText(question)
        msg_box.setStandardButtons(QMessageBox.No | QMessageBox.Yes)
        msg_box.setDefaultButton(QMessageBox.No)
        res = msg_box.exec_()
        if res == QMessageBox.No:
            return False
        else:
            return True

    @staticmethod
    def show_info(msg, parent, title):
        if iface is not None:
            QMessageBox.information(parent, title, msg)
        else:
            print(msg)

    @staticmethod
    def show_warn(msg, parent, title):
        if iface is not None:
            QMessageBox.warning(parent, title, msg)
        else:
            print(msg)

    @staticmethod
    def show_error(msg, parent, title):
        if iface is not None:
            QMessageBox.critical(parent, title, msg)
        else:
            print(msg)

    def bar_info(
        self,
        msg,
        context="3Di Models and Simulations",
        dur=5,
        log_text_color=QColor(Qt.black),
    ):
        if iface is not None:
            iface.messageBar().pushMessage(context, msg, level=Qgis.Info, duration=dur)
            if self.list_view:
                item = QStandardItem(msg)
                item.setForeground(QBrush(log_text_color))
                self.model.appendRow([item])
        else:
            print(msg)

    def bar_warn(
        self,
        msg,
        context="3Di Models and Simulations",
        dur=5,
        log_text_color=QColor(Qt.black),
    ):
        if iface is not None:
            iface.messageBar().pushMessage(
                context, msg, level=Qgis.Warning, duration=dur
            )
            if self.list_view:
                item = QStandardItem(msg)
                item.setForeground(QBrush(log_text_color))
                self.model.appendRow([item])
        else:
            print(msg)

    def bar_error(
        self,
        msg,
        context="3Di Models and Simulations",
        dur=5,
        log_text_color=QColor(Qt.black),
    ):
        if iface is not None:
            iface.messageBar().pushMessage(
                context, msg, level=Qgis.Critical, duration=dur
            )
            if self.list_view:
                item = QStandardItem(msg)
                item.setForeground(QBrush(log_text_color))
                self.model.appendRow([item])
        else:
            print(msg)

    def clear_message_bar(self):
        """Clearing message bar."""
        if iface is None:
            return
        iface.messageBar().clearWidgets()

    def progress_bar(
        self, msg, minimum=0, maximum=0, init_value=0, clear_msg_bar=False
    ):
        """Setting progress bar."""
        if iface is None:
            return None
        if clear_msg_bar:
            iface.messageBar().clearWidgets()
        pmb = iface.messageBar().createMessage(msg)
        pb = QProgressBar()
        pb.setMinimum(int(minimum))
        pb.setMaximum(int(maximum))
        pb.setValue(int(init_value))
        pb.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        pmb.layout().addWidget(pb)
        iface.messageBar().pushWidget(pmb, Qgis.Info)
        return pb

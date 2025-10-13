from qgis.core import Qgis
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QBrush, QColor, QStandardItem
from qgis.PyQt.QtWidgets import QMessageBox, QPushButton
from qgis.utils import iface


class UICommunication(object):
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

    @staticmethod
    def bar_info(msg, context="plugin", dur=5):
        if iface is not None:
            iface.messageBar().pushMessage(context, msg, level=Qgis.Info, duration=dur)
        else:
            print(msg)

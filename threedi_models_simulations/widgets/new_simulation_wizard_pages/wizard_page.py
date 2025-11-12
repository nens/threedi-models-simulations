from qgis.core import Qgis, QgsMessageLog
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QPalette
from qgis.PyQt.QtWidgets import (
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QTreeView,
    QVBoxLayout,
    QWizardPage,
)

from threedi_models_simulations.communication import UICommunication
from threedi_models_simulations.utils.general import SeparatorDelegate


class WizardPage(QWizardPage):
    def __init__(self, parent, show_steps: bool = False):
        super().__init__(parent)

        layout = QHBoxLayout()
        self.setLayout(layout)

        if show_steps:
            self.wizard_steps_widget = QGroupBox(self)
            self.wizard_steps_widget.setLayout(QVBoxLayout())
            self.wizard_steps_widget.setFixedWidth(250)

            layout.addWidget(self.wizard_steps_widget)

            self.wizard_steps_tree = QTreeView(self)
            self.wizard_steps_tree.setHeaderHidden(True)

            # Use the same background as standard widgets
            palette = self.wizard_steps_widget.palette()
            base_color = palette.color(
                QPalette.Window
            )  # This matches other widgets' gray background
            # base_color = self.wizard_steps_widget.palette().color(self.wizard_steps_widget.backgroundRole())
            palette.setColor(QPalette.Base, base_color)
            self.wizard_steps_tree.setPalette(palette)

            self.wizard_steps_tree.setFrameShape(QFrame.NoFrame)
            self.wizard_steps_tree.setSelectionMode(QTreeView.NoSelection)
            self.wizard_steps_tree.setFocusPolicy(Qt.NoFocus)
            self.wizard_steps_tree.setEditTriggers(QTreeView.NoEditTriggers)
            self.wizard_steps_tree.setIndentation(20)
            self.wizard_steps_tree.setRootIsDecorated(False)
            self.wizard_steps_tree.setItemDelegate(
                SeparatorDelegate(self.wizard_steps_tree)
            )
            self.wizard_steps_widget.layout().addWidget(self.wizard_steps_tree)

        else:
            self.wizard_steps_widget = None

        self.page_widget = QGroupBox(self)
        layout.addWidget(self.page_widget)

        # new pages need to set this flag preferably in the isComplete function.
        self._dirty = False
        self.initializing = False

    def get_page_widget(self):
        return self.page_widget

    def get_steps_widget(self):
        return self.wizard_steps_widget

    def get_steps_tree(self):
        return self.wizard_steps_tree

    def back_requires_save(self):
        if self.dirty:
            if UICommunication.ask(
                self,
                "Back pressed",
                "All changes will be lost when going back, would you like to save the current changes?",
            ):
                self.save_model()

    def cleanupPage(self):
        QgsMessageLog.logMessage(str(self.__class__) + "cleanup")
        if self.back_requires_save():
            self.save_model()

    def initializePage(self):
        QgsMessageLog.logMessage(str(self.__class__) + "initializePage")
        self.load_model()
        QgsMessageLog.logMessage(str(self.__class__) + "0 self.dirty = False")
        self.dirty = False
        self.initializing = True

    @property
    def dirty(self):
        return self._dirty and not self.wizard().backPressed

    @dirty.setter
    def dirty(self, value):
        self._dirty = value

    def validatePage(self):
        # When the user clicks Next or Finish to perform some last-minute validation. If it returns true, the next page is
        # shown (or the wizard finishes); otherwise, the current page stays up. After validation, the data needs to be stored
        # in the model.
        valid = self.validate_page()
        if not valid:
            return False
        self.save_model()
        QgsMessageLog.logMessage(str(self.__class__) + "1 self.dirty = False")
        self.dirty = False
        return True

    def isComplete(self):
        if not self.wizard():
            return self.is_complete()

        # isComplete is also called when the user pressed back on the next page
        if self.wizard().backPressed or self.initializing:
            QgsMessageLog.logMessage(str(self.__class__) + "3 self.dirty = False")
            self.dirty = False
            if self.wizard().backPressed:
                QgsMessageLog.logMessage(str(self.__class__) + "backpressed=false")
                self.wizard().backPressed = False
            if self.initializing:
                QgsMessageLog.logMessage(str(self.__class__) + "initializing=false")
                self.initializing = False
        else:
            QgsMessageLog.logMessage(str(self.__class__) + "-1 self.dirty = True")
            self.dirty = True

        return self.is_complete()

    def save_model(self):
        # Stores the UI in the model
        raise NotImplementedError("Subclasses must implement save_model()")

    def load_model(self):
        # Load the model into the UI
        raise NotImplementedError("Subclasses must implement load_model()")

    def validate_page(self):
        # When the user clicks Next or Finish to perform some last-minute validation. If it returns true, the next page is
        # shown (or the wizard finishes); otherwise, the current page stays up.
        raise NotImplementedError("Subclasses must implement validate_page()")

    def is_complete(self):
        # We also need to emit the QWizardPage::completeChanged() signal every time isComplete() may potentially return a different value,
        # so that the wizard knows that it must refresh the Next button. This requires us to add the following connect()
        # call to the SailingPage constructor:  connect(sailing, SIGNAL(selectionChanged()), this, SIGNAL(completeChanged()));
        raise NotImplementedError("Subclasses must implement is_complete()")

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
            self.wizard_steps_tree.setIndentation(20)  # remove indent
            self.wizard_steps_tree.setRootIsDecorated(False)
            self.wizard_steps_tree.setItemDelegate(
                SeparatorDelegate(self.wizard_steps_tree)
            )
            self.wizard_steps_widget.layout().addWidget(self.wizard_steps_tree)

        else:
            self.wizard_steps_widget = None

        self.page_widget = QGroupBox(self)
        layout.addWidget(self.page_widget)

    def get_page_widget(self):
        return self.page_widget

    def get_steps_widget(self):
        return self.wizard_steps_widget

    def get_steps_tree(self):
        return self.wizard_steps_tree

    def initializePage(self):
        # Fill the page with the current model
        raise NotImplementedError("Subclasses must implement initializePage()")

    def validatePage(self):
        # When the user clicks Next or Finish to perform some last-minute validation. If it returns true, the next page is
        # shown (or the wizard finishes); otherwise, the current page stays up. After validation, the data needs to be stored
        # in the model.
        raise NotImplementedError("Subclasses must implement validatePage()")

    def isComplete(self):
        # We also need to emit the QWizardPage::completeChanged() signal every time isComplete() may potentially return a different value,
        # so that the wizard knows that it must refresh the Next button. This requires us to add the following connect()
        # call to the SailingPage constructor:  connect(sailing, SIGNAL(selectionChanged()), this, SIGNAL(completeChanged()));
        raise NotImplementedError("Subclasses must implement isComplete()")

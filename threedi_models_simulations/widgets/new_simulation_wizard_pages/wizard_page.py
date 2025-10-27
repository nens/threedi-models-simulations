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
            self.wizard_steps_widget.setFixedWidth(200)

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
            self.wizard_steps_tree.setIndentation(0)  # remove indent
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
        raise NotImplementedError("Subclasses must implement initializePage()")

    def validatePage(self):
        raise NotImplementedError("Subclasses must implement validatePage()")

    def isComplete(self):
        raise NotImplementedError("Subclasses must implement isComplete()")

from qgis.PyQt.QtWidgets import QGroupBox, QHBoxLayout, QVBoxLayout, QWizardPage


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
        else:
            self.wizard_steps_widget = None

        self.page_widget = QGroupBox(self)
        layout.addWidget(self.page_widget)

    def get_page_widget(self):
        return self.page_widget

    def get_steps_widget(self):
        return self.wizard_steps_widget

    def initializePage(self):
        raise NotImplementedError("Subclasses must implement initializePage()")

    def validatePage(self):
        raise NotImplementedError("Subclasses must implement validatePage()")

    def isComplete(self):
        raise NotImplementedError("Subclasses must implement isComplete()")

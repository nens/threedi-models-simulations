from qgis.core import Qgis, QgsMessageLog
from qgis.PyQt.QtWidgets import (
    QCheckBox,
    QGridLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QRadioButton,
    QVBoxLayout,
)

from threedi_models_simulations.widgets.new_simulation_wizard_pages.wizard_page import (
    WizardPage,
)


class NamePage(WizardPage):
    def __init__(self, parent, new_sim):
        super().__init__(parent, show_steps=True)
        self.setTitle("Starting a new simulation")
        self.setSubTitle(
            r'You can find more information about setting projects and tags in the <a href="https://docs.3di.live/i_running_a_simulation.html#starting-a-simulation/">documentation</a>.'
        )
        self.new_sim = new_sim

        main_widget = self.get_page_widget()

        layout = QVBoxLayout()
        main_widget.setLayout(layout)

        layout.addWidget(QLabel("New simulation name", main_widget))
        self.name_le = QLineEdit(main_widget)
        layout.addWidget(self.name_le)
        self.name_le.textEdited.connect(self.completeChanged)

        layout.addWidget(QLabel("Project", main_widget))
        project_le = QLineEdit(main_widget)
        project_le.setPlaceholderText("Project name (optional)")
        layout.addWidget(project_le)

        layout.addWidget(QLabel("Tags", main_widget))
        tags_le = QLineEdit(main_widget)
        tags_le.setPlaceholderText("Comma-separated tags (optional)")
        layout.addWidget(tags_le)

        layout.addStretch()

    def initializePage(self):
        # Fill the page with the current model
        self.name_le.setText(self.new_sim.simulation.name)
        QgsMessageLog.logMessage("miauw", level=Qgis.Critical)
        return

    def validatePage(self):
        # when the user clicks Next or Finish to perform some last-minute validation. If it returns true, the next page is shown (or the wizard finishes); otherwise, the current page stays up.
        return True

    def isComplete(self):
        # We also need to emit the QWizardPage::completeChanged() signal every time isComplete() may potentially return a different value,
        # so that the wizard knows that it must refresh the Next button. This requires us to add the following connect()
        # call to the SailingPage constructor:  connect(sailing, SIGNAL(selectionChanged()), this, SIGNAL(completeChanged()));
        QgsMessageLog.logMessage(self.name_le.text(), level=Qgis.Critical)
        if len(self.name_le.text()) >= 1:
            return True
        return False

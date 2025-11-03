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
        self.project_le = QLineEdit(main_widget)
        self.project_le.setPlaceholderText("Project name (optional)")
        layout.addWidget(self.project_le)

        layout.addWidget(QLabel("Tags", main_widget))
        self.tags_le = QLineEdit(main_widget)
        self.tags_le.setPlaceholderText("Comma-separated tags (optional)")
        layout.addWidget(self.tags_le)

        layout.addStretch()

    def initializePage(self):
        self.name_le.setText(self.new_sim.simulation.name)
        # Note that project names are actually tags starting with "project:"
        tags_list = []
        for tag in self.new_sim.simulation.tags:
            if tag.startswith("project:"):
                self.project_le.setText(tag.split(":", 1)[-1].strip())
            else:
                tags_list.append(tag)

        self.tags_le.setText(",".join(tags_list))

    def validatePage(self):
        self.new_sim.simulation.name = self.name_le.text()
        self.new_sim.simulation.tags = [
            tag.strip() for tag in self.tags_le.text().split(",")
        ]
        if self.project_le.text():
            self.new_sim.simulation.tags.append("project:" + self.project_le.text())

        # as the tags have been cleaned up, reinitialize the UI components
        self.initializePage()

        return True

    def isComplete(self):
        if len(self.name_le.text()) >= 1:
            return True
        return False

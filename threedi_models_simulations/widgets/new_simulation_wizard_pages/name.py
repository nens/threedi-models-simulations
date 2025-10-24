from qgis.PyQt.QtWidgets import (
    QCheckBox,
    QGridLayout,
    QGroupBox,
    QLabel,
    QRadioButton,
    QVBoxLayout,
)

from threedi_models_simulations.widgets.new_simulation_wizard_pages.wizard_page import (
    WizardPage,
)


class NamePage(WizardPage):
    def __init__(self, parent):
        super().__init__(parent, show_steps=False)
        self.setTitle("Starting a new simulation")
        self.setSubTitle(
            r'You can find more information about setting projects and tags in the <a href="https://docs.3di.live/i_running_a_simulation.html#starting-a-simulation/">documentation</a>.'
        )

        main_widget = self.get_page_widget()

        layout = QVBoxLayout()
        main_widget.setLayout(layout)

        # Initial conditions
        init_cond_gb = QGroupBox("Initial conditions", main_widget)
        init_cond_layout = QVBoxLayout()
        water_levels_rb = QRadioButton("Initial water levels", init_cond_gb)
        saved_state_rb = QRadioButton("Used save state", init_cond_gb)
        init_cond_layout.addWidget(water_levels_rb)
        init_cond_layout.addWidget(saved_state_rb)
        init_cond_gb.setLayout(init_cond_layout)

        layout.addWidget(init_cond_gb)

    def initializePage(self):
        # Fill the page with the current model
        return

    def validatePage(self):
        return True

    def isComplete(self):
        # We also need to emit the QWizardPage::completeChanged() signal every time isComplete() may potentially return a different value,
        # so that the wizard knows that it must refresh the Next button. This requires us to add the following connect()
        # call to the SailingPage constructor:  connect(sailing, SIGNAL(selectionChanged()), this, SIGNAL(completeChanged()));
        return False

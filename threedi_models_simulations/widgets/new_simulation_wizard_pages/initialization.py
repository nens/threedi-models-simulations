from qgis.PyQt.QtWidgets import (
    QCheckBox,
    QGridLayout,
    QGroupBox,
    QLabel,
    QRadioButton,
    QVBoxLayout,
)

from threedi_models_simulations.utils.threedi_api import fetch_contracts
from threedi_models_simulations.widgets.new_simulation_wizard_pages.wizard_page import (
    WizardPage,
)


class InitializationPage(WizardPage):
    def __init__(self, parent, new_sim, threedi_api, organisation):
        super().__init__(parent, show_steps=False)
        self.setTitle("Starting a new simulation")
        self.setSubTitle(
            r'You can find more information about starting a simulation in the <a href="https://docs.3di.live/i_running_a_simulation.html#starting-a-simulation/">documentation</a>.'
        )

        self.new_sim = new_sim
        self.threedi_api = threedi_api
        self.organisation = organisation

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

        # Forcings
        forcings_gb = QGroupBox("Forcings", main_widget)
        forcings_layout = QGridLayout()
        forcings_gb.setLayout(forcings_layout)

        boundary_cond_cb = QCheckBox("Boundary conditions", forcings_gb)
        laterals_cb = QCheckBox("Laterals", forcings_gb)
        dwf_cb = QCheckBox("Dry weather flow", forcings_gb)
        rain_cb = QCheckBox("Rain", forcings_gb)
        wind_cb = QCheckBox("Wind", forcings_gb)
        leakage_cb = QCheckBox("Leakage", forcings_gb)
        leakage_cb.setEnabled(False)
        leakage_cb.setToolTip("This setting is retrieved from the selected template")
        sources_sinks_cb = QCheckBox("Sources and sinks", forcings_gb)
        sources_sinks_cb.setEnabled(False)
        sources_sinks_cb.setToolTip(
            "This setting is retrieved from the selected template"
        )
        local_time_rain_cb = QCheckBox("Local or time series rain", forcings_gb)
        local_time_rain_cb.setEnabled(False)
        local_time_rain_cb.setToolTip(
            "This setting is retrieved from the selected template"
        )

        forcings_layout.addWidget(boundary_cond_cb, 0, 0)
        forcings_layout.addWidget(laterals_cb, 1, 0)
        forcings_layout.addWidget(dwf_cb, 2, 0)

        forcings_layout.addWidget(rain_cb, 0, 1)
        forcings_layout.addWidget(wind_cb, 1, 1)
        forcings_layout.addWidget(leakage_cb, 2, 1)

        forcings_layout.addWidget(sources_sinks_cb, 0, 2, 1, 2)
        forcings_layout.addWidget(local_time_rain_cb, 1, 2, 1, 2)

        # Events
        events_gb = QGroupBox("Events", main_widget)
        events_layout = QGridLayout()
        events_gb.setLayout(events_layout)

        structure_controls_cb = QCheckBox("Structure controls", events_gb)
        breaches_cb = QCheckBox("Breaches", events_gb)
        obstacle_edits_cb = QCheckBox("Obstace edits", events_gb)
        raster_edits_cb = QCheckBox("Raster edits", events_gb)
        events_layout.addWidget(structure_controls_cb, 0, 0)
        events_layout.addWidget(breaches_cb, 1, 0)
        events_layout.addWidget(obstacle_edits_cb, 2, 0)
        events_layout.addWidget(raster_edits_cb, 0, 1, 1, 3)

        # Water quality
        self.wq_gb = QGroupBox("Water quality", main_widget)
        wq_layout = QGridLayout()
        self.wq_gb.setLayout(wq_layout)

        wq_layout.addWidget(QLabel("Add substrances to:", self.wq_gb), 0, 0)

        initial_water_sub_cb = QCheckBox("Initial water", self.wq_gb)
        boundary_cond_sub_cb = QCheckBox("Boundary conditions", self.wq_gb)
        lateral_cond_sub_cb = QCheckBox("Laterals", self.wq_gb)
        dwf_sub_cb = QCheckBox("Dry weather flow", self.wq_gb)
        rain_sub_cb = QCheckBox("Rain", self.wq_gb)
        evaporation_seepage_sub_cb = QCheckBox("Evaporation and seepage", self.wq_gb)
        leakage_sub_cb = QCheckBox("Leakage", self.wq_gb)

        wq_layout.addWidget(initial_water_sub_cb, 1, 0)
        wq_layout.addWidget(boundary_cond_sub_cb, 2, 0)
        wq_layout.addWidget(lateral_cond_sub_cb, 3, 0)

        wq_layout.addWidget(dwf_sub_cb, 1, 1)
        wq_layout.addWidget(rain_sub_cb, 2, 1)
        wq_layout.addWidget(evaporation_seepage_sub_cb, 3, 1)

        wq_layout.addWidget(leakage_sub_cb, 1, 2, 1, 2)

        layout.addWidget(init_cond_gb)
        layout.addWidget(forcings_gb)
        layout.addWidget(events_gb)
        layout.addWidget(self.wq_gb)

    def initializePage(self):
        # Disable substance UI if not in organisation contract
        self.check_substance_contract()

    def validatePage(self):
        # set model
        return True

    def isComplete(self):
        # We also need to emit the QWizardPage::completeChanged() signal every time isComplete() may potentially return a different value,
        # so that the wizard knows that it must refresh the Next button. This requires us to add the following connect()
        # call to the SailingPage constructor:  connect(sailing, SIGNAL(selectionChanged()), this, SIGNAL(completeChanged()));
        return True

    def check_substance_contract(self):
        contracts = fetch_contracts(
            self.threedi_api, organisation__unique_id=self.organisation.unique_id
        )
        self.has_water_quality_license = False
        for contract in contracts:
            if "waterquality" in contract.scope:
                self.has_water_quality_license = True
                break

        if not self.has_water_quality_license:
            self.wq_gb.setEnabled(False)
            for checkbox in self.wq_gb.findChildren(QCheckBox):
                checkbox.setChecked(False)
                checkbox.setEnabled(False)

            self.wq_gb.setToolTip(
                "Your organisation's contract does not include water quality simulations. Please get in touch to be informed about the possibilities."
            )

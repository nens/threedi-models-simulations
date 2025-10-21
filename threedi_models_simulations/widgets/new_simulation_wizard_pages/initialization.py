from qgis.PyQt.QtWidgets import (
    QCheckBox,
    QGridLayout,
    QGroupBox,
    QLabel,
    QRadioButton,
    QVBoxLayout,
    QWizardPage,
)


class InitializationPage(QWizardPage):
    def __init__(self, parent):
        super().__init__(parent)
        self.setTitle("Starting a new simulation")
        self.setSubTitle(
            r'You can find more information about starting a simulation in the <a href="http://example.com/">documentation</a>.'
        )

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Initial conditions
        init_cond_gb = QGroupBox("Initial conditions", self)
        init_cond_layout = QVBoxLayout()
        water_levels_rb = QRadioButton("Initial water levels", self)
        saved_state_rb = QRadioButton("Used save state", self)
        init_cond_layout.addWidget(water_levels_rb)
        init_cond_layout.addWidget(saved_state_rb)
        init_cond_gb.setLayout(init_cond_layout)

        # Forcings
        forcings_gb = QGroupBox("Forcings", self)
        forcings_layout = QGridLayout()
        forcings_gb.setLayout(forcings_layout)

        boundary_cond_cb = QCheckBox("Include boundary conditions", self)
        laterals_cb = QCheckBox("Include laterals", self)
        dwf_cb = QCheckBox("Include dry weather flow", self)
        rain_cb = QCheckBox("Include rain", self)
        wind_cb = QCheckBox("Include wind", self)
        raster_edits_cb = QCheckBox("Raster edits", self)
        leakage_cb = QCheckBox("Leakage", self)
        sources_sinks_cb = QCheckBox("Sources and sinks", self)
        local_time_rain_cb = QCheckBox("Local or time series rain", self)
        obstacle_edits_cb = QCheckBox("Obstace edits", self)

        forcings_layout.addWidget(boundary_cond_cb, 0, 0)
        forcings_layout.addWidget(laterals_cb, 1, 0)
        forcings_layout.addWidget(dwf_cb, 2, 0)

        forcings_layout.addWidget(rain_cb, 0, 1)
        forcings_layout.addWidget(wind_cb, 1, 1)
        forcings_layout.addWidget(raster_edits_cb, 2, 1)

        forcings_layout.addWidget(leakage_cb, 0, 2)
        forcings_layout.addWidget(sources_sinks_cb, 1, 2)
        forcings_layout.addWidget(local_time_rain_cb, 2, 2)

        forcings_layout.addWidget(obstacle_edits_cb, 0, 3)

        # Events
        events_gb = QGroupBox("Events", self)
        events_layout = QGridLayout()
        events_gb.setLayout(events_layout)

        structure_controls_cb = QCheckBox("Include structure controls", self)
        breaches_cb = QCheckBox("Include breaches", self)
        events_layout.addWidget(structure_controls_cb, 0, 0)
        events_layout.addWidget(breaches_cb, 1, 0)

        # Water quality
        wq_gb = QGroupBox("Water quality", self)
        wq_layout = QGridLayout()
        wq_gb.setLayout(wq_layout)

        wq_layout.addWidget(QLabel("Add substrances to:", self), 0, 0)

        initial_water_sub_cb = QCheckBox("Initial water", self)
        boundary_cond_sub_cb = QCheckBox("Boundary conditions", self)
        lateral_cond_sub_cb = QCheckBox("Laterals", self)
        dwf_sub_cb = QCheckBox("Dry weather flow", self)
        rain_sub_cb = QCheckBox("Rain", self)
        evaporation_seepage_sub_cb = QCheckBox("Evaporation and seepage", self)
        leakage_sub_cb = QCheckBox("Leakage", self)

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
        layout.addWidget(wq_gb)

from qgis.gui import QgsCollapsibleGroupBox
from qgis.PyQt.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QGridLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

from threedi_models_simulations.widgets.new_simulation_wizard_pages.wizard_page import (
    WizardPage,
)


class SettingsPage(WizardPage):
    def __init__(self, parent, new_sim):
        super().__init__(parent, show_steps=True)
        self.setTitle("Simulation settings")
        self.setSubTitle(
            r'You can find more information about setting project settings in the <a href="https://docs.3di.live/i_running_a_simulation.html#starting-a-simulation/">documentation</a>.'
        )
        self.new_sim = new_sim

        main_widget = self.get_page_widget()
        layout = QVBoxLayout()
        main_widget.setLayout(layout)

        scroll_area = QScrollArea(main_widget)
        scroll_area.setWidgetResizable(True)
        scroll_content_widget = QWidget(main_widget)
        scroll_area.setWidget(scroll_content_widget)
        content_layout = QVBoxLayout(scroll_content_widget)

        # Physical settings
        phys_settings_gb = QgsCollapsibleGroupBox("Physical", scroll_content_widget)
        phys_settings_gb.setProperty("collapsed", True)
        phys_settings_layout = QGridLayout(phys_settings_gb)

        phys_settings_layout.addWidget(
            QLabel("Use advection 1D", phys_settings_gb), 0, 0
        )
        self.advection_1d_cb = QComboBox(phys_settings_gb)
        self.advection_1d_cb.addItem("0: No 1D advection")
        self.advection_1d_cb.addItem("1: Momentum conservative scheme")
        self.advection_1d_cb.addItem("2: Energy conservative scheme")
        self.advection_1d_cb.addItem(
            "3: Combined momentum and energy conservative scheme"
        )
        self.advection_1d_cb.currentIndexChanged.connect(self.completeChanged)
        phys_settings_layout.addWidget(self.advection_1d_cb, 0, 1)

        phys_settings_layout.addWidget(
            QLabel("Use advection 2D", phys_settings_gb), 1, 0
        )
        self.advection_2d_cb = QComboBox(phys_settings_gb)
        self.advection_2d_cb.addItem("off")
        self.advection_2d_cb.addItem("standard")
        phys_settings_layout.addWidget(self.advection_2d_cb, 1, 1)

        content_layout.addWidget(phys_settings_gb)

        # Numerical
        numerical_settings_gb = QgsCollapsibleGroupBox(
            "Numerical", scroll_content_widget
        )
        numerical_settings_gb.setProperty("collapsed", True)
        numerical_settings_layout = QGridLayout(numerical_settings_gb)

        numerical_settings_layout.addWidget(
            QLabel("Pump implicit ratio:", numerical_settings_gb), 0, 0
        )
        self.pump_implicit_ratio = QDoubleSpinBox(numerical_settings_gb)
        self.pump_implicit_ratio.setButtonSymbols(QDoubleSpinBox.NoButtons)
        self.pump_implicit_ratio.setDecimals(2)
        self.pump_implicit_ratio.setMaximum(1.0)
        numerical_settings_layout.addWidget(self.pump_implicit_ratio, 0, 1)

        numerical_settings_layout.addWidget(
            QLabel("CFL strictness factor 1D:", numerical_settings_gb), 1, 0
        )
        self.cfl_strictness_factor_1d = QDoubleSpinBox(numerical_settings_gb)
        self.cfl_strictness_factor_1d.setButtonSymbols(QDoubleSpinBox.NoButtons)
        self.cfl_strictness_factor_1d.setDecimals(2)
        self.cfl_strictness_factor_1d.setMaximum(1.0)
        numerical_settings_layout.addWidget(self.cfl_strictness_factor_1d, 1, 1)

        numerical_settings_layout.addWidget(
            QLabel("CFL strictness factor 2D:", numerical_settings_gb), 2, 0
        )
        self.cfl_strictness_factor_2d = QDoubleSpinBox(numerical_settings_gb)
        self.cfl_strictness_factor_2d.setButtonSymbols(QDoubleSpinBox.NoButtons)
        self.cfl_strictness_factor_2d.setDecimals(2)
        self.cfl_strictness_factor_2d.setMaximum(1.0)
        numerical_settings_layout.addWidget(self.cfl_strictness_factor_2d, 2, 1)

        numerical_settings_layout.addWidget(
            QLabel("Convergence EPS:", numerical_settings_gb), 3, 0
        )
        self.convergence_eps = QDoubleSpinBox(numerical_settings_gb)
        self.convergence_eps.setButtonSymbols(QDoubleSpinBox.NoButtons)
        self.convergence_eps.setDecimals(7)
        self.convergence_eps.setMinimum(1e-06)
        self.convergence_eps.setMaximum(0.0001)
        self.convergence_eps.setSingleStep(1e-06)
        self.convergence_eps.setProperty("value", 1e-05)
        numerical_settings_layout.addWidget(self.convergence_eps, 3, 1)

        numerical_settings_layout.addWidget(
            QLabel("Convergence CG:", numerical_settings_gb), 4, 0
        )
        self.convergence_cg = QDoubleSpinBox(numerical_settings_gb)
        self.convergence_cg.setButtonSymbols(QDoubleSpinBox.NoButtons)
        self.convergence_cg.setDecimals(12)
        self.convergence_cg.setMinimum(0.0)
        self.convergence_cg.setMaximum(1e-06)
        self.convergence_cg.setProperty("value", 1e-06)
        self.convergence_cg.setObjectName("convergence_cg")
        numerical_settings_layout.addWidget(self.convergence_cg, 4, 1)

        numerical_settings_layout.addWidget(
            QLabel("Flow direction threshold:", numerical_settings_gb), 5, 0
        )
        self.flow_direction_threshold = QDoubleSpinBox(numerical_settings_gb)
        self.flow_direction_threshold.setButtonSymbols(QDoubleSpinBox.NoButtons)
        self.flow_direction_threshold.setDecimals(13)
        self.flow_direction_threshold.setMaximum(0.01)
        self.flow_direction_threshold.setProperty("value", 1e-06)
        numerical_settings_layout.addWidget(self.flow_direction_threshold, 5, 1)

        numerical_settings_layout.addWidget(
            QLabel("General numerical threshold:", numerical_settings_gb), 6, 0
        )
        self.general_numerical_threshold = QDoubleSpinBox(numerical_settings_gb)
        self.general_numerical_threshold.setButtonSymbols(QDoubleSpinBox.NoButtons)
        self.general_numerical_threshold.setDecimals(13)
        self.general_numerical_threshold.setMaximum(1.0)
        numerical_settings_layout.addWidget(self.general_numerical_threshold, 6, 1)

        numerical_settings_layout.addWidget(
            QLabel("Use of CG:", numerical_settings_gb), 7, 0
        )
        self.use_of_cg = QSpinBox(numerical_settings_gb)
        self.use_of_cg.setButtonSymbols(QSpinBox.NoButtons)
        self.use_of_cg.setMinimum(1)
        self.use_of_cg.setMaximum(2147483647)
        numerical_settings_layout.addWidget(self.use_of_cg, 7, 1)

        numerical_settings_layout.addWidget(
            QLabel("Limiter waterlevel gradient 1D:", numerical_settings_gb), 8, 0
        )
        self.limiter_waterlevel_gradient_1d = QSpinBox(numerical_settings_gb)
        self.limiter_waterlevel_gradient_1d.setButtonSymbols(QSpinBox.NoButtons)
        self.limiter_waterlevel_gradient_1d.setMaximum(1)
        numerical_settings_layout.addWidget(self.limiter_waterlevel_gradient_1d, 8, 1)

        numerical_settings_layout.addWidget(
            QLabel("Limiter waterlevel gradient 2D:", numerical_settings_gb), 9, 0
        )
        self.limiter_waterlevel_gradient_2d = QSpinBox(numerical_settings_gb)
        self.limiter_waterlevel_gradient_2d.setButtonSymbols(QSpinBox.NoButtons)
        self.limiter_waterlevel_gradient_2d.setMaximum(1)
        numerical_settings_layout.addWidget(self.limiter_waterlevel_gradient_2d, 9, 1)

        numerical_settings_layout.addWidget(
            QLabel("Max non linear Newton iterations:", numerical_settings_gb), 10, 0
        )
        self.max_non_linear_newton_iterations = QSpinBox(numerical_settings_gb)
        self.max_non_linear_newton_iterations.setButtonSymbols(QSpinBox.NoButtons)
        self.max_non_linear_newton_iterations.setMinimum(1)
        self.max_non_linear_newton_iterations.setMaximum(2147483647)
        numerical_settings_layout.addWidget(
            self.max_non_linear_newton_iterations, 10, 1
        )

        numerical_settings_layout.addWidget(
            QLabel("Max degree Gauss Seidel:", numerical_settings_gb), 11, 0
        )
        self.max_degree_gauss_seidel = QSpinBox(numerical_settings_gb)
        self.max_degree_gauss_seidel.setButtonSymbols(QSpinBox.NoButtons)
        self.max_degree_gauss_seidel.setMinimum(1)
        self.max_degree_gauss_seidel.setMaximum(2147483647)
        numerical_settings_layout.addWidget(self.max_degree_gauss_seidel, 11, 1)

        numerical_settings_layout.addWidget(
            QLabel("Min friction velocity:", numerical_settings_gb), 12, 0
        )
        self.min_friction_velocity = QDoubleSpinBox(numerical_settings_gb)
        self.min_friction_velocity.setButtonSymbols(QDoubleSpinBox.NoButtons)
        self.min_friction_velocity.setDecimals(3)
        self.min_friction_velocity.setMaximum(1.0)
        self.min_friction_velocity.setProperty("value", 0.005)
        numerical_settings_layout.addWidget(self.min_friction_velocity, 12, 1)

        numerical_settings_layout.addWidget(
            QLabel("Min surface area:", numerical_settings_gb), 13, 0
        )
        self.min_surface_area = QDoubleSpinBox(numerical_settings_gb)
        self.min_surface_area.setButtonSymbols(QDoubleSpinBox.NoButtons)
        self.min_surface_area.setDecimals(13)
        self.min_surface_area.setMaximum(1.0)
        numerical_settings_layout.addWidget(self.min_surface_area, 13, 1)

        numerical_settings_layout.addWidget(
            QLabel("Preissmann slot:", numerical_settings_gb), 14, 0
        )
        self.preissmann_slot = QDoubleSpinBox(numerical_settings_gb)
        self.preissmann_slot.setButtonSymbols(QDoubleSpinBox.NoButtons)
        self.preissmann_slot.setMaximum(2147483647.0)
        numerical_settings_layout.addWidget(self.preissmann_slot, 14, 1)

        numerical_settings_layout.addWidget(
            QLabel("Limiter slope thin water layer:", numerical_settings_gb), 15, 0
        )
        self.limiter_slope_thin_water_layer = QDoubleSpinBox(numerical_settings_gb)
        self.limiter_slope_thin_water_layer.setButtonSymbols(QDoubleSpinBox.NoButtons)
        self.limiter_slope_thin_water_layer.setMaximum(2147483647.0)
        numerical_settings_layout.addWidget(self.limiter_slope_thin_water_layer, 15, 1)

        numerical_settings_layout.addWidget(
            QLabel("Use nested newton:", numerical_settings_gb), 16, 0
        )
        self.use_nested_newton = QCheckBox(numerical_settings_gb)
        numerical_settings_layout.addWidget(self.use_nested_newton, 16, 1)

        numerical_settings_layout.addWidget(
            QLabel("Flooding threshold:", numerical_settings_gb), 17, 0
        )
        self.flooding_threshold = QDoubleSpinBox(numerical_settings_gb)
        self.flooding_threshold.setButtonSymbols(QDoubleSpinBox.NoButtons)
        self.flooding_threshold.setDecimals(13)
        self.flooding_threshold.setMaximum(0.05)
        self.flooding_threshold.setSingleStep(1e-06)
        self.flooding_threshold.setProperty("value", 1e-06)
        numerical_settings_layout.addWidget(self.flooding_threshold, 17, 1)

        numerical_settings_layout.addWidget(
            QLabel("Friction shallow water depth correction:", numerical_settings_gb),
            18,
            0,
        )
        self.friction_shallow_water_depth_correction = QComboBox(numerical_settings_gb)

        self.friction_shallow_water_depth_correction.addItem("off")
        self.friction_shallow_water_depth_correction.addItem(
            "max between avg and divided channel based friction"
        )
        self.friction_shallow_water_depth_correction.addItem("always linearized")
        self.friction_shallow_water_depth_correction.addItem(
            "linearizes the depth based on a weighed averaged"
        )
        numerical_settings_layout.addWidget(
            self.friction_shallow_water_depth_correction, 18, 1
        )

        numerical_settings_layout.addWidget(
            QLabel("Time integration method:", numerical_settings_gb), 19, 0
        )
        self.time_integration_method = QComboBox(numerical_settings_gb)
        self.time_integration_method.addItem("euler implicit")
        numerical_settings_layout.addWidget(self.time_integration_method, 19, 1)

        numerical_settings_layout.addWidget(
            QLabel("Limiter slope crossectional area 2D:", numerical_settings_gb), 20, 0
        )
        self.limiter_slope_crossectional_area_2d = QComboBox(numerical_settings_gb)
        self.limiter_slope_crossectional_area_2d.addItem("off")
        self.limiter_slope_crossectional_area_2d.addItem("higher order scheme")
        self.limiter_slope_crossectional_area_2d.addItem(
            "cross-sections treated as upwind method volume/surface area"
        )
        self.limiter_slope_crossectional_area_2d.addItem(
            "combination traditional method thin layer approach"
        )
        numerical_settings_layout.addWidget(
            self.limiter_slope_crossectional_area_2d, 20, 1
        )

        numerical_settings_layout.addWidget(
            QLabel("Limiter slope friction 2D:", numerical_settings_gb), 21, 0
        )
        self.limiter_slope_friction_2d = QComboBox(numerical_settings_gb)
        self.limiter_slope_friction_2d.addItem("off")
        self.limiter_slope_friction_2d.addItem("standard")
        numerical_settings_layout.addWidget(self.limiter_slope_friction_2d, 21, 1)

        numerical_settings_layout.addWidget(
            QLabel("Use preconditioner CG:", numerical_settings_gb), 22, 0
        )
        self.use_preconditioner_cg = QComboBox(numerical_settings_gb)
        self.use_preconditioner_cg.addItem("off")
        self.use_preconditioner_cg.addItem("standard")
        numerical_settings_layout.addWidget(self.use_preconditioner_cg, 22, 1)

        content_layout.addWidget(numerical_settings_gb)

        # Timestep settings
        timestep_settings_gb = QgsCollapsibleGroupBox("Timestep", scroll_content_widget)
        timestep_settings_gb.setProperty("collapsed", True)
        timestep_settings_layout = QGridLayout(timestep_settings_gb)

        timestep_settings_layout.addWidget(
            QLabel("Time step:", timestep_settings_gb), 0, 0
        )
        self.time_step = QDoubleSpinBox(timestep_settings_gb)
        self.time_step.setButtonSymbols(QDoubleSpinBox.NoButtons)
        self.time_step.setDecimals(4)
        self.time_step.setMaximum(1000000000.0)
        timestep_settings_layout.addWidget(self.time_step, 0, 1)

        timestep_settings_layout.addWidget(
            QLabel("Min time step:", timestep_settings_gb), 1, 0
        )
        self.min_time_step = QDoubleSpinBox(timestep_settings_gb)
        self.min_time_step.setButtonSymbols(QDoubleSpinBox.NoButtons)
        self.min_time_step.setDecimals(4)
        self.min_time_step.setMaximum(1000000000.0)
        timestep_settings_layout.addWidget(self.min_time_step, 1, 1)

        timestep_settings_layout.addWidget(
            QLabel("Max time step:", timestep_settings_gb), 2, 0
        )
        self.max_time_step = QDoubleSpinBox(timestep_settings_gb)
        self.max_time_step.setButtonSymbols(QDoubleSpinBox.NoButtons)
        self.max_time_step.setDecimals(4)
        self.max_time_step.setMaximum(1000000000.0)
        timestep_settings_layout.addWidget(self.max_time_step, 2, 1)

        timestep_settings_layout.addWidget(
            QLabel("Output time step:", timestep_settings_gb), 3, 0
        )
        self.output_time_step = QDoubleSpinBox(timestep_settings_gb)
        self.output_time_step.setButtonSymbols(QDoubleSpinBox.NoButtons)
        self.output_time_step.setDecimals(4)
        self.output_time_step.setMaximum(1000000000.0)
        timestep_settings_layout.addWidget(self.output_time_step, 3, 1)

        timestep_settings_layout.addWidget(
            QLabel("Use time step stretch:", timestep_settings_gb), 4, 0
        )
        self.use_time_step_stretch = QCheckBox(timestep_settings_gb)
        timestep_settings_layout.addWidget(self.use_time_step_stretch, 4, 1)

        content_layout.addWidget(timestep_settings_gb)

        # Aggregation settings
        agg_settings_gb = QgsCollapsibleGroupBox("Aggregation", scroll_content_widget)
        agg_settings_gb.setProperty("collapsed", True)
        agg_settings_layout = QGridLayout(agg_settings_gb)

        self.aggregation_tv = QTreeView(agg_settings_gb)
        agg_settings_layout.addWidget(self.aggregation_tv, 0, 0, 2, 4)
        self.add_aggregation_entry = QPushButton("Add", agg_settings_gb)
        agg_settings_layout.addWidget(self.add_aggregation_entry, 2, 2)
        self.remove_aggregation_entry = QPushButton("Remove", agg_settings_gb)
        agg_settings_layout.addWidget(self.remove_aggregation_entry, 2, 3)

        content_layout.addWidget(agg_settings_gb)

        # Water quality settings
        water_quality_gb = QgsCollapsibleGroupBox(
            "Water quality", scroll_content_widget
        )
        water_quality_gb.setProperty("collapsed", True)
        water_quality_layout = QGridLayout(water_quality_gb)

        water_quality_layout.addWidget(QLabel("Time step:", water_quality_gb), 0, 0)
        self.time_step_2 = QDoubleSpinBox(water_quality_gb)
        self.time_step_2.setButtonSymbols(QDoubleSpinBox.NoButtons)
        self.time_step_2.setDecimals(4)
        water_quality_layout.addWidget(self.time_step_2, 0, 1)

        water_quality_layout.addWidget(QLabel("Min time step:", water_quality_gb), 1, 0)
        self.min_time_step_2 = QDoubleSpinBox(water_quality_gb)
        self.min_time_step_2.setButtonSymbols(QDoubleSpinBox.NoButtons)
        self.min_time_step_2.setDecimals(4)
        water_quality_layout.addWidget(self.min_time_step_2, 1, 1)

        water_quality_layout.addWidget(QLabel("Max time step:", water_quality_gb), 2, 0)
        self.max_time_step_2 = QDoubleSpinBox(water_quality_gb)
        self.max_time_step_2.setButtonSymbols(QDoubleSpinBox.NoButtons)
        self.max_time_step_2.setDecimals(4)
        water_quality_layout.addWidget(self.max_time_step_2, 2, 1)

        water_quality_layout.addWidget(
            QLabel("General numerical threshold:", water_quality_gb), 3, 0
        )
        self.general_numerical_threshold_2 = QDoubleSpinBox(water_quality_gb)
        self.general_numerical_threshold_2.setButtonSymbols(QDoubleSpinBox.NoButtons)
        self.general_numerical_threshold_2.setDecimals(13)
        self.general_numerical_threshold_2.setMaximum(1.0)
        water_quality_layout.addWidget(self.general_numerical_threshold_2, 3, 1)

        water_quality_layout.addWidget(
            QLabel("Max number of multi step:", water_quality_gb), 4, 0
        )
        self.max_number_of_multi_step = QSpinBox(water_quality_gb)
        self.max_number_of_multi_step.setButtonSymbols(QSpinBox.NoButtons)
        self.max_number_of_multi_step.setMaximum(2147483647)
        self.max_number_of_multi_step.setProperty("value", 0)
        water_quality_layout.addWidget(self.max_number_of_multi_step, 4, 1)

        water_quality_layout.addWidget(
            QLabel("Max gs sweep iterations:", water_quality_gb), 5, 0
        )
        self.max_gs_sweep_iterations = QSpinBox(water_quality_gb)
        self.max_gs_sweep_iterations.setButtonSymbols(QSpinBox.NoButtons)
        self.max_gs_sweep_iterations.setMaximum(2147483647)
        self.max_gs_sweep_iterations.setProperty("value", 0)
        water_quality_layout.addWidget(self.max_gs_sweep_iterations, 5, 1)

        water_quality_layout.addWidget(
            QLabel("Convergence eps:", water_quality_gb), 6, 0
        )
        self.convergence_eps_2 = QDoubleSpinBox(water_quality_gb)
        self.convergence_eps_2.setButtonSymbols(QDoubleSpinBox.NoButtons)
        self.convergence_eps_2.setDecimals(7)
        self.convergence_eps_2.setMinimum(1e-06)
        self.convergence_eps_2.setMaximum(0.0001)
        self.convergence_eps_2.setSingleStep(1e-06)
        water_quality_layout.addWidget(self.convergence_eps_2, 6, 1)

        content_layout.addWidget(water_quality_gb)

        content_layout.addStretch()
        layout.addWidget(scroll_area)

    def initializePage(self):
        # Fill the page with the current model
        return

    def validatePage(self):
        # when the user clicks Next or Finish to perform some last-minute validation. If it returns true, the next page is shown (or the wizard finishes); otherwise, the current page stays up.
        # Update the model
        return True

    def isComplete(self):
        # We also need to emit the QWizardPage::completeChanged() signal every time isComplete() may potentially return a different value,
        # so that the wizard knows that it must refresh the Next button.
        return True

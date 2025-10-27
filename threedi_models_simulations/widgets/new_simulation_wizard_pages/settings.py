from qgis.core import Qgis, QgsMessageLog
from qgis.gui import QgsCollapsibleGroupBox
from qgis.PyQt.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QGridLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QRadioButton,
    QScrollArea,
    QSpinBox,
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

        content_layout.addWidget(numerical_settings_gb)

        # self.label_9 = QtWidgets.QLabel(self.group_numerical)
        # font = QtGui.QFont()
        # font.setFamily("Segoe UI")
        # font.setPointSize(10)
        # self.label_9.setFont(font)
        # self.label_9.setObjectName("label_9")
        # self.gridLayout_9.addWidget(self.label_9, 8, 3, 1, 1)
        # self.flooding_threshold = QtWidgets.QDoubleSpinBox(self.group_numerical)
        # self.flooding_threshold.setMinimumSize(QtCore.QSize(0, 25))
        # font = QtGui.QFont()
        # font.setFamily("Segoe UI")
        # font.setPointSize(10)
        # self.flooding_threshold.setFont(font)
        # self.flooding_threshold.setStyleSheet("QDoubleSpinBox {background-color: white;}")
        # self.flooding_threshold.setFrame(False)
        # self.flooding_threshold.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        # self.flooding_threshold.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        # self.flooding_threshold.setDecimals(13)
        # self.flooding_threshold.setMaximum(0.05)
        # self.flooding_threshold.setSingleStep(1e-06)
        # self.flooding_threshold.setProperty("value", 1e-06)
        # self.flooding_threshold.setObjectName("flooding_threshold")
        # self.gridLayout_9.addWidget(self.flooding_threshold, 8, 4, 1, 1)
        # self.label_16 = QtWidgets.QLabel(self.group_numerical)
        # font = QtGui.QFont()
        # font.setFamily("Segoe UI")
        # font.setPointSize(10)
        # self.label_16.setFont(font)
        # self.label_16.setObjectName("label_16")
        # self.gridLayout_9.addWidget(self.label_16, 9, 0, 1, 1)
        # self.friction_shallow_water_depth_correction = QtWidgets.QComboBox(self.group_numerical)
        # self.friction_shallow_water_depth_correction.setMinimumSize(QtCore.QSize(150, 25))
        # font = QtGui.QFont()
        # font.setFamily("Segoe UI")
        # font.setPointSize(10)
        # self.friction_shallow_water_depth_correction.setFont(font)
        # self.friction_shallow_water_depth_correction.setStyleSheet("QComboBox {background-color:white; selection-background-color: lightgray;}")
        # self.friction_shallow_water_depth_correction.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToContentsOnFirstShow)
        # self.friction_shallow_water_depth_correction.setFrame(False)
        # self.friction_shallow_water_depth_correction.setObjectName("friction_shallow_water_depth_correction")
        # self.friction_shallow_water_depth_correction.addItem("")
        # self.friction_shallow_water_depth_correction.addItem("")
        # self.friction_shallow_water_depth_correction.addItem("")
        # self.friction_shallow_water_depth_correction.addItem("")
        # self.gridLayout_9.addWidget(self.friction_shallow_water_depth_correction, 9, 1, 1, 4)
        # self.label_18 = QtWidgets.QLabel(self.group_numerical)
        # font = QtGui.QFont()
        # font.setFamily("Segoe UI")
        # font.setPointSize(10)
        # self.label_18.setFont(font)
        # self.label_18.setObjectName("label_18")
        # self.gridLayout_9.addWidget(self.label_18, 10, 0, 1, 1)
        # self.time_integration_method = QtWidgets.QComboBox(self.group_numerical)
        # self.time_integration_method.setMinimumSize(QtCore.QSize(0, 25))
        # font = QtGui.QFont()
        # font.setFamily("Segoe UI")
        # font.setPointSize(10)
        # self.time_integration_method.setFont(font)
        # self.time_integration_method.setStyleSheet("QComboBox {background-color:white; selection-background-color: lightgray;}")
        # self.time_integration_method.setFrame(False)
        # self.time_integration_method.setObjectName("time_integration_method")
        # self.time_integration_method.addItem("")
        # self.gridLayout_9.addWidget(self.time_integration_method, 10, 1, 1, 4)
        # self.label_3 = QtWidgets.QLabel(self.group_numerical)
        # self.label_3.setMinimumSize(QtCore.QSize(350, 0))
        # font = QtGui.QFont()
        # font.setFamily("Segoe UI")
        # font.setPointSize(10)
        # self.label_3.setFont(font)
        # self.label_3.setObjectName("label_3")
        # self.gridLayout_9.addWidget(self.label_3, 11, 0, 1, 1)
        # self.limiter_slope_crossectional_area_2d = QtWidgets.QComboBox(self.group_numerical)
        # self.limiter_slope_crossectional_area_2d.setMinimumSize(QtCore.QSize(150, 25))
        # font = QtGui.QFont()
        # font.setFamily("Segoe UI")
        # font.setPointSize(10)
        # self.limiter_slope_crossectional_area_2d.setFont(font)
        # self.limiter_slope_crossectional_area_2d.setStyleSheet("QComboBox {background-color:white; selection-background-color: lightgray;}")
        # self.limiter_slope_crossectional_area_2d.setFrame(False)
        # self.limiter_slope_crossectional_area_2d.setObjectName("limiter_slope_crossectional_area_2d")
        # self.limiter_slope_crossectional_area_2d.addItem("")
        # self.limiter_slope_crossectional_area_2d.addItem("")
        # self.limiter_slope_crossectional_area_2d.addItem("")
        # self.limiter_slope_crossectional_area_2d.addItem("")
        # self.gridLayout_9.addWidget(self.limiter_slope_crossectional_area_2d, 11, 1, 1, 4)
        # self.label_21 = QtWidgets.QLabel(self.group_numerical)
        # font = QtGui.QFont()
        # font.setFamily("Segoe UI")
        # font.setPointSize(10)
        # self.label_21.setFont(font)
        # self.label_21.setObjectName("label_21")
        # self.gridLayout_9.addWidget(self.label_21, 12, 0, 1, 1)
        # self.limiter_slope_friction_2d = QtWidgets.QComboBox(self.group_numerical)
        # self.limiter_slope_friction_2d.setMinimumSize(QtCore.QSize(0, 25))
        # font = QtGui.QFont()
        # font.setFamily("Segoe UI")
        # font.setPointSize(10)
        # self.limiter_slope_friction_2d.setFont(font)
        # self.limiter_slope_friction_2d.setStyleSheet("QComboBox {background-color:white; selection-background-color: lightgray;}")
        # self.limiter_slope_friction_2d.setFrame(False)
        # self.limiter_slope_friction_2d.setObjectName("limiter_slope_friction_2d")
        # self.limiter_slope_friction_2d.addItem("")
        # self.limiter_slope_friction_2d.addItem("")
        # self.gridLayout_9.addWidget(self.limiter_slope_friction_2d, 12, 1, 1, 4)
        # self.label_26 = QtWidgets.QLabel(self.group_numerical)
        # font = QtGui.QFont()
        # font.setFamily("Segoe UI")
        # font.setPointSize(10)
        # self.label_26.setFont(font)
        # self.label_26.setObjectName("label_26")
        # self.gridLayout_9.addWidget(self.label_26, 13, 0, 1, 1)
        # self.use_preconditioner_cg = QtWidgets.QComboBox(self.group_numerical)
        # self.use_preconditioner_cg.setMinimumSize(QtCore.QSize(0, 25))
        # font = QtGui.QFont()
        # font.setFamily("Segoe UI")
        # font.setPointSize(10)
        # self.use_preconditioner_cg.setFont(font)
        # self.use_preconditioner_cg.setStyleSheet("QComboBox {background-color:white; selection-background-color: lightgray;}")
        # self.use_preconditioner_cg.setFrame(False)
        # self.use_preconditioner_cg.setObjectName("use_preconditioner_cg")
        # self.use_preconditioner_cg.addItem("")
        # self.use_preconditioner_cg.addItem("")
        # self.gridLayout_9.addWidget(self.use_preconditioner_cg, 13, 1, 1, 4)
        # self.gridLayout_5.addWidget(self.group_numerical, 1, 0, 1, 1)
        # spacerItem1 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        # self.gridLayout_5.addItem(spacerItem1, 5, 0, 1, 1)

        content_layout.addStretch()

        layout.addWidget(scroll_area)

    def initializePage(self):
        # Fill the page with the current model
        return

    def validatePage(self):
        # when the user clicks Next or Finish to perform some last-minute validation. If it returns true, the next page is shown (or the wizard finishes); otherwise, the current page stays up.
        return True

    def isComplete(self):
        # We also need to emit the QWizardPage::completeChanged() signal every time isComplete() may potentially return a different value,
        # so that the wizard knows that it must refresh the Next button. This requires us to add the following connect()
        # call to the SailingPage constructor:  connect(sailing, SIGNAL(selectionChanged()), this, SIGNAL(completeChanged()));
        return True

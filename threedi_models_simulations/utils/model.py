from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List

from qgis.core import Qgis, QgsMessageLog
from threedi_api_client.openapi import (
    AggregationSettings,
    CurrentStatus,
    NumericalSettings,
    PhysicalSettings,
    Simulation,
    TimeStepSettings,
    WaterQualitySettings,
)


@dataclass
class NewSimulation:
    """A container for all simulation objects"""

    simulation_template_id: str

    # init_options: InitOptions = None
    # fileboundaryconditions: FileBoundaryCondition = None
    # boundary_conditions_data: list = None

    # structure_controls: StructureControls = None
    # initial_conditions: InitialConditions = None
    # laterals: Laterals = None
    # substances: Substances = None
    # dwf: DWF = None
    # breaches: Breaches = None
    # precipitation: Precipitation = None
    # wind: Wind = None
    numerical_settings: NumericalSettings = None
    water_quality_settings: WaterQualitySettings = None
    physical_settings: PhysicalSettings = None
    aggregation_settings: List[AggregationSettings] = None
    time_step_settings: TimeStepSettings = None
    # lizard_post_processing: LizardPostProcessing = None
    # new_saved_state: SavedState = None
    template_name: str = None
    start_simulation: bool = True
    # Last two attributes will be added after new simulation initialization
    simulation: Simulation = None
    initial_status: CurrentStatus = None


def load_template_in_model(
    simulation,
    settings_overview,
    events,
    lizard_post_processing_overview,
    simulation_template,
    organisation,
) -> NewSimulation:
    new_sim = NewSimulation(simulation_template_id=simulation_template.id)
    new_sim.simulation = Simulation(
        threedimodel=str(simulation.threedimodel_id),
        name=simulation.name,
        organisation=organisation.unique_id,
        start_datetime=datetime.now(timezone.utc),  # temp: will be filled later
        end_datetime=datetime.now(timezone.utc),  # temp: will be filled later
        duration=600,  # temp
        started_from="3Di Modeller Interface",
    )

    # events
    QgsMessageLog.logMessage(str(events), level=Qgis.Critical)

    # postprocessing
    QgsMessageLog.logMessage(str(lizard_post_processing_overview), level=Qgis.Critical)

    # template
    QgsMessageLog.logMessage(str(simulation_template), level=Qgis.Critical)

    # settings
    new_sim.aggregation_settings = settings_overview.aggregation_settings
    new_sim.physical_settings = settings_overview.physical_settings
    new_sim.numerical_settings = settings_overview.numerical_settings
    new_sim.water_quality_settings = settings_overview.water_quality_settings
    new_sim.time_step_settings = settings_overview.time_step_settings

    return new_sim

from dataclasses import dataclass
from datetime import datetime, timezone

from qgis.core import Qgis, QgsMessageLog

from threedi_models_simulations.models.file_boundary_condition import (
    FileBoundaryCondition,
)
from threedi_models_simulations.models.simulation import Simulation


@dataclass
class NewSimulation:
    """A container for all simulation objects"""

    simulation_template_id: str

    # init_options: InitOptions = None
    boundary_conditions: FileBoundaryCondition = None
    boundary_conditions_data: list = None

    # structure_controls: StructureControls = None
    # initial_conditions: InitialConditions = None
    # laterals: Laterals = None
    # substances: Substances = None
    # dwf: DWF = None
    # breaches: Breaches = None
    # precipitation: Precipitation = None
    # wind: Wind = None
    # settings: Settings = None
    # lizard_post_processing: LizardPostProcessing = None
    # new_saved_state: SavedState = None
    template_name: str = None
    start_simulation: bool = True
    # Last two attributes will be added after new simulation initialization
    simulation: Simulation = None
    # initial_status: CurrentStatus = None


def load_template_in_model(
    simulation,
    settings_overview,
    events,
    lizard_post_processing_overview,
    simulation_template,
    organisation,
) -> Simulation:
    QgsMessageLog.logMessage("simulation", level=Qgis.Critical)
    QgsMessageLog.logMessage(str(simulation), level=Qgis.Critical)
    QgsMessageLog.logMessage("settings_overview", level=Qgis.Critical)
    QgsMessageLog.logMessage(str(settings_overview), level=Qgis.Critical)
    QgsMessageLog.logMessage("events", level=Qgis.Critical)
    QgsMessageLog.logMessage(str(events), level=Qgis.Critical)
    QgsMessageLog.logMessage("postprocessing", level=Qgis.Critical)
    QgsMessageLog.logMessage(str(lizard_post_processing_overview), level=Qgis.Critical)
    QgsMessageLog.logMessage("template", level=Qgis.Critical)
    QgsMessageLog.logMessage(str(simulation_template), level=Qgis.Critical)
    QgsMessageLog.logMessage("organisation", level=Qgis.Critical)
    QgsMessageLog.logMessage(str(organisation), level=Qgis.Critical)

    new_sim = NewSimulation(simulation_template_id=simulation_template.id)
    new_sim.simulation = Simulation(
        threedimodel=str(simulation.threedimodel_id),
        name=simulation.name,
        organisation=organisation.unique_id,
        start_datetime=datetime.now(timezone.utc),  # temp: will be filled later
        end_datetime=datetime.now(timezone.utc),  # temp: will be filled later
        started_from="3Di Modeller Interface",
    )

    # events

    # postprocessing

    # template

    # settings

    return new_sim

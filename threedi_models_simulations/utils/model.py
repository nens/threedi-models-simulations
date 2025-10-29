from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List

from qgis.core import Qgis, QgsMessageLog
from threedi_api_client.openapi import (
    AggregationSettings,
    Breach,
    CurrentStatus,
    DamageEstimation,
    FileBoundaryCondition,
    FileRasterLeakage,
    FileRasterSourcesSinks,
    FileStructureControl,
    FileTimeseriesLeakage,
    FileTimeseriesRain,
    FileTimeseriesSourcesSinks,
    InitialWaterlevel,
    LizardRasterSourcesSinks,
    LizardTimeseriesRain,
    LizardTimeseriesSourcesSinks,
    LocalRain,
    MemoryStructureControl,
    NumericalSettings,
    ObstacleEdit,
    PhysicalSettings,
    RasterEdit,
    Simulation,
    TableStructureControl,
    TimedStructureControl,
    TimeseriesLeakageOverview,
    TimeseriesSourcesSinks,
    TimeStepSettings,
    WaterQualitySettings,
)


# TODO: These classes should be build using the generated API
@dataclass
class Precipitation:
    precipitation_type: str = None
    offset: float = None
    duration: int = None
    units: str = None
    values: list = None
    start: datetime = None
    interpolate: bool = None
    csv_filepath: str = None
    netcdf_filepath: str = None
    netcdf_global: bool = None
    netcdf_raster: bool = None
    substances: list = None


@dataclass
class Wind:
    wind_type: str = None
    offset: float = None
    duration: int = None
    speed: int = None
    direction: int = None
    units: str = None
    drag_coefficient: float = None
    interpolate_speed: bool = None
    interpolate_direction: bool = None
    values: list = None


@dataclass
class SavedState:
    name: str = None
    tags: str = None
    time: int = None
    thresholds: list = None


@dataclass
class NewSimulation:
    """A container for all simulation objects"""

    simulation_template_id: str

    # Init options
    raster_edits: RasterEdit = None

    # Leakage
    timeseries_leakage_overview: TimeseriesLeakageOverview = None
    file_timeseries_leakage: FileTimeseriesLeakage = None
    file_raster_leakage: FileRasterLeakage = None

    # Sources Sinks
    lizard_raster_sources_sinks: LizardRasterSourcesSinks = None
    lizard_timeseries_sources_sinks: LizardTimeseriesSourcesSinks = None
    timeseries_sources_sinks: TimeseriesSourcesSinks = None
    file_raster_sources_sinks: FileRasterSourcesSinks = None
    file_timeseries_sources_sinks: FileTimeseriesSourcesSinks = None

    lizard_timeseries_rain: LizardTimeseriesRain = None
    local_rain: LocalRain = None
    file_timeseries_rain: FileTimeseriesRain = None

    obstacle_edits: ObstacleEdit = None

    # Structure controls
    file_structure_controls: FileStructureControl = None
    memory_structure_controls: MemoryStructureControl = None
    table_structure_controls: TableStructureControl = None
    timed_structure_controls: TimedStructureControl = None
    local_file_structure_controls: str = None

    # Boundary Conditions
    file_boundary_conditions: FileBoundaryCondition = None
    boundary_conditions_data: list = None

    # Initial conditions
    global_value_1d: float = None
    from_geopackage_1d: bool = None
    initial_waterlevels_1d: dict = None
    online_waterlevels_1d: InitialWaterlevel = None
    global_value_2d: float = None
    online_raster_2d: InitialWaterlevel = None
    local_raster_2d: str = None
    aggregation_method_2d: str = None
    global_value_groundwater: str = None
    online_raster_groundwater: InitialWaterlevel = None
    local_raster_groundwater: str = None
    aggregation_method_groundwater: str = None
    saved_state: str = None
    initial_concentrations_2d: dict = None
    initial_concentrations_1d: dict = None

    # Laterals # TODO
    laterals: list = None
    file_laterals_1d: dict = None
    file_laterals_2d: dict = None

    # Substances  # TODO
    substances_data: list = None

    # DWF  # TODO
    dwf_data: dict = None

    breaches: List[Breach] = None

    # TODO
    precipitation: Precipitation = None
    wind: Wind = None

    numerical_settings: NumericalSettings = None
    water_quality_settings: WaterQualitySettings = None
    physical_settings: PhysicalSettings = None
    aggregation_settings: List[AggregationSettings] = None
    time_step_settings: TimeStepSettings = None

    # LizardPostProcessing
    basic_post_processing: bool = None
    arrival_time_map: bool = None
    damage_estimation: DamageEstimation = None

    new_saved_state: SavedState = None

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

    # Load events
    QgsMessageLog.logMessage(str(events), level=Qgis.Critical)
    if events:
        pass

    # Load postprocessing
    # QgsMessageLog.logMessage(str(lizard_post_processing_overview), level=Qgis.Critical)
    if lizard_post_processing_overview:
        pass

    # template
    QgsMessageLog.logMessage(str(simulation_template), level=Qgis.Critical)

    # settings
    new_sim.aggregation_settings = settings_overview.aggregation_settings
    new_sim.physical_settings = settings_overview.physical_settings
    new_sim.numerical_settings = settings_overview.numerical_settings
    new_sim.water_quality_settings = settings_overview.water_quality_settings
    new_sim.time_step_settings = settings_overview.time_step_settings

    return new_sim

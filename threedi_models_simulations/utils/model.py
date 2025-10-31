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


# TODO: These classes should be build using the generated API (probably using multiple kinds of precipitation/wind)
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

    # LocalTimeseriesRain
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
    # TODO: do we need these constant attributes?
    initial_1d_water_level_constant: float = None  # was global_value_1d
    initial_1d_water_level_predefined: bool = None  # was from_geopackage_1d
    initial_1d_water_level: dict = None  # was initial_waterlevels_1d
    initial_1d_water_level_file: InitialWaterlevel = None

    initial_2d_water_level_constant: float = None  # was global_value_2d
    initial_2d_water_level_raster: InitialWaterlevel = None
    initial_2d_water_level_raster_local: str = None
    initial_2d_water_level_aggregation_method: str = None

    initial_groundwater_constant: str = None
    initial_groundwater_level: InitialWaterlevel = None
    initial_groundwater_raster: str = None
    initial_groundwater_raster_local: str = None
    initial_groundwater_aggregation_method: str = None

    saved_state: str = None

    initial_concentrations_2d: dict = None
    initial_concentrations_1d: dict = None
    initial_concentrations_groundwater: dict = None

    # Laterals
    laterals: list = None
    file_laterals: list = None
    file_laterals_1d: dict = None
    file_laterals_2d: dict = None

    # Substances  # TODO
    substances: list = None

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
    """Load all information that is required for the Wizard"""

    QgsMessageLog.logMessage(str(simulation), level=Qgis.Critical)
    QgsMessageLog.logMessage(str("------------"), level=Qgis.Critical)
    QgsMessageLog.logMessage(str(simulation_template), level=Qgis.Critical)
    QgsMessageLog.logMessage(str("---ssss---------"), level=Qgis.Critical)
    new_sim = NewSimulation(simulation_template_id=simulation_template.id)
    new_sim.simulation = Simulation(
        threedimodel=str(simulation.threedimodel_id),
        name=simulation.name,
        organisation=organisation.unique_id,
        start_datetime=simulation.start_datetime,
        end_datetime=simulation.end_datetime,
        duration=600,  # temp
        started_from="3Di Modeller Interface",
        tags=simulation.tags,
    )

    # Load events
    QgsMessageLog.logMessage(str(events), level=Qgis.Critical)
    if events:
        new_sim.raster_edits = events.rasteredits

        new_sim.timeseries_leakage_overview = (
            events.leakage
        )  # [0]  # TODO: this is how its done in old plugin
        new_sim.file_timeseries_leakage = events.filetimeseriesleakage
        new_sim.file_raster_leakage = events.filerasterleakage

        # TODO: old plugin takes first element from event attribute
        new_sim.lizard_raster_sources_sinks = events.lizardrastersourcessinks
        new_sim.lizard_timeseries_sources_sinks = events.lizardtimeseriessourcessinks
        new_sim.timeseries_sources_sinks = events.timeseriessourcessinks
        new_sim.file_raster_sources_sinks = events.filerastersourcessinks
        new_sim.file_timeseries_sources_sinks = events.filetimeseriessourcessinks

        new_sim.lizard_timeseries_rain = events.lizardtimeseriesrain
        new_sim.local_rain = events.localrain
        new_sim.file_timeseries_rain = events.filetimeseriesrain

        new_sim.obstacle_edits = events.obstacleedits

        new_sim.file_structure_controls = events.filestructurecontrols
        new_sim.memory_structure_controls = events.memorystructurecontrols
        new_sim.table_structure_controls = events.tablestructurecontrols
        new_sim.timed_structure_controls = events.timedstructurecontrols
        # TODO: used for upload
        # new_sim.local_file_structure_controls

        new_sim.file_boundary_conditions = events.fileboundaryconditions
        # TODO: used for upload?
        # boundary_conditions_data

        # Initial conditions
        # TODO: derive the following value
        # new_sim.initial_1d_water_level_constant # was global_value_1d
        new_sim.initial_1d_water_level_predefined = (
            events.initial_onedwaterlevelpredefined
        )  # was from_geopackage_1d
        new_sim.initial_1d_water_level = events.initial_onedwaterlevel
        new_sim.initial_1d_water_level_file = events.initial_onedwaterlevelfile

        new_sim.initial_2d_water_level_raster = events.initial_twodwaterraster
        if events.initial_twodwaterraster:
            new_sim.initial_2d_water_level_aggregation_method = (
                events.initial_twodwaterraster["aggregation_method"]
            )

        # TODO: derive the following value
        # initial_groundwater_constant: str = None
        new_sim.initial_groundwater_level = events.initial_groundwaterlevel
        new_sim.initial_groundwater_raster = events.initial_groundwaterraster
        # local_raster_groundwater: str = None
        if events.initial_groundwaterraster:
            new_sim.initial_groundwater_aggregation_method = (
                events.initial_groundwaterraster["aggregation_method"]
            )

        new_sim.saved_state = events.initial_savedstate

        new_sim.initial_concentrations_2d = events.initial_twod_substance_concentrations
        new_sim.initial_concentrations_1d = events.initial_oned_substance_concentrations
        new_sim.initial_concentrations_groundwater = (
            events.initial_groundwater_substance_concentrations
        )

        # Laterals
        new_sim.laterals = events.laterals
        new_sim.file_laterals = events.filelaterals
        # file_laterals_1d: dict = None
        # file_laterals_2d: dict = None

        # # Substances
        new_sim.substances = events.substances

        # # DWF  # are stored as lateral
        # dwf_data: dict = None

        # breaches: List[Breach] = None

        # # TODO
        # precipitation: Precipitation = None
        # wind: Wind = None

    # Load postprocessing
    QgsMessageLog.logMessage(str(lizard_post_processing_overview), level=Qgis.Critical)
    # if lizard_post_processing_overview:
    #     basic_post_processing: bool = None
    #     arrival_time_map: bool = None
    #     damage_estimation: DamageEstimation = None

    # new_saved_state: SavedState = None

    # template
    QgsMessageLog.logMessage(str(simulation_template), level=Qgis.Critical)

    # settings
    new_sim.aggregation_settings = settings_overview.aggregation_settings
    new_sim.physical_settings = settings_overview.physical_settings
    new_sim.numerical_settings = settings_overview.numerical_settings
    new_sim.water_quality_settings = settings_overview.water_quality_settings
    new_sim.time_step_settings = settings_overview.time_step_settings

    return new_sim

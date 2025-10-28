import json
from collections import OrderedDict
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Callable, List, Tuple

import requests
from qgis.core import Qgis, QgsMessageLog
from threedi_api_client import ThreediApi
from threedi_api_client.openapi import (
    Action,
    AggregationSettings,
    ArrivalTimePostProcessing,
    BasicPostProcessing,
    Breach,
    Commit,
    ConstantLateral,
    ConstantLocalRain,
    ConstantRain,
    ConstantWind,
    Contract,
    CurrentStatus,
    DamagePostProcessing,
    Download,
    Event,
    FileBoundaryCondition,
    FileLateral,
    FileRasterSourcesSinks,
    FileStructureControl,
    FileTimeseriesSourcesSinks,
    ForcingSubstance,
    GroundWaterLevel,
    GroundWaterRaster,
    InitialConcentration,
    InitialSavedState,
    InitialWaterlevel,
    LizardRasterRain,
    LizardRasterSourcesSinks,
    LizardTimeseriesRain,
    LizardTimeseriesSourcesSinks,
    MemoryStructureControl,
    NumericalSettings,
    ObstacleEdit,
    OneDSubstanceConcentration,
    OneDWaterLevel,
    OneDWaterLevelFile,
    OneDWaterLevelPredefined,
    Organisation,
    PhysicalSettings,
    PostProcessingOverview,
    PotentialBreach,
    Progress,
    Raster,
    RasterCreate,
    RasterEdit,
    Repository,
    ResultFile,
    Revision,
    RevisionRaster,
    RevisionTask,
    Schematisation,
    SchematisationRevision,
    Simulation,
    SimulationSettingsOverview,
    SimulationStatus,
    SqliteFileUpload,
    StableThresholdSavedState,
    Substance,
    TableStructureControl,
    Template,
    ThreediModel,
    ThreediModelSavedState,
    ThreediModelTask,
    TimedSavedStateUpdate,
    TimedStructureControl,
    TimeseriesLateral,
    TimeseriesLocalRain,
    TimeseriesRain,
    TimeseriesSourcesSinks,
    TimeseriesWind,
    TimeStepSettings,
    TwoDSubstanceConcentration,
    TwoDWaterLevel,
    TwoDWaterRaster,
    Upload,
    UploadEventFile,
    User,
    WaterQualitySettings,
    WindDragCoefficient,
)

from threedi_models_simulations.constants import DOWNLOAD_CHUNK_SIZE


class SimulationStatusName(Enum):
    CRASHED = "crashed"
    CREATED = "created"
    ENDED = "ended"
    FINISHED = "finished"
    INITIALIZED = "initialized"
    POSTPROCESSING = "postprocessing"
    QUEUED = "queued"
    STARTING = "starting"
    STOPPED = "stopped"


class RainEventTypes(Enum):
    CONSTANT = "Constant"
    FROM_CSV = "From CSV"
    FROM_NETCDF = "From NetCDF"
    DESIGN = "Design"
    RADAR = "Radar - NL Only"


class WindEventTypes(Enum):
    CONSTANT = "Constant"
    CUSTOM = "Custom"


class FileState(Enum):
    """Possible uploaded file states."""

    CREATED = "created"
    UPLOADED = "uploaded"
    PROCESSED = "processed"
    ERROR = "error"
    REMOVED = "removed"


class ThreediFileState(Enum):
    """Possible 3Di file states."""

    PROCESSING = "processing"
    VALID = "valid"
    INVALID = "invalid"


class ThreediModelTaskStatus(Enum):
    """Possible 3Di Model Task statuses."""

    PENDING = "pending"
    SENT = "sent"
    RECEIVED = "received"
    STARTED = "started"
    SUCCESS = "success"
    FAILURE = "failure"
    REVOKED = "revoked"


class UploadFileType(Enum):
    """File types of the uploaded files."""

    DB = "DB"
    RASTER = "RASTER"


class UploadFileStatus(Enum):
    """Possible actions on files upload."""

    NO_CHANGES_DETECTED = "NO CHANGES DETECTED"
    CHANGES_DETECTED = "CHANGES DETECTED"
    NEW = "NEW"
    DELETED_LOCALLY = "DELETED LOCALLY"
    INVALID_REFERENCE = "INVALID REFERENCE!"


class ThreediModelTaskStatus(Enum):
    """Possible 3Di Model Task statuses."""

    PENDING = "pending"
    SENT = "sent"
    RECEIVED = "received"
    STARTED = "started"
    SUCCESS = "success"
    FAILURE = "failure"
    REVOKED = "revoked"


FETCH_LIMIT = 250


def get_api_client_with_personal_api_token(
    personal_api_token: str, api_host: str, version: str = "v3-beta"
) -> ThreediApi:
    """Setup 3Di API Client using Personal API Token."""
    config = {
        "THREEDI_API_HOST": api_host,
        "THREEDI_API_USERNAME": "__key__",
        "THREEDI_API_PERSONAL_API_TOKEN": personal_api_token,
    }
    return ThreediApi(config=config, version=version)


def paginated_fetch(api_method: Callable, *args, **kwargs) -> List[Any]:
    """Method for iterative fetching of the data via given API endpoint."""
    limit = FETCH_LIMIT
    response = api_method(*args, limit=limit, **kwargs)
    response_count = response.count
    results_list = response.results
    if response_count > limit:
        for offset in range(limit, response_count, limit):
            response = api_method(*args, offset=offset, limit=limit, **kwargs)
            results_list += response.results
    return results_list


def expiration_time():
    return datetime.now(timezone.utc) - timedelta(days=7)


def expiration_date():
    created__date__gt = expiration_time().strftime("%Y-%m-%d")
    return created__date__gt


def fetch_models_with_count(
    threedi_api: ThreediApi,
    limit: int = None,
    offset: int = None,
    name_contains: str = None,
    schematisation_name: str = None,
    schematisation_owner: str = None,
    show_valid_and_invalid: bool = False,
) -> Tuple[List[ThreediModel], int]:
    """Fetch 3Di models available for current user."""
    params = {
        "revision__schematisation__isnull": False,
        "is_valid": True,
        "disabled": False,
    }
    if limit is not None:
        params["limit"] = limit
    if offset is not None:
        params["offset"] = offset
    if name_contains is not None:
        params["name__icontains"] = name_contains.lower()
    if schematisation_name is not None:
        params["revision__schematisation__name"] = schematisation_name
    if schematisation_owner is not None:
        params["revision__schematisation__owner__unique_id"] = schematisation_owner
    if show_valid_and_invalid:
        params["is_valid"] = ""
    response = threedi_api.threedimodels_list(**params)
    return response.results, response.count


def fetch_schematisations_with_count(
    threedi_api: ThreediApi,
    limit: int = None,
    offset: int = None,
    name_contains: str = None,
    ordering: str = None,
) -> Tuple[List[Schematisation], int]:
    """Get list of the schematisations with count."""
    params = {}
    if limit is not None:
        params["limit"] = limit
    if offset is not None:
        params["offset"] = offset
    if name_contains is not None:
        params["name__icontains"] = name_contains.lower()
    if ordering is not None:
        params["ordering"] = ordering
    response = threedi_api.schematisations_list(**params)
    return response.results, response.count


def fetch_schematisation(threedi_api, schematisation_pk: int, **data) -> Schematisation:
    """Get schematisation with given id."""
    return threedi_api.schematisations_read(id=schematisation_pk, **data)


def fetch_schematisation_revisions(
    threedi_api, schematisation_pk: int, committed: bool = True, **data
) -> List[SchematisationRevision]:
    return paginated_fetch(
        threedi_api.schematisations_revisions_list,
        schematisation_pk,
        committed=committed,
        **data,
    )


def fetch_schematisation_latest_revision(
    threedi_api, schematisation_pk: int
) -> SchematisationRevision:
    """Get latest schematisation revision."""
    return threedi_api.schematisations_latest_revision(schematisation_pk)


def fetch_schematisation_revisions_with_count(
    threedi_api,
    schematisation_pk: int,
    committed: bool = True,
    limit: int = None,
    offset: int = None,
) -> Tuple[List[SchematisationRevision], int]:
    """Get list of the schematisation revisions with count."""
    params = {}
    if limit is not None:
        params["limit"] = limit
    if offset is not None:
        params["offset"] = offset
    response = threedi_api.schematisations_revisions_list(
        schematisation_pk, committed=committed, **params
    )
    return response.results, response.count


def extract_error_message(e):
    """Extracting useful information from ApiException exceptions."""
    error_body = e.body
    try:
        if isinstance(error_body, str):
            error_body = json.loads(error_body)
        if "detail" in error_body:
            error_details = error_body["detail"]
        elif "details" in error_body:
            error_details = error_body["details"]
        elif "errors" in error_body:
            errors = error_body["errors"]
            try:
                error_parts = [
                    f"{err['reason']} ({err['instance']['related_object']})"
                    for err in errors
                ]
            except TypeError:
                error_parts = list(errors.values())
            error_details = "\n" + "\n".join(error_parts)
        else:
            error_details = str(error_body)
    except json.JSONDecodeError:
        error_details = str(error_body)
    return f"Error: {error_details}"


def get_download_file(download, file_path):
    """Getting file from Download object and writing it under given path."""
    r = requests.get(download.get_url, stream=True, timeout=15)
    with open(file_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=DOWNLOAD_CHUNK_SIZE):
            if chunk:
                f.write(chunk)


def fetch_schematisation_revision_models(
    threedi_api, schematisation_pk: int, revision_pk: int
) -> List[ThreediModel]:
    """Fetch 3Di models belonging to the particular schematisation revision."""
    return threedi_api.schematisations_revisions_threedimodels(
        revision_pk, schematisation_pk
    )


def download_schematisation_revision_sqlite(
    threedi_api, schematisation_pk: int, revision_pk: int
) -> Download:
    """Get schematisation revision sqlite Download object."""
    return threedi_api.schematisations_revisions_sqlite_download(
        revision_pk, schematisation_pk
    )


def download_schematisation_revision_raster(
    threedi_api, raster_pk: int, schematisation_pk: int, revision_pk: int
) -> Download:
    """Download schematisation revision raster."""
    return threedi_api.schematisations_revisions_rasters_download(
        raster_pk, revision_pk, schematisation_pk
    )


def fetch_model_gridadmin_download(
    threedi_api, threedimodel_id: int
) -> Tuple[ResultFile, Download]:
    """Fetch simulation model gridadmin file."""
    result_file = ResultFile(filename="gridadmin.h5", created=datetime.utcnow())
    download = threedi_api.threedimodels_gridadmin_download(threedimodel_id)
    return result_file, download


def fetch_model_geojson_breaches_download(
    threedi_api, threedimodel_id: int
) -> Download:
    """Fetch model geojson breaches Download object."""
    return threedi_api.threedimodels_geojson_breaches_download(threedimodel_id)


def fetch_model_geopackage_download(
    threedi_api, threedimodel_id: int
) -> Tuple[ResultFile, Download]:
    """Fetch simulation model gridadmin file in GeoPackage format."""
    result_file = ResultFile(filename="gridadmin.gpkg", created=datetime.utcnow())
    download = threedi_api.threedimodels_geopackage_download(threedimodel_id)
    return result_file, download


def create_schematisation_revision(
    threedi_api, schematisation_pk: int, empty: bool = False, **data
) -> SchematisationRevision:
    """Create a new schematisation revision."""
    data["empty"] = empty
    return threedi_api.schematisations_revisions_create(schematisation_pk, data)


def upload_schematisation_revision(
    threedi_api, schematisation_pk: int, revision_pk: int, filename: str, **data
) -> SqliteFileUpload:
    """Create a new schematisation revision SqliteFileUpload."""
    data["filename"] = filename
    return threedi_api.schematisations_revisions_sqlite_upload(
        revision_pk, schematisation_pk, data
    )


def create_schematisation(threedi_api, name: str, owner: str, **data) -> Schematisation:
    data.update({"name": name, "owner": owner})
    return threedi_api.schematisations_create(data)


def delete_schematisation_revision_sqlite(
    threedi_api, schematisation_pk: int, revision_pk: int
):
    threedi_api.schematisations_revisions_sqlite_delete(revision_pk, schematisation_pk)


def create_schematisation_revision_raster(
    threedi_api,
    schematisation_pk: int,
    revision_pk: int,
    name: str,
    raster_type: str = "dem_file",
    **data,
) -> RasterCreate:
    """Create a new schematisation revision raster."""
    raster_type = "dem_file" if raster_type == "dem_raw_file" else raster_type
    data.update({"name": name, "type": raster_type})
    return threedi_api.schematisations_revisions_rasters_create(
        revision_pk, schematisation_pk, data
    )


def fetch_schematisation_revision_rasters(
    threedi_api, schematisation_pk: int, revision_pk: int
) -> List[RevisionRaster]:
    return paginated_fetch(
        threedi_api.schematisations_revisions_rasters_list,
        revision_pk,
        schematisation_pk,
    )


def upload_schematisation_revision_raster(
    threedi_api, raster_pk: int, schematisation_pk: int, revision_pk: int, filename: str
) -> Upload:
    """Create a new schematisation revision raster Upload object."""
    return threedi_api.schematisations_revisions_rasters_upload(
        raster_pk, revision_pk, schematisation_pk, {"filename": filename}
    )


def delete_schematisation_revision_raster(
    threedi_api, raster_pk: int, schematisation_pk: int, revision_pk: int
):
    """Remove schematisation revision raster."""
    threedi_api.schematisations_revisions_rasters_delete(
        raster_pk, revision_pk, schematisation_pk
    )


def fetch_schematisation_revision(
    threedi_api, schematisation_pk: int, revision_pk: int
) -> SchematisationRevision:
    """Get schematisation revision."""
    schematisation_revision = threedi_api.schematisations_revisions_read(
        revision_pk, schematisation_pk
    )
    return schematisation_revision


def fetch_schematisation_revision_tasks(
    threedi_api, schematisation_pk: int, revision_pk: int
) -> List[RevisionTask]:
    """Get list of the schematisation revision tasks."""
    return paginated_fetch(
        threedi_api.schematisations_revisions_tasks_list, revision_pk, schematisation_pk
    )


def fetch_schematisation_revision_task(
    threedi_api, task_pk: int, schematisation_pk: int, revision_pk: int
) -> RevisionTask:
    """Get schematisation revision task."""
    return threedi_api.schematisations_revisions_tasks_read(
        task_pk, revision_pk, schematisation_pk
    )


def create_schematisation_revision_model(
    threedi_api,
    schematisation_pk: int,
    revision_pk: int,
    inherit_templates: bool = False,
) -> ThreediModel:
    """Create a new 3Di model out of committed revision."""
    data = {
        "inherit_from_previous_threedimodel": True,
        "inherit_from_previous_revision": inherit_templates,
    }
    return threedi_api.schematisations_revisions_create_threedimodel(
        revision_pk, schematisation_pk, data
    )


def commit_schematisation_revision(
    threedi_api, schematisation_pk: int, revision_pk: int, **data
) -> Commit:
    return threedi_api.schematisations_revisions_commit(
        revision_pk, schematisation_pk, data
    )


def fetch_model_tasks(threedi_api, threedimodel_id: str) -> List[ThreediModelTask]:
    """Fetch 3Di model tasks list."""
    return paginated_fetch(threedi_api.threedimodels_tasks_list, threedimodel_id)


def fetch_model(threedi_api, threedimodel_id: int) -> ThreediModel:
    return threedi_api.threedimodels_read(threedimodel_id)


def delete_model(threedi_api, threedimodel_id: int) -> None:
    """Delete 3Di model with a given id."""
    threedi_api.threedimodels_delete(threedimodel_id)


def fetch_models_with_count(
    threedi_api,
    limit: int = None,
    offset: int = None,
    name_contains: str = None,
    schematisation_name: str = None,
    schematisation_owner: str = None,
    show_valid_and_invalid: bool = False,
) -> Tuple[List[ThreediModel], int]:
    """Fetch 3Di models available for current user."""
    params = {
        "revision__schematisation__isnull": False,
        "is_valid": True,
        "disabled": False,
    }
    if limit is not None:
        params["limit"] = limit
    if offset is not None:
        params["offset"] = offset
    if name_contains is not None:
        params["name__icontains"] = name_contains.lower()
    if schematisation_name is not None:
        params["revision__schematisation__name"] = schematisation_name
    if schematisation_owner is not None:
        params["revision__schematisation__owner__unique_id"] = schematisation_owner
    if show_valid_and_invalid:
        params["is_valid"] = ""

    response = threedi_api.threedimodels_list(**params)
    models_list = response.results
    models_count = response.count
    return models_list, models_count


def fetch_contracts(threedi_api, **data) -> List[Contract]:
    """Get valid 3Di contracts list."""
    return paginated_fetch(threedi_api.contracts_list, **data)


def create_simulation_action(threedi_api, simulation_pk: int, **action_data) -> Action:
    """Make an action on 'simulation_pk' simulation."""
    return threedi_api.simulations_actions_create(str(simulation_pk), action_data)


def create_simulation(threedi_api, **simulation_data) -> Simulation:
    sim = Simulation(**simulation_data)
    return threedi_api.simulations_create(sim)


def fetch_simulations(threedi_api) -> List[Simulation]:
    """Fetch all simulations available for current user."""
    return paginated_fetch(
        threedi_api.simulations_list, created__date__gt=expiration_date()
    )


def fetch_simulation_status(threedi_api, simulation_pk: int) -> CurrentStatus:
    """Get a given simulation current status."""
    return threedi_api.simulations_status_list(str(simulation_pk), limit=FETCH_LIMIT)


def fetch_simulation(threedi_api, simulation_pk: int) -> Simulation:
    return threedi_api.simulations_read(id=simulation_pk)


def create_simulation_action(threedi_api, simulation_pk: int, **action_data) -> Action:
    """Make an action on 'simulation_pk' simulation."""
    return threedi_api.simulations_actions_create(str(simulation_pk), action_data)


def create_template_from_simulation(
    threedi_api, name: str, simulation_pk: str, **data
) -> Template:
    """Create simulation template out of the simulation."""
    data.update({"name": name, "simulation": simulation_pk})
    return threedi_api.simulation_templates_create(data)


def fetch_simulation_downloads(
    threedi_api, simulation_pk: int
) -> List[Tuple[ResultFile, Download]]:
    """Fetch simulation downloads list."""
    spk_str = str(simulation_pk)
    downloads = []
    results_list = paginated_fetch(threedi_api.simulations_results_files_list, spk_str)
    for result_file in results_list:
        download = threedi_api.simulations_results_files_download(
            result_file.id, spk_str
        )
        downloads.append((result_file, download))
    return downloads


def fetch_simulation_statuses(threedi_api, **params) -> List[SimulationStatus]:
    """Fetch simulations statuses."""
    params["created__date__gt"] = expiration_date()
    statuses = paginated_fetch(threedi_api.statuses_list, **params)
    return statuses


def fetch_simulation_settings_overview(
    threedi_api, simulation_pk: str
) -> SimulationSettingsOverview:
    """Get a simulation settings overview."""
    return threedi_api.simulations_settings_overview(simulation_pk=simulation_pk)


def fetch_simulation_events(threedi_api, simulation_pk: int) -> Event:
    """Get a simulation events collection."""
    return threedi_api.simulations_events(id=simulation_pk)


def fetch_simulation_lizard_postprocessing_overview(
    threedi_api, simulation_pk: int
) -> PostProcessingOverview:
    """Get a simulation lizard postprocessing overview."""
    return threedi_api.simulations_results_post_processing_lizard_overview_list(
        str(simulation_pk)
    )


def fetch_simulation_templates_with_count(
    threedi_api, simulation_pk: int = None, limit: int = None, offset: int = None
) -> Tuple[List[Template], int]:
    """Get list of the simulation templated with count."""
    params = {}
    if simulation_pk is not None:
        params["simulation__threedimodel__id"] = simulation_pk
    if limit is not None:
        params["limit"] = limit
    if offset is not None:
        params["offset"] = offset
    response = threedi_api.simulation_templates_list(**params)
    simulation_templates_list = response.results
    simulation_templates_count = response.count
    return simulation_templates_list, simulation_templates_count


def create_simulation_settings_physical(
    threedi_api, simulation_pk: int, **data
) -> PhysicalSettings:
    return threedi_api.simulations_settings_physical_create(str(simulation_pk), data)


def create_simulation_settings_numerical(
    threedi_api, simulation_pk: int, **data
) -> NumericalSettings:
    return threedi_api.simulations_settings_numerical_create(str(simulation_pk), data)


def create_simulation_settings_time_step(
    threedi_api, simulation_pk: int, **data
) -> TimeStepSettings:
    return threedi_api.simulations_settings_time_step_create(str(simulation_pk), data)


def create_simulation_settings_aggregation(
    threedi_api, simulation_pk: int, **data
) -> AggregationSettings:
    return threedi_api.simulations_settings_aggregation_create(str(simulation_pk), data)


def create_simulation_settings_water_quality(
    threedi_api, simulation_pk: int, **data
) -> WaterQualitySettings:
    return threedi_api.simulations_settings_water_quality_create(
        str(simulation_pk), data
    )


class SchematisationApiMapper:
    """This class maps types between the geopackage and the API"""

    @staticmethod
    def settings_to_api_raster_types():
        raster_type_map = {
            "friction_coefficient_file": "frict_coef_file",
            "max_infiltration_volume_file": "max_infiltration_capacity_file",
            "groundwater_hydraulic_conductivity_file": "groundwater_hydro_connectivity_file",
            "initial_water_level_file": "initial_waterlevel_file",
        }
        return raster_type_map

    @staticmethod
    def api_to_settings_raster_types():
        raster_type_map = {
            v: k
            for k, v in SchematisationApiMapper.settings_to_api_raster_types().items()
        }
        return raster_type_map

    @staticmethod
    def api_client_raster_type(settings_raster_type):
        try:
            return SchematisationApiMapper.settings_to_api_raster_types()[
                settings_raster_type
            ]
        except KeyError:
            return settings_raster_type

    @staticmethod
    def settings_raster_type(api_raster_type):
        try:
            return SchematisationApiMapper.api_to_settings_raster_types()[
                api_raster_type
            ]
        except KeyError:
            return api_raster_type

    @staticmethod
    def model_settings_rasters():
        """Rasters mapping from the Model settings layer."""
        raster_info = OrderedDict(
            (
                ("dem_file", "Digital elevation model [m MSL]"),
                ("friction_coefficient_file", "Friction coefficient [-]"),
            )
        )
        return raster_info

    @staticmethod
    def initial_conditions_rasters():
        """Rasters mapping for the Initial conditions."""
        raster_info = OrderedDict(
            (
                ("initial_groundwater_level_file", "Initial groundwater level [m MSL]"),
                ("initial_water_level_file", "Initial water level [m MSL]"),
            )
        )
        return raster_info

    @staticmethod
    def interception_rasters():
        """Rasters mapping for the Interception."""
        raster_info = OrderedDict((("interception_file", "Interception [m]"),))
        return raster_info

    @staticmethod
    def simple_infiltration_rasters():
        """Rasters mapping for the Infiltration."""
        raster_info = OrderedDict(
            (
                ("infiltration_rate_file", "Infiltration rate [mm/d]"),
                ("max_infiltration_volume_file", "Max infiltration volume [m]"),
            )
        )
        return raster_info

    @staticmethod
    def groundwater_rasters():
        """Rasters mapping for the Groundwater."""
        raster_info = OrderedDict(
            (
                (
                    "equilibrium_infiltration_rate_file",
                    "Equilibrium infiltration rate [mm/d]",
                ),
                (
                    "groundwater_hydraulic_conductivity_file",
                    "Hydraulic conductivity [m/day]",
                ),
                (
                    "groundwater_impervious_layer_level_file",
                    "Impervious layer level [m MSL]",
                ),
                ("infiltration_decay_period_file", "Infiltration decay period [d]"),
                ("initial_infiltration_rate_file", "Initial infiltration rate [mm/d]"),
                ("leakage_file", "Leakage [mm/d]"),
                ("phreatic_storage_capacity_file", "Phreatic storage capacity [-]"),
            )
        )
        return raster_info

    @staticmethod
    def interflow_rasters():
        """Rasters mapping for the Interflow."""
        raster_info = OrderedDict(
            (
                ("hydraulic_conductivity_file", "Hydraulic conductivity [m/d]"),
                ("porosity_file", "Porosity [-]"),
            )
        )
        return raster_info

    @staticmethod
    def vegetation_drag_rasters():
        """Rasters mapping for the Vegetation drag settings."""
        raster_info = OrderedDict(
            (
                ("vegetation_height_file", "Vegetation height [m]"),
                ("vegetation_stem_count_file", "Vegetation stem count [-]"),
                ("vegetation_stem_diameter_file", "Vegetation stem diameter [m]"),
                ("vegetation_drag_coefficient_file", "Vegetation drag coefficient [-]"),
            )
        )
        return raster_info

    @classmethod
    def raster_reference_tables(cls):
        """GeoPackage tables mapping with references to the rasters."""
        reference_tables = OrderedDict(
            (
                ("model_settings", cls.model_settings_rasters()),
                ("initial_conditions", cls.initial_conditions_rasters()),
                ("interception", cls.interception_rasters()),
                ("simple_infiltration", cls.simple_infiltration_rasters()),
                ("groundwater", cls.groundwater_rasters()),
                ("interflow", cls.interflow_rasters()),
                ("vegetation_drag_2d", cls.vegetation_drag_rasters()),
            )
        )
        return reference_tables

    @classmethod
    def raster_table_mapping(cls):
        """Rasters to geopackage tables mapping."""
        table_mapping = {}
        for (
            table_name,
            raster_files_references,
        ) in cls.raster_reference_tables().items():
            for raster_type in raster_files_references.keys():
                table_mapping[raster_type] = table_name
        return table_mapping

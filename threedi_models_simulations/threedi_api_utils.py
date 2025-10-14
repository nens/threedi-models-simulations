import datetime
import json
from typing import Any, Callable, List, Tuple

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


def fetch_schematisation_revision_3di_models(
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


def fetch_3di_model_gridadmin_download(
    threedi_api, threedimodel_id: int
) -> Tuple[ResultFile, Download]:
    """Fetch simulation model gridadmin file."""
    result_file = ResultFile(filename="gridadmin.h5", created=datetime.utcnow())
    download = threedi_api.threedimodels_gridadmin_download(threedimodel_id)
    return result_file, download


def fetch_3di_model_geopackage_download(
    threedi_api, threedimodel_id: int
) -> Tuple[ResultFile, Download]:
    """Fetch simulation model gridadmin file in GeoPackage format."""
    result_file = ResultFile(filename="gridadmin.gpkg", created=datetime.utcnow())
    download = threedi_api.threedimodels_geopackage_download(threedimodel_id)
    return result_file, download

import json
from typing import Any, Callable, List

from threedi_api_client import ThreediApi

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
    error_msg = f"Error: {error_details}"
    return error_msg

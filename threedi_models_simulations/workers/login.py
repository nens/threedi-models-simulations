from qgis.PyQt.QtCore import QThread, pyqtSignal
from threedi_api_client import ThreediApi
from threedi_api_client.openapi import ApiException

from threedi_models_simulations.authentication import get_3di_auth
from threedi_models_simulations.utils.threedi_api import (
    extract_error_message,
    get_api_client_with_personal_api_token,
    paginated_fetch,
)
from threedi_models_simulations.widgets.settings import api_url


class AuthorizationException(Exception):
    pass


class LoginWorker(QThread):
    api_success = pyqtSignal(ThreediApi)
    profile_success = pyqtSignal(dict)
    org_success = pyqtSignal(dict)
    error = pyqtSignal(str)
    settings_requested = pyqtSignal()

    def run(self):
        try:
            username, personal_api_token = get_3di_auth()
            if not username or not personal_api_token:
                raise AuthorizationException("Personal API Key is not set.")

            threedi_api = get_api_client_with_personal_api_token(
                personal_api_token, api_url()
            )
            self.api_success.emit(threedi_api)

            user_profile = threedi_api.auth_profile_list()
            user_info = {
                "username": user_profile.username,
                "first_name": user_profile.first_name,
                "last_name": user_profile.last_name,
            }

            self.profile_success.emit(user_info)
            organisations = paginated_fetch(threedi_api.organisations_list)
            orgs = {org.unique_id: org for org in organisations}
            self.org_success.emit(orgs)

        except ApiException as e:
            api_url_error_message = (
                f"Error: Invalid Base API URL '{api_url()}'. "
                f"The 3Di API expects that the version is not included. "
                f"Please change the Base API URL in the 3Di Models and Simulations plugin settings."
            )
            ssl_error_message = (
                "An error occurred. This specific error is probably caused by issues with an expired SSL "
                "certificate that has not properly been removed by your operating system. Please ask your system "
                "administrator to remove this expired SSL certificate manually. Instructions can be found here: "
                "https://docs.3di.live/f_problem_solving.html#connecting-to-the-3di-api"
            )
            if e.status == 404:
                error_msg = api_url_error_message
            else:
                error_msg = extract_error_message(e)
            if "SSLError" in error_msg:
                error_msg = f"{ssl_error_message}\n\n{error_msg}"
            self.error.emit(error_msg)
        except AuthorizationException:
            self.error.emit(
                "Personal API Key is not filled. Please set it in the Settings Dialog."
            )
            self.settings_requested.emit()
        except Exception as e:
            if "THREEDI_API_HOST" in str(e):
                error_msg = api_url_error_message
            else:
                error_msg = f"Error: {e}"
            self.error.emit(error_msg)

from enum import Enum

from qgis.PyQt.QtCore import QSettings

from threedi_models_simulations.communication import UICommunication
from threedi_models_simulations.utils import get_schematisation_editor_instance
from threedi_models_simulations.widgets.schematisation_download_dialog import (
    SchematisationDownloadDialog,
)

# from threedi_models_simulations.widgets.login import LogInDialog
# from ..utils import NestedObject
# from ..widgets.new_schematisation_wizard import NewSchematisationWizard
from threedi_models_simulations.widgets.schematisation_load_dialog import (
    SchematisationLoadDialog,
)


class SchematisationLoaderActions(Enum):
    CREATED = "created"
    LOADED = "loaded"
    DOWNLOADED = "downloaded"


class SchematisationLoader:
    """Schematisation build options class."""

    def __init__(self, parent):
        self.parent = parent

    # # @api_client_required  # TODO
    # def new_schematisation(self):
    #     """Create a new schematisation."""
    #     self.new_schematisation_wizard = NewSchematisationWizard(self.plugin_dock)
    #     self.new_schematisation_wizard.exec_()
    #     new_schematisation = self.new_schematisation_wizard.new_schematisation
    #     if new_schematisation is not None:
    #         local_schematisation = self.new_schematisation_wizard.new_local_schematisation
    #         self.load_local_schematisation(local_schematisation, action=SchematisationLoaderActions.CREATED)

    def load_local_schematisation(
        self,
        local_schematisation=None,
        action=SchematisationLoaderActions.LOADED,
        custom_geopackage_filepath=None,
    ):
        """Load locally stored schematisation. Returns schematisation"""
        if not local_schematisation:
            work_dir = QSettings().value("threedi/working_dir", "")
            schematisation_load = SchematisationLoadDialog(work_dir, self.parent)
            schematisation_load.exec()
            local_schematisation = schematisation_load.selected_local_schematisation
        if local_schematisation and local_schematisation.schematisation_db_filepath:
            try:
                geopackage_filepath = (
                    local_schematisation.schematisation_db_filepath
                    if not custom_geopackage_filepath
                    else custom_geopackage_filepath
                )
                msg = f"Schematisation '{local_schematisation.name}' {action.value}!\n"
                UICommunication.bar_info(msg)
                # Load new schematisation
                schematisation_editor = get_schematisation_editor_instance()
                if schematisation_editor:
                    title = "Load schematisation"
                    question = "Do you want to load schematisation data from the associated GeoPackage file?"
                    if UICommunication.ask(None, title, question):
                        schematisation_editor.load_schematisation(geopackage_filepath)
                else:
                    msg += (
                        "Please use the 3Di Schematisation Editor to load it to your project from the GeoPackage:"
                        f"\n{geopackage_filepath}"
                    )
                    UICommunication.show_warn(msg, self.parent, "Schematisation")
                return local_schematisation
            except (TypeError, ValueError):
                error_msg = "Invalid schematisation directory structure. Loading schematisation canceled."
                UICommunication.show_error(error_msg, self.parent, "Schematisation")
        return None

    # # @api_client_required  # TODO
    def download_schematisation(self, threedi_api, organisations):
        """Download an existing schematisation. Returns the local schematisation"""
        work_dir = QSettings().value("threedi/working_dir", "")
        schematisation_download = SchematisationDownloadDialog(
            work_dir, threedi_api, organisations, self.parent
        )
        schematisation_download.exec()
        downloaded_local_schematisation = (
            schematisation_download.downloaded_local_schematisation
        )
        custom_geopackage_filepath = (
            schematisation_download.downloaded_geopackage_filepath
        )
        if downloaded_local_schematisation is not None:
            local_schematisation = self.load_local_schematisation(
                local_schematisation=downloaded_local_schematisation,
                action=SchematisationLoaderActions.DOWNLOADED,
                custom_geopackage_filepath=custom_geopackage_filepath,
            )
            wip_revision = downloaded_local_schematisation.wip_revision
            if wip_revision is not None:
                settings = QSettings("3di", "qgisplugin")
                settings.setValue(
                    "last_used_geopackage_path", wip_revision.schematisation_dir
                )
            return local_schematisation
        return None

    # # @api_client_required  # TODO
    # def load_remote_schematisation(self, schematisation, revision, progress_bar = None):
    #     """Download and load a schematisation from the server."""
    #     if isinstance(schematisation, dict):
    #         schematisation = NestedObject(schematisation)
    #     if isinstance(revision, dict):
    #         revision = NestedObject(revision)

    #     # Download and load the schematisation
    #     schematisation_download = SchematisationDownload(self.plugin_dock)
    #     schematisation_download.download_required_files(schematisation, revision, True, progress_bar)
    #     downloaded_local_schematisation = schematisation_download.downloaded_local_schematisation
    #     custom_geopackage_filepath = schematisation_download.downloaded_geopackage_filepath
    #     if downloaded_local_schematisation is not None:
    #         self.load_local_schematisation(
    #             local_schematisation=downloaded_local_schematisation,
    #             action=SchematisationLoaderActions.DOWNLOADED,
    #             custom_geopackage_filepath=custom_geopackage_filepath,
    #         )
    #         wip_revision = downloaded_local_schematisation.wip_revision
    #         if wip_revision is not None:
    #             settings = QSettings("3di", "qgisplugin")
    #             settings.setValue("last_used_geopackage_path", wip_revision.schematisation_dir)

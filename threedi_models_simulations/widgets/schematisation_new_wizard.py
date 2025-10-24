import os
import shutil
import time
from collections import defaultdict
from operator import itemgetter

from qgis.core import QgsFeature
from qgis.PyQt.QtCore import QSettings, QSize, Qt
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtWidgets import QSizePolicy, QWizard
from threedi_api_client.openapi import ApiException
from threedi_mi_utils import LocalSchematisation
from threedi_schema import ThreediDatabase

from threedi_models_simulations.threedi_api_utils import (
    SchematisationApiMapper,
    create_schematisation,
    extract_error_message,
)
from threedi_models_simulations.utils.general import ensure_valid_schema
from threedi_models_simulations.utils.qgis import geopackage_layer
from threedi_models_simulations.widgets.new_wizard_pages.explain import (
    SchematisationExplainPage,
)
from threedi_models_simulations.widgets.new_wizard_pages.name import (
    SchematisationNamePage,
)
from threedi_models_simulations.widgets.new_wizard_pages.settings import (
    SchematisationSettingsPage,
)


class CommitErrors(Exception):
    pass


class GeoPackageError(Exception):
    pass


class NewSchematisationWizard(QWizard):
    """New schematisation wizard."""

    def __init__(self, threedi_api, working_dir, communication, organisations, parent):
        super().__init__(parent)
        self.setWizardStyle(QWizard.ClassicStyle)
        self.working_dir = working_dir
        self.threedi_api = threedi_api
        self.communication = communication
        self.new_schematisation = None
        self.new_local_schematisation = None

        self.schematisation_name_page = SchematisationNamePage(organisations, self)
        self.schematisation_explain_page = SchematisationExplainPage(self)
        self.schematisation_settings_page = SchematisationSettingsPage(
            self.communication, self
        )
        self.addPage(self.schematisation_name_page)
        self.addPage(self.schematisation_explain_page)
        self.addPage(self.schematisation_settings_page)
        self.setButtonText(QWizard.FinishButton, "Create schematisation")
        self.finish_btn = self.button(QWizard.FinishButton)
        self.finish_btn.clicked.connect(self.create_schematisation)
        self.cancel_btn = self.button(QWizard.CancelButton)
        self.cancel_btn.clicked.connect(self.cancel_wizard)
        self.setWindowTitle("New schematisation")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setOption(QWizard.HaveNextButtonOnLastPage, False)
        self.resize(
            QSettings().value("threedi/new_schematisation_wizard_size", QSize(790, 700))
        )

    def create_schematisation(self):
        if self.schematisation_name_page.field("from_geopackage"):
            self.create_schematisation_from_geopackage()
        else:
            self.create_new_schematisation()

    def create_new_schematisation(self):
        """Get settings from the wizard and create new schematisation (locally and remotely)."""
        if not self.schematisation_settings_page.settings_are_valid:
            return

        name = self.schematisation_name_page.field("schematisation_name")
        description = self.schematisation_name_page.field("schematisation_description")
        tags = self.schematisation_name_page.field("schematisation_tags")
        if not tags:
            tags = []
        else:
            tags = [tag.strip() for tag in tags.split(",")]

        organisation = self.schematisation_name_page.field(
            "schematisation_organisation"
        )
        owner = organisation.unique_id

        schematisation_settings = self.schematisation_settings_page.main_widget.collect_new_schematisation_settings()
        raster_filepaths = (
            self.schematisation_settings_page.main_widget.raster_filepaths()
        )
        try:
            schematisation = create_schematisation(
                self.threedi_api,
                name,
                owner,
                tags=tags,
                meta={"description": description},
            )
            local_schematisation = LocalSchematisation(
                self.working_dir,
                schematisation.id,
                name,
                parent_revision_number=0,
                create=True,
            )
            wip_revision = local_schematisation.wip_revision

            schematisation_filename = f"{name}.gpkg"
            geopackage_filepath = os.path.join(
                wip_revision.schematisation_dir, schematisation_filename
            )
            empty_db = ThreediDatabase(geopackage_filepath)
            empty_db.schema.upgrade(
                epsg_code_override=schematisation_settings["model_settings"][
                    "epsg_code"
                ]
            )

            for raster_filepath in raster_filepaths:
                if raster_filepath:
                    new_raster_filepath = os.path.join(
                        wip_revision.raster_dir, os.path.basename(raster_filepath)
                    )
                    shutil.copyfile(raster_filepath, new_raster_filepath)
            for table_name, table_settings in schematisation_settings.items():
                table_layer = geopackage_layer(
                    wip_revision.schematisation_db_filepath, table_name
                )
                table_layer.startEditing()
                table_fields = table_layer.fields()
                table_fields_names = {f.name() for f in table_fields}
                # Note that this assumes that all columns have the same length!!!
                nrows = (
                    len(list(table_settings.values())[0])
                    if isinstance(list(table_settings.values())[0], list)
                    else 1
                )
                for i in range(nrows):
                    new_settings_feat = QgsFeature(table_fields)
                    for field_name, field_value in table_settings.items():
                        if field_name in table_fields_names:
                            if isinstance(field_value, list):
                                new_settings_feat[field_name] = field_value[i]
                            else:
                                new_settings_feat[field_name] = field_value
                    table_layer.addFeature(new_settings_feat)
                success = table_layer.commitChanges()

                if not success:
                    commit_errors = table_layer.commitErrors()
                    errors_str = "\n".join(commit_errors)
                    error = CommitErrors(f"{table_name} commit errors:\n{errors_str}")
                    raise error
            time.sleep(0.5)
            self.new_schematisation = schematisation
            self.new_local_schematisation = local_schematisation
            msg = f"Schematisation '{name} ({schematisation.id})' created!"
            self.communication.bar_info(msg, log_text_color=QColor(Qt.darkGreen))
        except ApiException as e:
            self.new_schematisation = None
            self.new_local_schematisation = None
            error_msg = extract_error_message(e)
            self.communication.bar_error(error_msg, log_text_color=QColor(Qt.red))
        except Exception as e:
            self.new_schematisation = None
            self.new_local_schematisation = None
            error_msg = f"Error: {e}"
            self.communication.bar_error(error_msg, log_text_color=QColor(Qt.red))

    @staticmethod
    def get_paths_from_geopackage(geopackage_path):
        """Search GeoPackage database tables for attributes with file paths."""
        paths = defaultdict(dict)
        for (
            table_name,
            raster_info,
        ) in SchematisationApiMapper.raster_reference_tables().items():
            settings_fields = list(raster_info.keys())
            settings_lyr = geopackage_layer(geopackage_path, table_name)
            if not settings_lyr.isValid():
                raise GeoPackageError(
                    f"'{table_name}' table could not be loaded from {geopackage_path}"
                )
            try:
                set_feat = next(settings_lyr.getFeatures())
            except StopIteration:
                continue
            for field_name in settings_fields:
                field_value = set_feat[field_name]
                paths[table_name][field_name] = field_value if field_value else None
        return paths

    def create_schematisation_from_geopackage(self):
        """Get settings from existing GeoPackage and create new schematisation (locally and remotely)."""
        try:
            src_db = self.schematisation_name_page.field("geopackage_path")
            schema_is_valid = ensure_valid_schema(  # possible migration
                src_db, self.communication
            )
            if schema_is_valid is True:
                if src_db.lower().endswith(".sqlite"):
                    src_db = src_db.rsplit(".", 1)[0] + ".gpkg"
            else:
                return  # ensure_valid_schema deals with showing errors.

            name = self.schematisation_name_page.field("schematisation_name")
            description = self.schematisation_name_page.field(
                "schematisation_description"
            )
            tags = self.schematisation_name_page.field("schematisation_tags")
            if not tags:
                tags = []
            else:
                tags = [tag.strip() for tag in tags.split(",")]

            organisation = self.schematisation_name_page.field(
                "schematisation_organisation"
            )
            owner = organisation.unique_id

            schematisation = create_schematisation(
                self.threedi_api,
                name,
                owner,
                tags=tags,
                meta={"description": description},
            )

            local_schematisation = LocalSchematisation(
                self.working_dir,
                schematisation.id,
                name,
                parent_revision_number=0,
                create=True,
            )
            wip_revision = local_schematisation.wip_revision
            geopackage_filepath = os.path.join(
                wip_revision.schematisation_dir, f"{name}.gpkg"
            )
            raster_paths = self.get_paths_from_geopackage(src_db)
            src_dir = os.path.dirname(src_db)
            shutil.copyfile(src_db, geopackage_filepath)
            new_paths = defaultdict(dict)
            missing_rasters = []
            for table_name, raster_paths_info in raster_paths.items():
                for raster_name, raster_rel_path in raster_paths_info.items():
                    if not raster_rel_path:
                        continue
                    raster_full_path = os.path.join(src_dir, "rasters", raster_rel_path)
                    if os.path.exists(raster_full_path):
                        new_raster_filepath = os.path.join(
                            wip_revision.raster_dir, os.path.basename(raster_rel_path)
                        )
                        shutil.copyfile(raster_full_path, new_raster_filepath)
                        new_paths[table_name][raster_name] = os.path.relpath(
                            new_raster_filepath, wip_revision.schematisation_dir
                        )
                    else:
                        new_paths[table_name][raster_name] = None
                        missing_rasters.append((raster_name, raster_rel_path))
            if missing_rasters:
                missing_rasters.sort(key=itemgetter(0))
                missing_rasters_string = "\n".join(
                    f"{rname}: {rpath}" for rname, rpath in missing_rasters
                )
                warn_msg = f"Warning: the following raster files where not found:\n{missing_rasters_string}"
                self.communication.show_warn(warn_msg, self, "Warning")
                self.communication.bar_warn("Schematisation creation aborted!")
                return
            self.new_schematisation = schematisation
            self.new_local_schematisation = local_schematisation
            msg = f"Schematisation '{name} ({schematisation.id})' created!"
            self.communication.bar_info(msg, log_text_color=QColor(Qt.darkGreen))
        except ApiException as e:
            self.new_schematisation = None
            self.new_local_schematisation = None
            error_msg = extract_error_message(e)
            self.communication.bar_error(error_msg, log_text_color=QColor(Qt.red))
        except Exception as e:
            self.new_schematisation = None
            self.new_local_schematisation = None
            error_msg = f"Error: {e}"
            self.communication.bar_error(error_msg, log_text_color=QColor(Qt.red))

    def cancel_wizard(self):
        """Handling canceling wizard action."""
        QSettings().setValue("threedi/new_schematisation_wizard_size", self.size())
        self.reject()

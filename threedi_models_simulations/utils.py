import hashlib
import os
import shutil
import warnings
from uuid import uuid4
from zipfile import ZIP_DEFLATED, ZipFile

from qgis.core import QgsVectorLayer
from qgis.PyQt.QtCore import QSettings
from qgis.PyQt.QtWidgets import QFileDialog
from qgis.utils import plugins


def is_writable(working_dir: str) -> bool:
    """Try to write and remove an empty text file into given location."""
    try:
        test_filename = f"{uuid4()}.txt"
        test_file_path = os.path.join(working_dir, test_filename)
        with open(test_file_path, "w") as test_file:
            test_file.write("")
        os.remove(test_file_path)
    except (PermissionError, OSError):
        return False
    else:
        return True


def get_plugin_instance(plugin_name):
    """Return given plugin name instance."""
    try:
        plugin_instance = plugins[plugin_name]
    except (AttributeError, KeyError):
        plugin_instance = None
    return plugin_instance


def get_schematisation_editor_instance():
    """Return Schematisation Editor plugin instance."""
    return get_plugin_instance("threedi_schematisation_editor")


def is_loaded_in_schematisation_editor(local_schematisation_gpkg):
    """Check if local schematisation revision is loaded in the Schematisation Editor."""
    if local_schematisation_gpkg is None:
        return None
    local_schematisation_gpkg = os.path.normpath(local_schematisation_gpkg)
    try:
        schematisation_editor = plugins["threedi_schematisation_editor"]
        return (
            local_schematisation_gpkg
            in schematisation_editor.workspace_context_manager.layer_managers
        )
    except KeyError:
        return None


def unzip_archive(zip_filepath, location=None):
    """Unzip archive content."""
    if not location:
        location = os.path.dirname(zip_filepath)
    with ZipFile(zip_filepath, "r") as zf:
        content_list = zf.namelist()
        zf.extractall(location)
        return content_list


def zip_into_archive(file_path, compression=ZIP_DEFLATED):
    """Zip file."""
    zip_filename = os.path.basename(file_path)
    zip_filepath = file_path.rsplit(".", 1)[0] + ".zip"
    with ZipFile(zip_filepath, "w", compression=compression) as zf:
        zf.write(file_path, arcname=zip_filename)
    return zip_filepath


def migrate_schematisation_schema(schematisation_filepath, progress_callback=None):
    migration_succeed = False
    srid = None

    try:
        from threedi_schema import ThreediDatabase, errors

        backup_filepath = backup_schematisation_file(schematisation_filepath)
        threedi_db = ThreediDatabase(schematisation_filepath)
        schema = threedi_db.schema
        srid, _ = schema._get_epsg_data()
        if srid is None:
            try:
                srid = schema._get_dem_epsg()
            except errors.InvalidSRIDException:
                srid = None
        if srid is None:
            migration_feedback_msg = "Could not fetch valid EPSG code from database or DEM; aborting database migration."
    except ImportError:
        migration_feedback_msg = "Missing threedi-schema library (or its dependencies). Schema migration failed."
    except Exception as e:
        migration_feedback_msg = f"{e}"

    if srid is not None:
        migration_feedback_msg = ""
        try:
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always", UserWarning)
                schema.upgrade(
                    backup=False,
                    epsg_code_override=srid,
                    progress_func=progress_callback,
                )
            if w:
                for warning in w:
                    migration_feedback_msg += (
                        f"{warning._category_name}: {warning.message}\n"
                    )
            shutil.rmtree(os.path.dirname(backup_filepath))
            migration_succeed = True
        except errors.UpgradeFailedError:
            migration_feedback_msg = (
                "The schematisation database schema cannot be migrated to the current version. "
                "Please contact the service desk for assistance."
            )
        except Exception as e:
            migration_feedback_msg = f"{e}"

    return migration_succeed, migration_feedback_msg


def backup_schematisation_file(filename):
    """Make a backup of the schematisation file."""
    backup_folder = os.path.join(os.path.dirname(os.path.dirname(filename)), "_backup")
    os.makedirs(backup_folder, exist_ok=True)
    prefix = str(uuid4())[:8]
    backup_file_path = os.path.join(
        backup_folder, f"{prefix}_{os.path.basename(filename)}"
    )
    shutil.copyfile(filename, backup_file_path)
    return backup_file_path


def geopackage_layer(gpkg_path, table_name, layer_name=None):
    """Creating vector layer out of GeoPackage source."""
    uri = f"{gpkg_path}|layername={table_name}"
    layer_name = table_name if layer_name is None else layer_name
    vlayer = QgsVectorLayer(uri, layer_name, "ogr")
    return vlayer


def get_filepath(
    parent, extension_filter=None, extension=None, save=False, dialog_title=None
):
    """Opening dialog to get a filepath."""
    if extension_filter is None:
        extension_filter = "All Files (*.*)"

    if dialog_title is None:
        dialog_title = "Choose file"

    working_dir = QSettings().value(
        "threedi/working_dir", os.path.expanduser("~"), type=str
    )
    starting_dir = QSettings().value(
        "threedi/last_schematisation_folder", working_dir, type=str
    )
    if save is True:
        file_name, __ = QFileDialog.getSaveFileName(
            parent, dialog_title, starting_dir, extension_filter
        )
    else:
        file_name, __ = QFileDialog.getOpenFileName(
            parent, dialog_title, starting_dir, extension_filter
        )
    if len(file_name) == 0:
        return None

    if extension:
        if not file_name.endswith(extension):
            file_name += extension

    QSettings().setValue(
        "threedi/last_schematisation_folder", os.path.dirname(file_name)
    )
    return file_name


def is_file_checksum_equal(file_path, etag):
    """Checking if etag (MD5 checksum) matches checksum calculated for a given file."""
    with open(file_path, "rb") as file_to_check:
        data = file_to_check.read()
        md5_returned = hashlib.md5(data).hexdigest()
        return etag == md5_returned

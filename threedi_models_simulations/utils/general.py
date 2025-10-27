import json
import os
import re
import shutil
import warnings
from uuid import uuid4

import requests
from qgis.gui import QgsFileWidget, QgsProjectionSelectionWidget
from qgis.PyQt.QtCore import QLocale, QSettings, Qt
from qgis.PyQt.QtGui import QPen
from qgis.PyQt.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDoubleSpinBox,
    QFileDialog,
    QGroupBox,
    QLineEdit,
    QRadioButton,
    QSpinBox,
    QStyledItemDelegate,
    QTimeEdit,
    QWidget,
)

from threedi_models_simulations.communication import progress_bar_callback_factory
from threedi_models_simulations.constants import DOWNLOAD_CHUNK_SIZE


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


def ensure_valid_schema(schematisation_filepath, communication):
    """Check if schema version is up-to-date and migrate it if needed."""
    try:
        from threedi_schema import ThreediDatabase, errors
    except ImportError:
        communication.show_error(
            "Could not import `threedi-schema` library to validate database schema."
        )
        return
    try:
        threedi_db = ThreediDatabase(schematisation_filepath)

        # Add additional check to deal with legacy gpkgs created by schematisation editor
        if schematisation_filepath.endswith(".gpkg"):
            version_num = threedi_db.schema.get_version()
            if version_num < 300:
                warn_msg = "The selected file is not a valid 3Di schematisation database.\n\nYou may have selected a geopackage that was created by an older version of the 3Di Schematisation Editor (before version 2.0). In that case, there will probably be a Spatialite (*.sqlite) in the same folder. Please use that file instead."
                communication.show_error(warn_msg)
                return False

        threedi_db.schema.validate_schema()
    except errors.MigrationMissingError:
        warn_and_ask_msg = (
            "The selected schematisation database cannot be used because its database schema version is out of date. "
            "Would you like to migrate your schematisation to the current schema version?"
        )
        do_migration = communication.ask(None, "Missing migration", warn_and_ask_msg)
        if not do_migration:
            return False
        progress_bar_callback = progress_bar_callback_factory(communication)
        migration_succeed, migration_feedback_msg = migrate_schematisation_schema(
            schematisation_filepath, progress_bar_callback
        )
        if not migration_succeed:
            communication.show_error(migration_feedback_msg)
            return False
    except Exception as e:
        error_msg = f"{e}"
        communication.show_error(error_msg)
        return False
    return True


def scan_widgets_parameters(
    main_widget, get_combobox_text, remove_postfix, lineedits_as_float_or_none
):
    """Scan widget children and get their values.

    In Qt Designer, widgets in the same UI file need to have an unique object name. When an object
    name already exist, Qt designer adds a _2 postfix. Use remove_postfix to remove these.
    """
    parameters = {}
    for widget in main_widget.children():
        obj_name = widget.objectName()
        if remove_postfix:
            result = re.match("^(.+)(_\d+)$", obj_name)
            if result is not None:
                obj_name = result.group(1)

        if isinstance(widget, QLineEdit):
            if lineedits_as_float_or_none:
                if widget.text():
                    val, to_float_possible = QLocale().toFloat(widget.text())
                    assert to_float_possible  # Should be handled by validators
                    if (
                        "e" in widget.text().lower()
                    ):  # we use python buildin for scientific notation
                        parameters[obj_name] = float(widget.text())
                    else:
                        parameters[obj_name] = val
                else:
                    parameters[obj_name] = None
            else:
                parameters[obj_name] = widget.text()
        elif isinstance(widget, (QCheckBox, QRadioButton)):
            parameters[obj_name] = widget.isChecked()
        elif isinstance(widget, QComboBox):
            parameters[obj_name] = (
                widget.currentText() if get_combobox_text else widget.currentIndex()
            )
        elif isinstance(widget, QDateEdit):
            parameters[obj_name] = widget.dateTime().toString("yyyy-MM-dd")
        elif isinstance(widget, QTimeEdit):
            parameters[obj_name] = widget.time().toString("H:m")
        elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
            parameters[obj_name] = widget.value() if widget.text() else None
        elif isinstance(widget, QgsProjectionSelectionWidget):
            parameters[obj_name] = widget.crs()
        elif isinstance(widget, QgsFileWidget):
            parameters[obj_name] = widget.filePath()
        elif isinstance(widget, QGroupBox):
            if widget.isCheckable():
                is_checked = widget.isChecked()
                parameters[obj_name] = is_checked
                if is_checked:
                    parameters.update(
                        scan_widgets_parameters(
                            widget,
                            get_combobox_text=get_combobox_text,
                            remove_postfix=remove_postfix,
                            lineedits_as_float_or_none=lineedits_as_float_or_none,
                        )
                    )
            else:
                parameters.update(
                    scan_widgets_parameters(
                        widget,
                        get_combobox_text=get_combobox_text,
                        remove_postfix=remove_postfix,
                        lineedits_as_float_or_none=lineedits_as_float_or_none,
                    )
                )
        elif isinstance(widget, QWidget):
            parameters.update(
                scan_widgets_parameters(
                    widget,
                    get_combobox_text=get_combobox_text,
                    remove_postfix=remove_postfix,
                    lineedits_as_float_or_none=lineedits_as_float_or_none,
                )
            )
    return parameters


def upload_local_file(upload, filepath):
    """Upload file."""
    with open(filepath, "rb") as file:
        response = requests.put(upload.put_url, data=file)
        return response


def read_json_data(json_filepath):
    """Parse and return data from JSON file."""
    with open(json_filepath, "r+") as json_file:
        data = json.load(json_file)
        return data


def write_json_data(values, json_file_template):
    """Writing data to the JSON file."""
    with open(json_file_template, "w") as json_file:
        jsonf = json.dumps(values)
        json_file.write(jsonf)


def get_download_file(download, file_path):
    """Getting file from Download object and writing it under given path."""
    r = requests.get(download.get_url, stream=True, timeout=15)
    with open(file_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=DOWNLOAD_CHUNK_SIZE):
            if chunk:
                f.write(chunk)


class SeparatorDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        if index.data(Qt.UserRole + 10):  # Custom role for separator lines
            pen = QPen(Qt.gray)
            pen.setWidth(1)
            painter.setPen(pen)
            y = option.rect.center().y()
            painter.drawLine(option.rect.left(), y, option.rect.right(), y)
        else:
            super().paint(painter, option, index)

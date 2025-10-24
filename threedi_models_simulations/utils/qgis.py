import os

from qgis.core import QgsVectorLayer
from qgis.utils import plugins


def style_path(qml_filename):
    """Setting up path to the QML style with given filename."""
    path = os.path.join(os.path.dirname(__file__), "styles", qml_filename)
    return path


def set_named_style(layer, qml_filename):
    """Set QML style to the vector layer."""
    qml_path = style_path(qml_filename)
    layer.loadNamedStyle(qml_path)


def geopackage_layer(gpkg_path, table_name, layer_name=None):
    """Creating vector layer out of GeoPackage source."""
    uri = f"{gpkg_path}|layername={table_name}"
    layer_name = table_name if layer_name is None else layer_name
    vlayer = QgsVectorLayer(uri, layer_name, "ogr")
    return vlayer


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

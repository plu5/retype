from .loader import dynamic_load
from .modules_name_map import name_map, module_names
from .__main__ import QT_WRAPPER


already_imported = {}
qt_modules = {}


def __getattr__(name):
    return dynamic_load(name, name_map, already_imported, qt_modules, module_names)

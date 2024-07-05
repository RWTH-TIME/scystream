import importlib
import pkgutil
import os


def import_all_models(module_name: str) -> None:
    package = importlib.import_module(module_name)
    package_dir = os.path.dirname(package.__file__)

    for _, name, is_pkg in pkgutil.iter_modules([package_dir]):
        if not is_pkg:
            importlib.import_module(f"{module_name}.{name}")
